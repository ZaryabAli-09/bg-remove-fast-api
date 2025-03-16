from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import shutil
import os
import gc  # ✅ Garbage collection to free memory
from rembg import remove
from PIL import Image

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def cleanup_files(files):
    """Delete files after response is sent."""
    for file in files:
        if os.path.exists(file):
            os.remove(file)

@app.get("/")
def home():
    return {"message": "FastAPI is running on Render!"}

@app.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    output_path = os.path.join(UPLOAD_DIR, f"processed_{file.filename}")

    try:
        # ✅ Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ✅ Open and Resize Large Images (Reduces RAM Usage)
        with Image.open(file_path) as input_image:
            if max(input_image.size) > 1024:  # Resize large images
                input_image.thumbnail((1024, 1024))
            
            # ✅ Remove Background (Only process smaller images to save RAM)
            output_image = remove(input_image)
            output_image.save(output_path, "PNG")

        # ✅ Free up memory immediately
        gc.collect()

        # ✅ Cleanup temp files after response
        background_tasks.add_task(cleanup_files, [file_path, output_path])

        return FileResponse(output_path, media_type="image/png")

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# ✅ Ensure Render uses the correct port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if PORT is not set
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
