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
TELEGRAM_CHANNEL_URL = "https://t.me/your_channel"  # <-- замените на реальную ссылку

# === Generation ===
GENERATION_POLL_INTERVAL = 3  # seconds
GENERATION_MAX_POLL_ATTEMPTS = 120  # 6 minutes max

# === Files ===
MAX_FILE_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}

# === Payments ===
MIN_PAYMENT_AMOUNT = 50  # рублей
MAX_PAYMENT_AMOUNT = 50000  # рублей
PAYMENT_PACKAGES = [100, 300, 500, 1000, 2000, 5000]  # предустановленные суммы

# === Cache TTL (seconds) ===
CACHE_USER_TTL = 300  # 5 minutes
CACHE_MODELS_TTL = 60  # 1 minute

