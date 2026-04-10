import asyncio
import os
import signal
import shutil
import time
import tomllib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

# packages
import bitmath
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# local modules
from database.database import * # UPLOAD_DIR is defined here
from python.helpers import *

with open("server-config.toml", "rb") as f:
    config = tomllib.load(f)

# Server config
maxCapacity = bitmath.parse_string(config["server"]["maxsize"]) # Max server capacity in bytes
jobFrequency = config["server"]["deletionchecktime"] # How many seconds between each cleanup job
fileMaxLifetime = config["server"]["maxfilelifetime"]
serverLifetime = config["server"]["serverlifetime"]
deleteFilesOnShutdown = config["server"]["deleteonshutdown"]
basicAccess = config["interface"]["shouldfileconfigbepublic"]

# Color variables
CYAN = "\033[96m"
GREEN = '\033[32m'
ORANGE = "\033[38;2;255;165;0m"
RESET = "\033[0m"
JOB = f"{CYAN}[JOB]{RESET}"
CONFIG = f"{ORANGE}[CONFIG]{RESET}"

print(f"""=== CONFIGURATION ===============
SERVER CAPACITY: {maxCapacity.bytes} bytes
JOB FREQUENCY: {jobFrequency} seconds
=================================""")

def deleteAllFiles():
    files = getAllFiles()
    for key in files:
        removeFile(key, "Automatic deletion on shutdown")

async def cleanupExpiredFiles():
    """Runs every X seconds while server is up"""
    while True:
        # === CLEAN UP SECTION ===
        try:
            print(f"{JOB} Running file cleanup job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            
            expiredFiles = getExpiredFiles()  # Returns list
            for downloadKey in expiredFiles:
                # Delete from uploads and db
                removeFile(downloadKey, "Expired")
            
            print(f"{JOB} Deleted {len(expiredFiles)} files.")
        except Exception as e:
            print(f"{JOB} Error in cleanup job: {e}")
        
        # === WAITING ===
        try:
            nextRunTime = datetime.now() + timedelta(seconds=jobFrequency)
            print(f"{JOB} Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Next job at {nextRunTime.strftime('%Y-%m-%d %H:%M:%S')}")            

            await asyncio.sleep(jobFrequency)
        except asyncio.CancelledError:
            print(f"{JOB} Cancellation recieved.")
            break



async def autoShutdown():
    """Automatically shuts down the server after serverLifetime seconds by sending SIGINT"""
    global serverLifetime
    print(f"{JOB} Server will shut down in {serverLifetime} seconds")
    
    try:
        while (serverLifetime > 0):
            await asyncio.sleep(1)
            serverLifetime -= 1

        print(f"{JOB} Server lifetime reached. Shutting down...")
        
        # Sending sigint to let uvicorn handle server termination gracefully
        os.kill(os.getpid(), signal.SIGINT)
        
    except asyncio.CancelledError:
        print(f"{JOB} Auto-shutdown task cancelled")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Start the background job
    backgroundJob = asyncio.create_task(cleanupExpiredFiles())

    shutdownTask = None
    if serverLifetime > 0:
        shutdownTask = asyncio.create_task(autoShutdown())

    if (deleteFilesOnShutdown == 1):
        print(f"{CONFIG} All uploaded files will be deleted when this server shuts down.")

    
    yield  # Server
    
    # try closing once server down
    backgroundJob.cancel()
    try:
        await backgroundJob
    except asyncio.CancelledError:
        pass
    print(f"{JOB} File cleanup job stopped!")

    if (deleteFilesOnShutdown == 1):
        print(f"{CONFIG} Deleting files...")
        deleteAllFiles()

app = FastAPI(lifespan=lifespan)

#https handling
@app.middleware("http")
async def add_protocol_info(request: Request, call_next):
    """Add protocol info to request state"""
    # Check if request came through HTTPS
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        request.state.is_https = forwarded_proto == "https"
    else:
        request.state.is_https = request.url.scheme == "https"
    
    response = await call_next(request)
    return response



# Setup directories 
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/upload", StaticFiles(directory="upload"), name="upload")


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=Path("static/index.html").read_text())

@app.post("/upload")
async def uploadFile(
    file: UploadFile = File(...), # User file
    life: int = Form(...),  # User requested lifetime for the file
    compressed: bool = Form(...), # Whether or not the file is compressed
    originalFileSize: int = Form(...), # Original file size if compressed
    encrypted: bool = Form(...), # Whether or not it was encrypted
    salt: bytes = Form(...) # Salt for decryption
):    
    # Get current directory size
    currentCapacity = queryKnownSize()
    uploadedFileSize = file.size
    
    # Check if adding the new file would exceed capacity
    if currentCapacity + uploadedFileSize > maxCapacity.bytes:
        return {
            "status": "error", 
            "message": "File too large: Would cause total allowed size to be exceeded."
        }

    if (life > fileMaxLifetime or life < 0):
        life = fileMaxLifetime
    
    # Generate download key
    random_bytes = os.urandom(16)
    downloadKey = random_bytes.hex()
    
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
            size=uploadedFileSize,
            originalSize=originalFileSize,
            compressed=compressed,
            encrypted=encrypted,
            salt=salt,
            expireTime=life
            )

    return {
        "status": "ok", 
        "message": "Upload succeeded!",
        "key": downloadKey,
        "life": life if basicAccess == 1 else -1
    }


@app.get("/policies")
async def getPolicies():
    if (basicAccess == 1):
        return {"access": 1, "fileLifetime": fileMaxLifetime, "serverLifetime": serverLifetime}
    else:
        return{"access": 0}


@app.get("/query")
async def serveQuery(key: str):
    fileInfo = getFileInfoFromKey(key)
    if fileInfo == -1:
        return {"status": -1}
    else:
        status = "ok"
        fileName = fileInfo[0]
        size = fileInfo[1]
        originalSize = fileInfo[2]
        compressed = fileInfo[3]
        encrypted = fileInfo[4]
        salt = fileInfo[5]
        createdDate = fileInfo[6]
        expireDate = fileInfo[7]

        return {"status": status,
                "fileName": fileName,
                "processedSize": size,
                "downloadSize": originalSize,
                "compressed": compressed,
                "encrypted": encrypted,
                "salt": salt,
                "uploadedDate": createdDate,
                "expireDate": expireDate}

@app.delete("/delete")
async def deleteRequestedFile(key: str):

    if (removeFile(key, "User requested deletion") == 1):
        return {"status": "ok"}
    else:
        return {"status": "bad"}


