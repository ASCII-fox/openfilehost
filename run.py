import uvicorn
import socket

serverport = 8000

if __name__ == "__main__":

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
