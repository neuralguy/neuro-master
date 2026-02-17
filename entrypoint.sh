#!/bin/sh
set -e

echo "Applying database migrations..."

# Try normal migration first
if alembic upgrade head 2>&1; then
    echo "Migrations applied successfully."
else
    echo "Migration failed. Stamping initial migration and applying the rest..."
    # Stamp only the initial migration (tables already exist from create_all)
    alembic stamp 9bfd534d9eee
    # Now apply all subsequent migrations
    alembic upgrade head
    echo "Migrations applied successfully."
fi

echo "Starting application..."
exec python -m src.main
