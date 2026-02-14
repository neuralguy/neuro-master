"""Application entry point."""

import asyncio

import uvicorn
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat

from src.api.app import app as fastapi_app
from src.bot.handlers import setup_routers
from src.bot.loader import bot, dp
from src.bot.middlewares import (
    AuthMiddleware,
    DatabaseMiddleware,
    LoggingMiddleware,
    ThrottlingMiddleware,
)
from src.config import settings
from src.core.database import async_session_maker, check_db_connection, close_db, init_db
from src.core.redis import check_redis_connection, close_redis
from src.modules.ai_models.service import seed_default_models
from src.shared.logger import enable_telegram_logging, logger


async def set_bot_commands(bot: Bot) -> None:
    """Set bot commands."""
    commands = [
        BotCommand(command="start", description="🚀 Главное меню"),
        BotCommand(command="help", description="❓ Помощь"),
    ]
    
    # Add admin command for admins
    admin_commands = commands + [
        BotCommand(command="admin", description="🔐 Админ-панель"),
    ]
    
    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    
    # Set admin commands for each admin
    from aiogram.types import BotCommandScopeChat
    for admin_id in settings.admin_ids_list:
        try:
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception as e:
            logger.warning(f"Failed to set admin commands | admin_id={admin_id}, error={e}")


async def on_startup() -> None:
    """Application startup tasks."""
    logger.info("=" * 60)
    logger.info(f"Starting AI Content Bot | dev_mode={settings.DEV_MODE}")
    logger.info("=" * 60)

    # Check database connection
    if not await check_db_connection():
        raise RuntimeError("Failed to connect to database")
    logger.info("Database connection OK")

    # Check Redis connection
    if not await check_redis_connection():
        raise RuntimeError("Failed to connect to Redis")
    logger.info("Redis connection OK")

    # Initialize database tables
    await init_db()

    # Seed default AI models
    async with async_session_maker() as session:
        await seed_default_models(session)
    logger.info("AI models seeded")

    # Setup bot commands
    await set_bot_commands(bot)
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot started | username=@{bot_info.username}, id={bot_info.id}")

    # Enable Telegram logging if configured
    if settings.LOG_TELEGRAM_CHAT_ID:
        enable_telegram_logging(
            bot,
            settings.LOG_TELEGRAM_CHAT_ID,
            level="WARNING",
        )


async def on_shutdown() -> None:
    """Application shutdown tasks."""
    logger.info("Shutting down...")
    
    await close_db()
    await close_redis()
    await bot.session.close()
    
    logger.info("Bot stopped")


async def run_bot() -> None:
    """Run Telegram bot."""
    # Setup middlewares (order matters!)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.3))
    
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Setup routers
    main_router = setup_routers()
    dp.include_router(main_router)
    
    # Register startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    logger.info("Starting bot polling...")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


async def run_api() -> None:
    """Run FastAPI server."""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info" if settings.DEV_MODE else "warning",
    )
    server = uvicorn.Server(config)
    
    logger.info("Starting FastAPI server on port 8000...")
    await server.serve()


async def main() -> None:
    """Main entry point - run both bot and API."""
    try:
        # Run both bot and API concurrently
        await asyncio.gather(
            run_bot(),
            run_api(),
        )
    except Exception as e:
        logger.exception(f"Application error | error={e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
