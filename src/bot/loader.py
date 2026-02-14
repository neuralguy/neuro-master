"""Bot and dispatcher initialization."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from src.config import settings
from src.shared.logger import logger


def create_storage():
    """Create FSM storage based on environment."""
    if settings.DEV_MODE:
        logger.info("Bot FSM storage: MemoryStorage (dev mode)")
        return MemoryStorage()
    
    logger.info(f"Bot FSM storage: RedisStorage | url={settings.REDIS_URL}")
    return RedisStorage.from_url(settings.REDIS_URL)


# Bot instance
bot = Bot(
    token=settings.BOT_TOKEN.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    ),
)

# Dispatcher instance
dp = Dispatcher(storage=create_storage())


async def get_bot_info() -> dict:
    """Get bot information."""
    me = await bot.get_me()
    return {
        "id": me.id,
        "username": me.username,
        "first_name": me.first_name,
    }
