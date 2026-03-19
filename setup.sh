#!/bin/bash 

# Variables
ENVIRONMENT="pyenv"
PACKAGES=("fastapi" "uvicorn")

# Functions 
state() {
  echo "[SETUP] $1"
}

checkpackages() {
  echo "[PACKAGES] Checking for missing packages..."
# List of required packages

  for package in "${PACKAGES[@]}"; do
      if pip show "$package" > /dev/null 2>&1; then
          echo "[PACKAGES] $package is already installed."
      else
          echo "[PACKAGES] $package not found. Installing..."
          pip install "$package"
      fi
  done
}

runscript() {
  echo "Done! Running server..."
  python run.py
}

# Check if python exists
if command -v python &>/dev/null || command -v python3 &>/dev/null; then
    state "Python is installed"
else
    state "Python is not installed"
    exit 1
fi

state "Checking if python environment exists..."

if [ ! -d "$ENVIRONMENT" ]; then
  state "Environment not found, creating it."
  python -m venv $ENVIRONMENT
  state "Installing packages..."
  source $ENVIRONMENT/bin/activate

  checkpackages
else
  state "Environment exists."
  source $ENVIRONMENT/bin/activate

  checkpackages
fi

# Should assume at this point that we are in the environment and that packages 
# are properly set up, can run main script now

runscript
