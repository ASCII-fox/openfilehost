#!/bin/bash 

# Functions 
state() {
  echo "[SETUP] $1"
}

checkpackages() {
  echo "[PACKAGES] Checking for missing packages..."
  # TODO: IMPLEMENT
}

runscript() {
  # python3 pyserver.py
}
# Variables
ENVIRONMENT="pyenv"

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
