from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import hashlib
import os
import bitmath
from python.helpers import *
import shutil
import tomllib

with open("server-config.toml", "rb") as f:
    config = tomllib.load(f)


maxCapacity = bitmath.parse_string(config["server"]["maxsize"])
print(maxCapacity.bytes)
exit

app = FastAPI()


# Make sure upload directory exists
UPLOAD_DIR = Path("upload")
UPLOAD_DIR.mkdir(exist_ok=True)


# Setup directories 
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/upload", StaticFiles(directory="upload"), name="upload")


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=Path("static/index.html").read_text())

@app.post("/upload")
async def uploadFile(file: UploadFile = File(...)):
    
    # Get current directory size
    currentCapacity = getDirectorySize("upload")
    uploadedFileSize = file.size
    
    # Check if adding the new file would exceed capacity
    if currentCapacity + uploadedFileSize > maxCapacity.bytes:
        return {
            "status": "error", 
            "message": "File too large: Would cause total allowed size to be exceeded."
        }
    
    # Generate download key
    random_bytes = os.urandom(6)
    downloadKey = int.from_bytes(random_bytes, byteorder='big')
    
    # Get file extension
    originalFilename = file.filename
    fileExtension = Path(originalFilename).suffix
    
    newFilename = f"{downloadKey}{fileExtension}"
    filePath = UPLOAD_DIR / newFilename
    
    # Handle duplicate filenames (unlikely with random keys, but just in case)
    if filePath.exists():
        counter = 1
        while filePath.exists():
            newFilename = f"{downloadKey}_{counter}{fileExtension}"
            filePath = UPLOAD_DIR / newFilename
            counter += 1
        downloadKey = f"{downloadKey}_{counter}"
    downloadKey = f"{downloadKey}{fileExtension}"
    
    # Save file
    with filePath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # TODO: Add database input
    # Store in database with original filename
    # addFile(
    #    name=originalFilename,           
    #    downloadKey=downloadKey,          
    #)
    
    return {
        "status": "ok", 
        "message": "Upload succeeded!",
        "key": downloadKey
    }


@app.get("/policies")
async def getPolicies():
    basicAccess = config["interface"]["shouldfileconfigbepublic"]
    if (basicAccess == 1):
        fileLifetime = config["server"]["filelifetime"]
        return {"access": 1, "fileLifetime": fileLifetime}
    else:
        return{"access": 0}



