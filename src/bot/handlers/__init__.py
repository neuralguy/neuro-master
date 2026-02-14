"""Bot handlers."""

from aiogram import Router

from src.bot.handlers.start import router as start_router
from src.bot.handlers.menu import router as menu_router
from src.bot.handlers.admin import router as admin_router
from src.bot.handlers.payments import router as payments_router


def setup_routers() -> Router:
    """Setup and return main router with all handlers."""
    router = Router()
    
    # Include routers in order of priority
    router.include_router(admin_router)
    router.include_router(start_router)
    router.include_router(payments_router)
    router.include_router(menu_router)
    
    return router
