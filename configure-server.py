# Responsible for getting uvicorn ready

import uvicorn
import socket
import tomllib
import sys
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from python.certificates import get_ssl_context


# Get config
with open("server-config.toml", "rb") as f:
    config = tomllib.load(f)

shouldServerBePublic = config["server"].get("shouldserverbepublic", 0) # Public HTTPS or LAN HTTP
http_port = config["server"].get("http_port", 8000)
https_port = config["server"].get("https_port", 8443)
local_host = config["server"].get("local_host", "0.0.0.0")

def get_public_ipv6():
    """Get the public IPv6 address of this machine"""
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        # Connect to Google's public IPv6 DNS
        s.connect(("2001:4860:4860::8888", 80))
        ip = s.getsockname()[0]
        s.close()
        
        # Remove zone index if present
        if '%' in ip:
            ip = ip.split('%')[0]
        return ip
    except Exception as e:
        logger.error(f"Failed to get IPv6 address: {e}")
        return None

if __name__ == "__main__":
    # Display network information
    ipv6 = get_public_ipv6()
    if ipv6:
        print(f"\n=== Network Information ===")
        print(f"Public IPv6: {ipv6}")
        print(f"HTTPS URL: https://[{ipv6}]:{https_port}")
        print(f"HTTP URL: http://[{ipv6}]:{http_port}")
        print(f"If no SSL certificates are available or the server is configured to be local,")
        print(f"It can be accessed at {local_host}:{http_port}")
        print("===========================\n")
    
    cert_file, key_file = None, None
    # Get certificates if needed
    if shouldServerBePublic == 1:
        cert_file, key_file = get_ssl_context(
        ip_address=ipv6
    )
    
    if cert_file and key_file and shouldServerBePublic == 1:
        print(f"  SSL certificates loaded")
        print(f"  Certificate: {cert_file}")
        print(f"  Private Key: {key_file}")
        
        # Start HTTPS server
        print(f"\nStarting HTTPS server on port {https_port}")
        uvicorn.run(
            "server:app",
            host="::",  # Listen on all IPv6 interfaces
            port=https_port,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file),
            reload=True,
            log_level="info"
        )
    else:
        print(f"Starting local HTTP server on port {http_port}")
        
        uvicorn.run(
            "server:app",
            host=local_host,
            port=http_port,
            reload=True,
            log_level="info"
        )
