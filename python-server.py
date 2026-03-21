# stdlib
import asyncio
import os
import shutil
import time
import tomllib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

# packages
import bitmath
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# local modules
from database import *
from python.helpers import *

with open("server-config.toml", "rb") as f:
    config = tomllib.load(f)


maxCapacity = bitmath.parse_string(config["server"]["maxsize"]) # Max server capacity in bytes
jobFrequency = config["server"]["deletionchecktime"] # How many seconds between each cleanup job

CYAN = "\033[96m"
GREEN = '\033[32m'
RESET = "\033[0m"

print(f"""=== CONFIGURATION ===============
SERVER CAPACITY: {maxCapacity.bytes} bytes
JOB FREQUENCY: {jobFrequency} seconds
=================================""")

async def cleanupExpiredFiles():
    """Runs every X seconds while server is up"""
    while True:
        # === CLEAN UP SECTION ===
        try:
            print(f"{CYAN}[JOB]{RESET} Running file cleanup job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(1)  # test
            
            # TODO: IMPLEMENT
            
        except Exception as e:
            print(f"{CYAN}[JOB]{RESET} Error in cleanup job: {e}")
        
        # === WAITING ===
        try:
            nextRunTime = datetime.now() + timedelta(seconds=jobFrequency)
            print(f"{CYAN}[JOB]{RESET} Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Next job at {nextRunTime.strftime('%Y-%m-%d %H:%M:%S')}")            

            await asyncio.sleep(jobFrequency)
        except asyncio.CancelledError:
            print(f"{CYAN}[JOB]{RESET} Cancellation recieved.")
            break


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Start the background job
    backgroundJob = asyncio.create_task(cleanupExpiredFiles())
    print(f"{CYAN}[JOB]{RESET} File cleanup job started!")
    
    yield  # Server
    
    # try closing once server down
    backgroundJob.cancel()
    try:
        await backgroundJob
    except asyncio.CancelledError:
        pass
    print(f"{CYAN}[JOB]{RESET} File cleanup job stopped!")

app = FastAPI(lifespan=lifespan)

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
    
    addFile(
            name=originalFilename,
            downloadKey=downloadKey,
            size=uploadedFileSize
            )

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



