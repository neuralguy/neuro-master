"""Main menu handlers."""

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.inline import (
    get_payment_amounts_keyboard,
    get_referral_keyboard,
    get_trending_prompts_keyboard,
    get_webapp_keyboard,
)
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.core.security import generate_webapp_token
from src.modules.user.models import User
from src.modules.user.service import UserService
from src.shared.constants import (
    HELP_BUTTON_TEXT,
    TRENDING_PROMPTS_BUTTON_TEXT,
)
from src.bot.loader import bot
from src.shared.logger import logger

router = Router(name="menu")


@router.message(F.text == TRENDING_PROMPTS_BUTTON_TEXT)
async def menu_trending_prompts(message: Message, db_user: User) -> None:
    """Handle Trending Prompts button."""
    logger.info(f"Trending prompts opened | user_id={db_user.telegram_id}")

    text = (
        "🖤 Закрытая коллекция премиальных промтов — каждый день "
        "в нашем Telegram-канале.\n\n"
        "Берите готовые решения и создавайте визуал уровня luxury "
        "за считанные минуты 👇"
    )

    await message.answer(text, reply_markup=get_trending_prompts_keyboard())


@router.message(F.text == HELP_BUTTON_TEXT)
async def menu_help(message: Message, db_user: User) -> None:
    """Handle Help button - redirect to /help."""
    from src.bot.handlers.start import cmd_help
    await cmd_help(message, db_user)


@router.message(F.text == "❌ Отмена")
async def menu_cancel(message: Message) -> None:
    """Handle Cancel button."""
    token = generate_webapp_token(message.from_user.id)
    await message.answer(
        "✅ Действие отменено",
        reply_markup=get_main_menu_keyboard(message.from_user.id, token),
    )

