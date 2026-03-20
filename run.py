import uvicorn
import socket
import tomllib

# Get port from config
with open("server-config.toml", "rb") as f:
    config = tomllib.load(f)

serverport = config["server"]["port"]

if __name__ == "__main__":

    # Get the address of the server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print("Server accessible from LAN at: ",s.getsockname()[0],f":{serverport}")
    s.close()


    uvicorn.run(
        "python-server:app",
        host="0.0.0.0",
        port=serverport,
        reload=True
)
