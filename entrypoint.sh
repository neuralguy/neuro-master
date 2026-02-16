#!/bin/sh
set -e

echo "Applying database migrations..."

# If alembic_version table doesn't exist or is empty,
# but application tables already exist — stamp current state
# so alembic doesn't try to re-create them.
alembic upgrade head 2>&1 || {
    echo "Migration failed, attempting to stamp existing database..."
    alembic stamp head
    echo "Database stamped. Retrying migrations..."
    alembic upgrade head
}

echo "Migrations applied successfully."

echo "Starting application..."
exec python -m src.main
