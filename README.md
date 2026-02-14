# 🤖 AI Content Bot

Telegram Mini App для генерации AI контента (изображения, видео, FaceSwap) с интеграцией kie.ai API.

## 🎯 Функционал

### Для пользователей
- 🖼 **Генерация изображений** (Nano Banana Pro, FLUX.2, GPT Image)
- 🎬 **Создание видео** (Sora 2 Pro, Veo 3.1, Grok Imagine)
- 😊 **FaceSwap** - замена лиц на фото
- 💰 **Система токенов** с пополнением через ЮКassa
- 🎁 **Реферальная программа** (50 токенов за друга)
- 📸 **Галерея** с избранным
- 📊 **История операций**

### Для администраторов
- 👥 Управление пользователями
- 🤖 Управление AI моделями и ценами
- 💳 Мониторинг платежей
- 📊 Статистика и аналитика
- 📡 WebSocket логи в реальном времени

## 🏗 Архитектура

```
Backend (Python 3.11+)
├── Telegram Bot (aiogram 3.x)
├── FastAPI REST API
├── PostgreSQL / SQLite
├── Redis (cache + FSM)
└── kie.ai API integration

Frontend (TODO)
└── Telegram Mini App
```

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- Redis
- PostgreSQL (опционально, для prod)

### 1. Установка

```bash
# Клонирование
cd ai-content-bot

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -e .
```

### 2. Конфигурация

```bash
# Создать .env
cp .env.example .env

# Отредактировать .env:
# - BOT_TOKEN_DEV (от @BotFather)
# - ADMIN_IDS (ваш Telegram ID)
# - KIE_API_KEY (от kie.ai)
# - YOOKASSA_SHOP_ID, YOOKASSA_SECRET
```

### 3. Запуск

#### Dev режим (SQLite + Memory storage)

```bash
# Запустить Redis
docker-compose -f docker-compose.dev.yml up redis -d

# Применить миграции
alembic upgrade head

# Запустить бота + API
python -m src.main
```

#### Production (PostgreSQL + Docker)

```bash
# Настроить .env для production (DEV_MODE=0)
docker-compose up -d
```

## 📡 API Endpoints

### Public API
- `POST /api/v1/auth/telegram` - Аутентификация через Telegram WebApp
- `GET /api/v1/models` - Список доступных AI моделей
- `POST /api/v1/generation` - Создать генерацию
- `GET /api/v1/generation/{id}` - Статус генерации
- `GET /api/v1/gallery` - Галерея пользователя
- `POST /api/v1/payments` - Создать платёж
- `GET /api/v1/user/me` - Профиль пользователя

### Admin API
- `GET /api/v1/admin/stats` - Статистика
- `GET /api/v1/admin/users` - Список пользователей
- `PATCH /api/v1/admin/users/{id}` - Изменить пользователя
- `GET /api/v1/admin/models` - Управление моделями
- `WS /ws/admin/logs` - WebSocket логи

**Документация**: http://localhost:8000/api/docs (в dev режиме)

## 🗄 База данных

### Миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "description"

# Применить
alembic upgrade head

# Откатить
alembic downgrade -1
```

### Модели
- `users` - Пользователи
- `referrals` - Реферальные связи
- `payments` - Платежи
- `balance_history` - История баланса
- `ai_models` - AI модели
- `generations` - Задачи генерации
- `gallery_items` - Элементы галереи

## 🎨 AI Модели (по умолчанию)

### Изображения
- **Nano Banana Pro** (5 токенов) - Google DeepMind
- **FLUX.2** (5 токенов) - Black Forest Labs
- **GPT Image 1.5** (8 токенов) - OpenAI

### Видео
- **Sora 2 Pro** (50 токенов) - OpenAI, до 15 сек
- **Veo 3.1** (60 токенов) - Google DeepMind
- **Grok Imagine** (30 токенов) - xAI

### FaceSwap
- **FaceSwap** (10 токенов) - Замена лиц

## 💰 Платежи

- Интеграция с **ЮКassa**
- 1 токен = 1 рубль
- Минимум: 50 ₽
- Максимум: 50,000 ₽
- Предустановленные пакеты: 100, 300, 500, 1000, 2000, 5000 ₽

## 📊 Логирование

- **Консоль**: Цветной вывод с контекстом (request_id, user_id)
- **Файлы**: Ротация по размеру, сжатие
- **Telegram**: Батчинг логов в Telegram чат
- **WebSocket**: Реал-тайм логи для админ панели

```python
from src.shared.logger import logger

logger.info("Message")  # Автоматически добавляется контекст
```

## 🔐 Безопасность

- ✅ Telegram WebApp Init Data validation
- ✅ HMAC проверка подписи
- ✅ Проверка срока действия (24 часа)
- ✅ Admin-only endpoints
- ✅ Rate limiting (Throttling middleware)

## 🧪 Тестирование

```bash
# Unit tests
pytest tests/

# С покрытием
pytest --cov=src tests/
```

## 📦 Зависимости

Основные:
- `aiogram` 3.13+ - Telegram Bot
- `fastapi` 0.115+ - REST API
- `sqlalchemy` 2.0+ - ORM
- `alembic` - Миграции
- `pydantic` 2.9+ - Валидация
- `loguru` - Логирование
- `redis` 5.2+ - Кеш
- `httpx` - HTTP клиент
- `yookassa` - Платежи

## 🐳 Docker

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up -d

# Логи
docker-compose logs -f app
```

## 📝 Структура кода

```
src/
├── api/          # FastAPI application
├── bot/          # Telegram bot (aiogram)
├── core/         # Database, Redis, Security
├── modules/      # Business logic (User, Payments, Generation, etc.)
├── shared/       # Logger, Enums, Constants
├── config.py     # Settings
└── main.py       # Entry point
```

## 🛠 Разработка

### Добавление новой AI модели

```python
# В src/modules/ai_models/service.py DEFAULT_MODELS
{
    "code": "new-model",
    "name": "New Model",
    "provider_model": "provider/model-name",
    "generation_type": GenerationType.IMAGE,
    "price_tokens": 10,
    "description": "Description",
    "icon": "🎨",
    "config": {"aspect_ratios": ["1:1"]},
}
```

### Добавление API endpoint

```python
# src/api/routes/your_route.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/endpoint")
async def handler(current_user: CurrentUser):
    return {"status": "ok"}

# Подключить в src/api/routes/__init__.py
```

## 📄 Лицензия

MIT License

## 🤝 Контакты

- Issues: GitHub Issues
- Email: support@example.com

---

**Статус**: ✅ Backend готов | 🔄 Frontend в разработке

Made with ❤️ using Python, aiogram & FastAPI
