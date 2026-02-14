"""Admin handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters.admin import AdminFilter
from src.bot.keyboards.inline import get_admin_keyboard
from src.modules.payments.repository import PaymentRepository
from src.modules.user.models import User
from src.modules.user.service import UserService
from src.shared.logger import logger

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message, db_user: User) -> None:
    """Handle /admin command."""
    logger.info(f"Admin panel opened | admin_id={db_user.telegram_id}")
    
    text = (
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите раздел:"
    )
    
    await message.answer(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin:stats")
async def callback_admin_stats(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    """Handle admin stats button."""
    await callback.answer()
    logger.info(f"Admin stats requested | admin_id={db_user.telegram_id}")
    
    user_service = UserService(session)
    payment_repo = PaymentRepository(session)
    
    user_stats = await user_service.get_stats()
    payment_stats = await payment_repo.get_stats()
    
    text = (
        "📊 <b>Статистика</b>\n\n"
        
        "👥 <b>Пользователи:</b>\n"
        f"• Всего: {user_stats['total_users']}\n"
        f"• Заблокировано: {user_stats['banned_users']}\n"
        f"• Общий баланс: {user_stats['total_balance']} токенов\n\n"
        
        "💳 <b>Платежи:</b>\n"
        f"• Успешных: {payment_stats['total_payments']}\n"
        f"• Сумма: {payment_stats['total_amount']} ₽\n"
        f"• В ожидании: {payment_stats['pending_payments']}\n"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin:users")
async def callback_admin_users(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    """Handle admin users button."""
    await callback.answer()
    logger.info(f"Admin users list requested | admin_id={db_user.telegram_id}")
    
    user_service = UserService(session)
    users, total = await user_service.get_all_users(limit=10)
    
    text = f"👥 <b>Пользователи</b> (всего: {total})\n\n"
    
    for user in users[:10]:
        status = "🚫" if user.is_banned else "✅"
        admin = "👑" if user.is_admin else ""
        text += (
            f"{status}{admin} {user.display_name}\n"
            f"   ID: <code>{user.telegram_id}</code> | 💰 {user.balance}\n"
        )
    
    text += "\n🌐 Откройте админку для полного управления"
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin:payments")
async def callback_admin_payments(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User,
) -> None:
    """Handle admin payments button."""
    await callback.answer()
    logger.info(f"Admin payments list requested | admin_id={db_user.telegram_id}")
    
    payment_repo = PaymentRepository(session)
    payments = await payment_repo.get_all_payments(limit=10)
    
    text = "💳 <b>Последние платежи</b>\n\n"
    
    for payment in payments[:10]:
        status_emoji = {
            "success": "✅",
            "pending": "⏳",
            "failed": "❌",
            "cancelled": "🚫",
        }.get(payment.status.value, "❓")
        
        date = payment.created_at.strftime("%d.%m %H:%M")
        text += f"{status_emoji} {payment.amount}₽ | {date}\n"
    
    text += "\n🌐 Откройте админку для полного управления"
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin:models")
async def callback_admin_models(callback: CallbackQuery) -> None:
    """Handle admin models button."""
    await callback.answer()
    
    text = (
        "🤖 <b>AI Модели</b>\n\n"
        "Управление моделями доступно в веб-админке.\n\n"
        "🌐 Откройте админку для настройки моделей и цен."
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "back_to_admin")
async def callback_back_to_admin(callback: CallbackQuery, db_user: User) -> None:
    """Handle back to admin menu."""
    await callback.answer()
    
    text = (
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите раздел:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
