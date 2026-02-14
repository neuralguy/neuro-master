#!/bin/bash
set -e

# Конфигурация
BACKUP_DIR="/backups/ai-content-bot"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Создаём директорию для бэкапов
mkdir -p $BACKUP_DIR

echo "🗄️ Создание бэкапа..."

# Бэкап базы данных PostgreSQL
echo "📊 Бэкап PostgreSQL..."
docker-compose exec -T db pg_dump -U postgres aibot > "$BACKUP_DIR/db_$DATE.sql"

# Бэкап файлов генераций
echo "📁 Бэкап файлов..."
tar -czf "$BACKUP_DIR/storage_$DATE.tar.gz" storage/

# Бэкап .env (зашифрованный)
echo "🔐 Бэкап конфигурации..."
cp .env "$BACKUP_DIR/env_$DATE.backup"

# Удаляем старые бэкапы
echo "🧹 Удаление старых бэкапов..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "✅ Бэкап завершён: $BACKUP_DIR"
ls -lh $BACKUP_DIR
