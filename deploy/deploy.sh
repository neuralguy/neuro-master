#!/bin/bash
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Деплой AI Content Bot${NC}"

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен${NC}"
    exit 1
fi

# Проверяем .env файл
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден${NC}"
    echo -e "${YELLOW}Скопируйте .env.example в .env и настройте переменные${NC}"
    exit 1
fi

# Останавливаем старые контейнеры
echo -e "${YELLOW}📦 Останавливаем старые контейнеры...${NC}"
docker-compose down --remove-orphans || true

# Собираем новые образы
echo -e "${YELLOW}🔨 Собираем образы...${NC}"
docker-compose build --no-cache

# Запускаем
echo -e "${YELLOW}🚀 Запускаем контейнеры...${NC}"
docker-compose up -d

# Ждём запуска
echo -e "${YELLOW}⏳ Ждём запуска приложения...${NC}"
sleep 10

# Применяем миграции
echo -e "${YELLOW}📊 Применяем миграции...${NC}"
docker-compose exec -T app alembic upgrade head

# Проверяем статус
echo -e "${YELLOW}🔍 Проверяем статус...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Деплой завершён успешно!${NC}"
    echo ""
    echo -e "Логи: ${YELLOW}docker-compose logs -f app${NC}"
    echo -e "Статус: ${YELLOW}docker-compose ps${NC}"
else
    echo -e "${RED}❌ Ошибка при запуске${NC}"
    docker-compose logs --tail=50 app
    exit 1
fi
