from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import tomllib

app = FastAPI()

with open("server-config.toml", "rb") as f:
    config = tomllib.load(f)

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
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "ok", "filename": file.filename}

@app.get("/policies")
async def getPolicies():
    basicAccess = config["interface"]["shouldfileconfigbepublic"]
    if (basicAccess == 1):
        fileLifetime = config["server"]["filelifetime"]
        return {"access": 1, "fileLifetime": fileLifetime}
    else:
        return{"access": 0}

