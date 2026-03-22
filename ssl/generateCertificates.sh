#!/bin/bash

# Generate self-signed certificate

set -e

SSL_DIR="${PWD}/ssl" # To be ran from OpenFileHost/
CERT_DIR="${SSL_DIR}/certs"
CERTMSG="\033[0;32m[CERTIFICATE]\033[0m"


echo -e "$CERTMSG Removing old certificates..."
mkdir -p "$CERT_DIR"
rm -r "$CERT_DIR"
mkdir -p "$CERT_DIR"


# Get IP address
IP_ADDRESS=$(python3 -c "import socket; s=socket.socket(socket.AF_INET6, socket.SOCK_DGRAM); s.connect(('2001:4860:4860::8888', 80)); ip=s.getsockname()[0]; s.close(); print(ip.split('%')[0])" 2>/dev/null || 
             python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()")

if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="localhost"
fi

CERT_NAME="${IP_ADDRESS//:/_}"
CERT_PATH="$CERT_DIR/$CERT_NAME"
mkdir -p "$CERT_PATH"


CERT_FILE="$CERT_PATH/fullchain.pem"
KEY_FILE="$CERT_PATH/privkey.pem"

echo -e "$CERTMSG Generating self-signed certificate for: $IP_ADDRESS"

# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days 30 \
    -subj "/CN=$IP_ADDRESS" \
    -addext "subjectAltName=IP:$IP_ADDRESS"

chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo -e "$CERTMSG Self-signed certificate generated"
echo "  Certificate: $CERT_FILE"
echo "  Private Key: $KEY_FILE"
echo ""
echo -e "$CERTMSG Browsers will show a warning because this certificate is self-signed."
echo "      This is normal and you can proceed after accepting the warning. HTTPS will be enabled."
