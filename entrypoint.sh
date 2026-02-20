#!/bin/sh
set -e

echo "Applying database migrations..."

# Try normal migration first
if alembic upgrade head 2>&1; then
    echo "Migrations applied successfully."
else
    echo "Migration failed. Trying to detect current state..."
    # Получаем текущую ревизию
    CURRENT=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]{12}' | head -1)
    echo "Current revision: $CURRENT"

    if [ -z "$CURRENT" ]; then
        # БД есть но alembic_version пустая — таблицы созданы вручную через create_all
        # Стампуем на последнюю миграцию до наших изменений
        echo "No revision found. Stamping to c3d4e5f6a7b8..."
        alembic stamp c3d4e5f6a7b8
    fi

    alembic upgrade head
    echo "Migrations applied successfully."
fi

echo "Starting application..."
exec python -m src.main
