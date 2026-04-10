# Responsible for keeping track of files and database
# functions

import sqlite3
from datetime import datetime, timedelta
from python.helpers import getDirectorySize
from pathlib import Path

fileDB = sqlite3.connect("database/files.db")
cursor = fileDB.cursor()

# Ensure upload dir exists
UPLOAD_DIR = Path("upload")
UPLOAD_DIR.mkdir(exist_ok=True)
# color text
DBLUE = "\033[38;5;27m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"
DATABASE = f"{DBLUE}[DATABASE]{RESET}"
ADDED = f"{GREEN}Added{RESET}"
DELETED = f"{RED}Deleted{RESET}"

cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        name TEXT NOT NULL,
        pathName TEXT NOT NULL PRIMARY KEY,
        size INTEGER NOT NULL,
        originalSize INTEGER NOT NULL,
        compressed BOOL NOT NULL,
        encrypted BOOL NOT NULL,
        salt BLOB,
        createdDate TIMESTAMP,
        expireDate TIMESTAMP
    )
""")

def addFile(name, downloadKey, size, originalSize, compressed, encrypted, salt, expireTime):
    cursor.execute(
        "INSERT INTO files (name, pathName, size, originalSize, compressed, encrypted, salt, createdDate, expireDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, downloadKey, size, originalSize, compressed, encrypted, salt, datetime.now(), datetime.now() + timedelta(seconds=expireTime))
    )
    print(f"{DATABASE} {ADDED} file {UPLOAD_DIR}/{downloadKey}")
    fileDB.commit()

def removeFile(downloadKey, reason):
    filePath = UPLOAD_DIR / downloadKey
    rtnVal = 0
    if filePath.exists():
        filePath.unlink()
        print(f"{DATABASE} {DELETED} file: {filePath} [{reason}]")
        rtnVal = 1
    else:
        print(f"{DATABASE} File not found: {filePath}")
        rtnVal = -1


    cursor.execute("DELETE FROM files WHERE pathName = ?", (downloadKey,))
    fileDB.commit()
    return rtnVal

# return an array in the form of [name, size, compressed, createdDate, expireDate]
def getFileInfoFromKey(downloadKey):
    cursor.execute(
        "SELECT name, size, originalSize, compressed, encrypted, salt, createdDate, expireDate FROM files WHERE pathName = ?",
        (downloadKey,)
    )
    result = cursor.fetchone()
    
    if result:
        return list(result)
    else:
        # Return -1 if not found
        return -1


# returns an array of files that need to be deleted
def getExpiredFiles():
    cursor.execute(
        "SELECT pathName FROM files WHERE datetime(expireDate) < datetime('now')",
    )
    return [row[0] for row in cursor.fetchall()]

def getAllFiles():
    cursor.execute(
        "SELECT pathName FROM files",
    )
    return [row[0] for row in cursor.fetchall()]


# gets the size of upload/ according to this database
def queryKnownSize():
    cursor.execute("SELECT SUM(size) FROM files")
    result = cursor.fetchone()
    return result[0] if result[0] is not None else 0

if __name__ == "__main__":
    cursor.execute("PRAGMA table_info(files)")
    columns = [col[1] for col in cursor.fetchall()]

    cursor.execute("SELECT * FROM files")
    rows = cursor.fetchall()
    print(" | ".join(columns))
    print("-" * 50)
    for row in rows:
        print(" | ".join(str(value) for value in row))

    print("Printing expired rows:")
    expiredRows = getExpiredFiles()
    for downloadKey in expiredRows:
        print(downloadKey)

    print(f"Total db size: {queryKnownSize()}");
    print(f"According to getDirectorySize, it is {getDirectorySize('upload')}")
    fileDB.close()
