#!/bin/bash

# Variables
ENVIRONMENT="pyenv"
PACKAGES=("fastapi" "uvicorn" "python-multipart" "bitmath")

# Functions
state() {
  echo "[SETUP] $1"
}

checkpackages() {
  echo "[PACKAGES] Checking for missing packages..."
  # List of required packages

  for package in "${PACKAGES[@]}"; do
    if pip show "$package" >/dev/null 2>&1; then
      echo "[PACKAGES] $package is already installed."
    else
      echo "[PACKAGES] $package not found. Installing..."
      pip install "$package"
    fi
  done
}

startserver() {
  python configure-server.py
}

generatecertificates() {
  ./ssl/generateCertificates.sh
}

# Timer start
start=$(date +%s.%N)

# Check if python exists
if command -v python &>/dev/null || command -v python3 &>/dev/null; then
  state "Python is installed"
else
  state "Python is not installed"
  exit 1
fi

state "Checking if python environment exists..."

if [ ! -d "$ENVIRONMENT" ]; then
  state "Environment not found! Creating it."
  state "First time set up might take some time!"
  python -m venv $ENVIRONMENT
  state "Installing packages..."
  source $ENVIRONMENT/bin/activate

  checkpackages
else
  state "Environment exists."
  source $ENVIRONMENT/bin/activate

  checkpackages
fi

# Check if the server needs to be public
python3 -c "
import sys
sys.path.insert(0, '.')
from python.helpers import needToGenerateCertificates
sys.exit(needToGenerateCertificates())
"
# Generate certs if so, otherwise no
if [ $? -eq 1 ]; then
  generatecertificates
else
  state "Local server. Not generating any certificates."
fi

# Should assume at this point that we are in the environment and that packages
# are properly set up, end the setup timer and start the server
end=$(date +%s.%N)
runtime=$(echo "$end - $start" | bc)
state "Done! Total setup time: ${runtime} seconds"

startserver
