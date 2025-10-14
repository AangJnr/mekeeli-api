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


# Open Docker
open -a Docker

docker compose -f ../docker-compose.yml -f ../docker-compose.override.yml down
docker volume rm mekeeli_postgres-data-dev  || true
sleep 5

# Load environment variables from .env.local
set -a  # automatically export all variables
source .env.local
set +a
echo "Environment variables loaded from .env.local."

echo "DATABASE_URL: $DATABASE_URL"


docker compose -f ../docker-compose.yml -f ../docker-compose.override.yml up db -d
# Wait a few seconds for postgres to initialize
sleep 5

# Install dependencies from requirements.txt.
echo "Installing dependencies..."
pip install -r requirements.txt


# Run database migrations.
echo "Running database migrations..."
rm -f alembic/versions/*.py || true
chmod -R u+rwx alembic
mkdir -p alembic/versions
touch alembic/versions/.gitkeep
sleep 5
alembic stamp head

alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
echo "Database migrations applied."
sleep 5

# Start the FastAPI server using uvicorn on the port specified by the $PORT env var.
echo "Starting FastAPI server on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT --reload
