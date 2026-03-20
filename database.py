# Responsible for keeping track of files

import sqlite3
from datetime import datetime

fileDB = sqlite3.connect("files.db")
cursor = fileDB.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        pathName TEXT NOT NULL,
        size INTEGER NOT NULL,
        created_at TIMESTAMP
    )
""")

def addFile(name, downloadKey, size):
    cursor.execute(
        "INSERT INTO files (name, pathName, size, created_at) VALUES (?, ?, ?, ?)",
        (name, downloadKey, size, datetime.now())
    )
    fileDB.commit()

def getFile(sha256):

# returns an array of files that need to be deleted
def getExpiredFiles(fileLifetime):
    cursor.execute(
        "SELECT id, name, pathName, size, created_at FROM files WHERE datetime(created_at, ?) < datetime('now')",
        (f'+{fileLifetime} seconds',)
    )
    return cursor.fetchall()
