# Misc helper functions

from pathlib import Path
import tomllib


def getDirectorySize(directory):
    path = Path(directory)
    total_size = sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
    return total_size

def needToGenerateCertificates():
    with open("server-config.toml", "rb") as f:
        config = tomllib.load(f)
    needGenCerts = config["server"].get("shouldserverbepublic", 0)
    return 1 if needGenCerts == 1 else 0



if __name__ == "__main__":
    size = getDirectorySize("upload")
    print(size)
