"""Main menu handlers."""

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.inline import get_payment_amounts_keyboard, get_referral_keyboard, get_webapp_keyboard
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.core.security import generate_webapp_token
from src.modules.user.models import User
from src.modules.user.service import UserService
from src.shared.constants import (
    BALANCE_BUTTON_TEXT,
    HELP_BUTTON_TEXT,
    PROFILE_BUTTON_TEXT,
    REFERRAL_BUTTON_TEXT,
    WEBAPP_BUTTON_TEXT,
)
from src.bot.loader import bot
from src.shared.logger import logger

router = Router(name="menu")


@router.message(F.text == BALANCE_BUTTON_TEXT)
async def menu_balance(message: Message, db_user: User, session: AsyncSession) -> None:
    """Handle Balance button."""
    logger.info(f"Balance menu opened | user_id={db_user.telegram_id}, balance={db_user.balance}")
    user_service = UserService(session)
    history = await user_service.get_balance_history(db_user.id, limit=5)
    
    history_text = ""
    if history:
        history_text = "\n\n📋 <b>Последние операции:</b>\n"
        for record in history:
            sign = "+" if record.amount > 0 else ""
            emoji = "💰" if record.amount > 0 else "💸"
            history_text += f"{emoji} {sign}{record.amount} — {record.description}\n"
    
    text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"🪙 Токенов: <b>{db_user.balance}</b>\n"
        f"{history_text}\n"
        "Пополнить баланс:"
    )
    
    await message.answer(text, reply_markup=get_payment_amounts_keyboard())


@router.message(F.text == PROFILE_BUTTON_TEXT)
async def menu_profile(message: Message, db_user: User, session: AsyncSession) -> None:
    """Handle Profile button."""
    logger.info(f"Profile menu opened | user_id={db_user.telegram_id}")
    user_service = UserService(session)
    
    referral_info = await user_service.get_referral_info(db_user)
    reg_date = db_user.created_at.strftime("%d.%m.%Y")
    
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"📛 Имя: {db_user.full_name}\n"
        f"🆔 ID: <code>{db_user.telegram_id}</code>\n"
        f"📅 Регистрация: {reg_date}\n\n"
        f"💰 Баланс: <b>{db_user.balance} токенов</b>\n\n"
        f"👥 Приглашено друзей: {referral_info['total_referrals']}\n"
        f"🎁 Заработано бонусов: {referral_info['total_bonus_earned']} токенов"
    )
    
    await message.answer(text, reply_markup=get_webapp_keyboard())


@router.message(F.text == REFERRAL_BUTTON_TEXT)
async def menu_referral(message: Message, db_user: User, session: AsyncSession) -> None:
    """Handle Referral button."""
    logger.info(f"Referral menu opened | user_id={db_user.telegram_id}, referral_code={db_user.referral_code}")
    user_service = UserService(session)
    
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={db_user.referral_code}"
    
    referral_info = await user_service.get_referral_info(db_user)
    
    text = (
        f"🎁 <b>Пригласи друга</b>\n\n"
        f"Приглашай друзей и получай <b>{50} токенов</b> за каждого!\n\n"
        f"🔗 Твоя ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"👥 Приглашено: {referral_info['total_referrals']}\n"
        f"💰 Заработано: {referral_info['total_bonus_earned']} токенов"
    )
    
    await message.answer(text, reply_markup=get_referral_keyboard(referral_link))


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

