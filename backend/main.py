from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import json


app = FastAPI()

# Make it so the response is 200 OK and doesn't cause any error in response
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allows requests from any origin/port
    allow_credentials=False,      # Must be False when allow_origins is ["*"]
    allow_methods=["*"],          # Allows POST, GET, etc.
    allow_headers=["*"],          # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/parse-file")
async def parse_file(file: UploadFile = File(...)):
    tmp_file_path = os.path.join("./tmp", file.filename)

    # Save the file to disk to perform some OS level operations on it
    try:
        contents = await file.read()
        with open(tmp_file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file to disk: {str(e)}"
        )
    finally:
            await file.close() # do not delete

    result = subprocess.run(
        ["exiftool", "-json", tmp_file_path],
        capture_output=True, 
        text=True, 
        check=True
    )
    exif_data = json.loads(result.stdout)
    print(exif_data)
    parse_metadata(exif_data[0])

    return {
        "filename": file.filename,
        "size": len(contents)
    }


def parse_metadata(exif_data):
    print(exif_data["FileName"])