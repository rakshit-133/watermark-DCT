import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
# --- NEW IMPORT ---
from starlette.background import BackgroundTask

# Import your existing watermark functions
from watermark import embed_watermark, extract_watermark

# --- App Setup ---
app = FastAPI(title="Watermarking API")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW HELPER FUNCTION ---
def cleanup_file(path: str):
    """Helper function to remove a file after sending."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error cleaning up file {path}: {e}")

# --- API Endpoints ---

@app.post("/embed")
async def embed_api(
    image: UploadFile = File(..., description="The host image file."),
    text: str = Form(..., description="The secret watermark text.")
):
    # Save the uploaded file to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_in:
        content = await image.read()
        temp_in.write(content)
        input_path = temp_in.name

    # Create a temp file for the output
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_out:
        output_path = temp_out.name
    
    try:
        # Run your synchronous backend function
        embed_watermark(input_path, text, output_path, strength=20)
        
        # --- MODIFIED RETURN ---
        # Create a background task to delete the output file *after* sending
        cleanup_task = BackgroundTask(cleanup_file, path=output_path)
        
        return FileResponse(
            output_path, 
            media_type='image/png', 
            filename='watermarked_image.png',
            background=cleanup_task  # <-- ADD THIS LINE
        )
    except Exception as e:
        # If anything goes wrong, raise a proper HTTP error
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # --- MODIFIED FINALLY ---
        # We ONLY clean up the input file here.
        # The output file is handled by the BackgroundTask.
        cleanup_file(path=input_path)

@app.post("/extract")
async def extract_api(
    image: UploadFile = File(..., description="The watermarked image file.")
):
    # Save the uploaded file to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_in:
        content = await image.read()
        temp_in.write(content)
        input_path = temp_in.name
    
    try:
        # Run your backend function
        message = extract_watermark(input_path, strength=20)
        
        # Return the extracted message as JSON
        return {"message": message}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # This function is fine, as it cleans up *after* returning
        cleanup_file(path=input_path)