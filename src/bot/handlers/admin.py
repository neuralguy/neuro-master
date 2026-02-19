"""Admin handlers."""

import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters.admin import AdminFilter
from src.bot.keyboards.inline import (
    get_admin_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_filter_keyboard,
)
from src.bot.loader import bot
from src.modules.payments.repository import PaymentRepository
from src.modules.user.models import User
from src.modules.user.repository import UserRepository
from src.modules.user.service import UserService
from src.shared.logger import logger


class BroadcastStates(StatesGroup):
    choosing_filter = State()
    entering_balance = State()
    entering_message = State()
    confirming = State()

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
async def callback_back_to_admin(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    """Handle back to admin menu."""
    await callback.answer()
    await state.clear()

    text = (
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите раздел:"
    )

    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())


# === Broadcast handlers ===

@router.callback_query(F.data == "admin:broadcast")
async def callback_admin_broadcast(
    callback: CallbackQuery,
    db_user: User,
    state: FSMContext,
) -> None:
    """Start broadcast flow."""
    await callback.answer()
    await state.set_state(BroadcastStates.choosing_filter)

    logger.info(f"Broadcast started | admin_id={db_user.telegram_id}")

    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Выберите, кому отправить сообщение:",
        reply_markup=get_broadcast_filter_keyboard(),
    )


@router.callback_query(BroadcastStates.choosing_filter, F.data.startswith("broadcast:filter:"))
async def callback_broadcast_filter(
    callback: CallbackQuery,
    db_user: User,
    state: FSMContext,
) -> None:
    """Handle filter selection."""
    await callback.answer()
    filter_type = callback.data.split(":")[-1]  # gte / lte / all

    if filter_type == "all":
        await state.update_data(filter_type="all", balance_threshold=None)
        await state.set_state(BroadcastStates.entering_message)
        await callback.message.edit_text(
            "📢 <b>Рассылка — всем пользователям</b>\n\n"
            "Введите текст сообщения для рассылки:"
        )
    else:
        await state.update_data(filter_type=filter_type)
        await state.set_state(BroadcastStates.entering_balance)
        label = "больше" if filter_type == "gte" else "меньше"
        await callback.message.edit_text(
            f"📢 <b>Рассылка</b>\n\n"
            f"Введите порог токенов. Сообщение получат пользователи с балансом <b>{label}</b> указанного числа:"
        )


@router.message(BroadcastStates.entering_balance)
async def handle_broadcast_balance(
    message: Message,
    db_user: User,
    state: FSMContext,
) -> None:
    """Handle balance threshold input."""
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("⚠️ Введите целое число (количество токенов):")
        return

    await state.update_data(balance_threshold=int(text))
    await state.set_state(BroadcastStates.entering_message)

    data = await state.get_data()
    label = "больше" if data["filter_type"] == "gte" else "меньше"
    await message.answer(
        f"✅ Порог: <b>{text}</b> токенов ({label}).\n\n"
        "Теперь введите текст сообщения для рассылки:"
    )


@router.message(BroadcastStates.entering_message)
async def handle_broadcast_message(
    message: Message,
    db_user: User,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Handle broadcast message input and show preview with confirmation."""
    if not message.text:
        await message.answer("⚠️ Поддерживается только текстовое сообщение. Введите текст:")
        return

    await state.update_data(broadcast_text=message.text)
    data = await state.get_data()

    user_repo = UserRepository(session)
    filter_type = data["filter_type"]
    balance_threshold = data.get("balance_threshold")

    if filter_type == "all":
        users = await user_repo.get_all(limit=100_000, is_banned=False)
    else:
        users = await user_repo.get_by_balance_filter(
            balance_threshold=balance_threshold,
            comparison=filter_type,
        )

    count = len(users)
    await state.update_data(recipient_ids=[u.telegram_id for u in users])
    await state.set_state(BroadcastStates.confirming)

    if filter_type == "all":
        filter_desc = "👥 Все незабаненные пользователи"
    elif filter_type == "gte":
        filter_desc = f"📈 Баланс ≥ {balance_threshold} токенов"
    else:
        filter_desc = f"📉 Баланс ≤ {balance_threshold} токенов"

    preview = (
        f"📢 <b>Предпросмотр рассылки</b>\n\n"
        f"<b>Фильтр:</b> {filter_desc}\n"
        f"<b>Получателей:</b> {count} чел.\n\n"
        f"<b>Текст сообщения:</b>\n"
        f"<blockquote>{message.text}</blockquote>\n\n"
        f"Отправить?"
    )

    await message.answer(preview, reply_markup=get_broadcast_confirm_keyboard(count))


@router.callback_query(BroadcastStates.confirming, F.data == "broadcast:confirm")
async def callback_broadcast_confirm(
    callback: CallbackQuery,
    db_user: User,
    state: FSMContext,
) -> None:
    """Execute the broadcast."""
    await callback.answer()
    data = await state.get_data()
    await state.clear()

    recipient_ids: list[int] = data.get("recipient_ids", [])
    broadcast_text: str = data.get("broadcast_text", "")

    logger.info(
        f"Broadcast sending | admin_id={db_user.telegram_id}, "
        f"recipients={len(recipient_ids)}"
    )

    await callback.message.edit_text(
        f"⏳ Начинаю рассылку для {len(recipient_ids)} пользователей..."
    )

    success = 0
    failed = 0

    for telegram_id in recipient_ids:
        try:
            await bot.send_message(chat_id=telegram_id, text=broadcast_text)
            success += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast failed for user | telegram_id={telegram_id}, error={e}")
        # Соблюдаем лимит Telegram: ~30 msg/sec
        await asyncio.sleep(0.05)

    logger.info(
        f"Broadcast done | admin_id={db_user.telegram_id}, "
        f"success={success}, failed={failed}"
    )

    await callback.message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"• Отправлено: {success}\n"
        f"• Ошибок: {failed}",
        reply_markup=get_admin_keyboard(),
    )


@router.callback_query(BroadcastStates.confirming, F.data == "broadcast:cancel")
async def callback_broadcast_cancel(
    callback: CallbackQuery,
    db_user: User,
    state: FSMContext,
) -> None:
    """Cancel broadcast."""
    await callback.answer("Рассылка отменена")
    await state.clear()

    await callback.message.edit_text(
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_admin_keyboard(),
    )
