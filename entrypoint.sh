#!/bin/bash
set -e

echo "Running database migrations..."
max_retries=20
retry_delay=3
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge "$max_retries" ]; then
    echo "Migration failed after $attempt attempts."
    exit 1
  fi
  echo "Migration attempt $attempt failed. Retrying in ${retry_delay}s..."
  attempt=$((attempt + 1))
  sleep "$retry_delay"
done

echo "Starting Mekeeli..."
exec "$@"
