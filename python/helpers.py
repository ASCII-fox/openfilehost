# Misc helper functions

from pathlib import Path

def getDirectorySize(directory):
    path = Path(directory)
    total_size = sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
    return total_size


if __name__ == "__main__":
    size = getDirectorySize("upload")
    print(size)
