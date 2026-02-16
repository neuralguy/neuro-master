#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head
echo "Migrations applied successfully."

echo "Starting application..."
exec python -m src.main
