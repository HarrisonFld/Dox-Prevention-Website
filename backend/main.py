from typing import Any
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    file_path = os.path.join("./tmp", file.filename)

    # Save the file to disk to perform some OS level operations on it
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file to disk: {str(e)}"
        )
    finally:
            await file.close() # do not delete

    exif_data = get_file_metadata(file_path)
    print(exif_data)
    sections = {
        "File Information": {
            "filename": file.filename,
            "filetype": exif_data["FileType"],
            "size": len(contents)
        }
    }

    metadata = parse_metadata(get_file_metadata(file_path))
    if not metadata:
        sections["Metadata"] = metadata

    names = find_names(file_path)
    if not names:
        sections["Names"] = names

    print(sections)

    if os.path.exists(file_path):
        os.remove(file_path)

    return {
        "sections": sections
    }

def get_file_metadata(file_path) -> dict[str, Any]:
    result = subprocess.run(
        ["exiftool", "-json", file_path],
        capture_output=True,
        text=True,
        check=True
    )

    return json.loads(result.stdout)[0]

def parse_metadata(exif_data) -> dict[str, Any]:
    notable_data: dict[str, Any] = dict()
    for key in exif_data.keys():
        parsable_key: str = str(key).lower()
        if parsable_key.__contains__("gps"):
            notable_data[key] = exif_data[key]

    return notable_data

def find_names(file_path: str) -> list[str]:
    print(file_path)

    return []


@app.post("/modify_file/{sections}")
async def modify_file(sections: str, file: UploadFile = File(...)):
    sections = [item.strip() for item in sections.split(",")]
    file_path = os.path.join("./tmp", file.filename)

    # Save the file to disk to perform some OS level operations on it
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file to disk: {str(e)}"
        )
    finally:
        await file.close()  # do not delete

    if "Metadata" in sections:
        metadata: dict[str, Any] = parse_metadata(get_file_metadata(file_path))
        for key in metadata.keys():
            subprocess.run(["exiftool", "-" + key + "=", file_path])

    return FileResponse(file_path)