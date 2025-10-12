#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if the virtual environment exists. If not, create it and install dependencies.
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
  echo "Virtual environment created."
fi

# Activate the virtual environment.
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies from requirements.txt.
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations.
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI server using uvicorn on the port specified by the $PORT env var.
echo "Starting FastAPI server on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT --reload
