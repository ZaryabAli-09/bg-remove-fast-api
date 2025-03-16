from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import shutil
import os
from rembg import remove
from PIL import Image
import uvicorn


app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def cleanup_files(files):
    """Delete files after response is sent."""
    for file in files:
        if os.path.exists(file):
            os.remove(file)

@app.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    output_path = os.path.join(UPLOAD_DIR, f"processed_{file.filename}")

    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the image to remove background
        with Image.open(file_path) as input_image:
            output_image = remove(input_image)  # Remove background
            output_image.save(output_path, "PNG")  # Save as PNG with transparency

        # Add cleanup task after response is sent
        background_tasks.add_task(cleanup_files, [file_path, output_path])

        # Return the processed image
        return FileResponse(output_path, media_type="image/png")

    except Exception as e:
        # Delete the uploaded file if an error occurs
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Run Uvicorn when executed directly (Render requires this)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)