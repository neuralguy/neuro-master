"""Start and help handlers."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.bot.keyboards.inline import get_webapp_keyboard
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.config import settings
from src.core.security import generate_webapp_token
from src.modules.user.models import User
from src.shared.logger import logger

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    db_user: User,
    is_new_user: bool,
) -> None:
    """Handle /start command."""
    token = generate_webapp_token(message.from_user.id)

    if is_new_user:
        text = (
            "👋 Добро пожаловать!\n\n"
            f"🎁 Вам начислено <b>{settings.WELCOME_BONUS} токенов</b> в подарок!\n\n"
            "🤖 Я помогу вам создавать:\n"
            "• 🖼 Изображения с помощью ИИ\n"
            "• 🎬 Видео из текста и картинок\n\n"
            "Нажмите кнопку ниже, чтобы начать 👇"
        )
        logger.info(f"New user started bot | user_id={db_user.telegram_id}")
    else:
        text = (
            "👋 С возвращением!\n\n"
            f"💰 Ваш баланс: <b>{db_user.balance} токенов</b>\n\n"
            "Выберите действие 👇"
        )

    await message.answer(
        text,
        reply_markup=get_main_menu_keyboard(message.from_user.id, token),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User) -> None:
    """Handle /help command."""
    logger.info(f"Help command | user_id={db_user.telegram_id}")

    text = (
        "📖 <b>Справка</b>\n\n"
        "🤖 <b>Возможности бота:</b>\n"
        "• Генерация изображений по описанию\n"
        "• Создание видео из текста/картинок\n\n"
        "💰 <b>Токены:</b>\n"
        f"• При регистрации: {settings.WELCOME_BONUS} токенов\n"
        f"• За приглашённого друга: {settings.REFERRAL_BONUS} токенов\n\n"
        "📱 <b>Как пользоваться:</b>\n"
        "1. Откройте приложение кнопкой ниже\n"
        "2. Выберите тип генерации\n"
        "3. Введите описание или загрузите фото\n"
        "4. Дождитесь результата\n\n"
        "❓ <b>Команды:</b>\n"
        "/start — Главное меню\n"
        "/help — Эта справка\n\n"
        "💬 По вопросам: @support"
    )

    await message.answer(text, reply_markup=get_webapp_keyboard())


@router.message(Command("id"))
async def cmd_id(message: Message, db_user: User) -> None:
    """Handle /id command - show user's Telegram ID."""
    logger.debug(f"ID command | user_id={db_user.telegram_id}")
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
        f"📊 ID в системе: <code>{db_user.id}</code>"
    )

