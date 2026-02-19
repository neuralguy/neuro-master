"""Application constants."""

# === Telegram ===
WEBAPP_BUTTON_TEXT = "🚀 Открыть приложение"
HELP_BUTTON_TEXT = "❓ Помощь"
BALANCE_BUTTON_TEXT = "💰 Баланс"
PROFILE_BUTTON_TEXT = "👤 Профиль"
REFERRAL_BUTTON_TEXT = "🎁 Пригласить друга"

# Новые кнопки главного меню
CREATE_IMAGE_BUTTON_TEXT = "🖼 Создать изображение"
CREATE_VIDEO_BUTTON_TEXT = "🎬 Создать видео"
TRENDING_PROMPTS_BUTTON_TEXT = "🔥 Трендовые промты"
EARN_TOKENS_BUTTON_TEXT = "💎 Заработать токены"

# === Telegram Channel ===
TELEGRAM_CHANNEL_URL = "https://t.me/aimakepromt"

# === Generation ===
GENERATION_POLL_INTERVAL = 3
GENERATION_MAX_POLL_ATTEMPTS = 120

# === Files ===
MAX_FILE_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}

# === Payments ===
PAYMENT_PACKAGES_USD = [
    {"id": "standard", "name": "Стандарт", "amount": 10,  "tokens": 300,  "offer_id": "8209d23e-e188-43c5-b725-a04a6391f5e1"},
    {"id": "vip",      "name": "VIP",      "amount": 20,  "tokens": 630,  "offer_id": "33167ef1-0032-454b-ac93-f0eecef8e95e"},
    {"id": "premium",  "name": "Премиум",  "amount": 40,  "tokens": 1300, "offer_id": "4e1aedfe-8f24-4750-8915-4bcdcd58cc8f"},
    {"id": "platinum", "name": "Платина",  "amount": 80,  "tokens": 2650, "offer_id": "12b79195-2c40-4f03-9f50-0b66f2855d81"},
]
PAYMENT_PACKAGES_RUB = [
    {"id": "standard", "name": "Стандарт", "amount": 760,  "tokens": 300,  "offer_id": "8209d23e-e188-43c5-b725-a04a6391f5e1"},
    {"id": "vip",      "name": "VIP",      "amount": 1500, "tokens": 630,  "offer_id": "33167ef1-0032-454b-ac93-f0eecef8e95e"},
    {"id": "premium",  "name": "Премиум",  "amount": 3000, "tokens": 1300, "offer_id": "4e1aedfe-8f24-4750-8915-4bcdcd58cc8f"},
    {"id": "platinum", "name": "Платина",  "amount": 6150, "tokens": 2650, "offer_id": "12b79195-2c40-4f03-9f50-0b66f2855d81"},
]
# Для обратной совместимости
PAYMENT_PACKAGES = PAYMENT_PACKAGES_USD
PAYMENT_CURRENCY = "USD"
MIN_PAYMENT_AMOUNT = 10
MAX_PAYMENT_AMOUNT = 80

# === Cache TTL (seconds) ===
CACHE_USER_TTL = 300
CACHE_MODELS_TTL = 60

