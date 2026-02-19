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
PAYMENT_PACKAGES = [
    {"id": "standard", "name": "Стандарт", "amount": 10, "tokens": 300,  "offer_id": "5d8bdfaa-d141-499a-b2fe-09a6312bc96b"},
    {"id": "vip",      "name": "VIP",      "amount": 20, "tokens": 630,  "offer_id": "32aa9ae1-ced9-47bb-b5c1-2166a4eb41a9"},
    {"id": "premium",  "name": "Премиум",  "amount": 40, "tokens": 1300, "offer_id": "490746bb-b9d0-44f3-92e4-a0e0b4552659"},
    {"id": "platinum", "name": "Платина",   "amount": 80, "tokens": 2650, "offer_id": "5250344d-6fb5-4355-9bff-051cce02c094"},
]
PAYMENT_CURRENCY = "USD"
MIN_PAYMENT_AMOUNT = 10
MAX_PAYMENT_AMOUNT = 80

# === Cache TTL (seconds) ===
CACHE_USER_TTL = 300
CACHE_MODELS_TTL = 60

