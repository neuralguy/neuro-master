"""Payment handlers."""

import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.inline import get_payment_amounts_keyboard, get_payment_keyboard
from src.bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard
from src.modules.payments.service import PaymentService
from src.modules.user.models import User
from src.shared.constants import MAX_PAYMENT_AMOUNT, MIN_PAYMENT_AMOUNT
from src.shared.logger import logger

router = Router(name="payments")


class PaymentStates(StatesGroup):
    """Payment FSM states."""
    waiting_for_amount = State()


@router.callback_query(F.data.startswith("pay_amount:"))
async def callback_pay_amount(
    callback: CallbackQuery,
    db_user: User,
    session: AsyncSession,
) -> None:
    """Handle predefined payment amount selection."""
    await callback.answer()
    
    amount = int(callback.data.split(":")[1])
    logger.info(f"Payment amount selected | user_id={db_user.telegram_id}, amount={amount}")
    
    payment_service = PaymentService(session)
    
    try:
        payment, confirmation_url = await payment_service.create_payment(
            user_id=db_user.id,
            amount=amount,
        )
        
        text = (
            f"💳 <b>Оплата</b>\n\n"
            f"💰 Сумма: <b>{amount} ₽</b>\n"
            f"🪙 Получите: <b>{amount} токенов</b>\n\n"
            "Нажмите кнопку «Оплатить» для перехода к оплате.\n"
            "После оплаты нажмите «Проверить оплату»."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_payment_keyboard(confirmation_url, str(payment.id)),
        )
        
        logger.info(f"Payment created | user_id={db_user.telegram_id}, payment_id={payment.id}, amount={amount}")
        
    except Exception as e:
        logger.error(f"Payment creation failed | user_id={db_user.telegram_id}, amount={amount}, error={e}")
        await callback.message.edit_text(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            reply_markup=get_payment_amounts_keyboard(),
        )


@router.callback_query(F.data == "pay_custom")
async def callback_pay_custom(
    callback: CallbackQuery,
    state: FSMContext,
    db_user: User,
) -> None:
    """Handle custom payment amount button."""
    await callback.answer()
    logger.debug(f"Custom payment amount requested | user_id={db_user.telegram_id}")
    
    await state.set_state(PaymentStates.waiting_for_amount)
    
    await callback.message.edit_text(
        f"💰 <b>Введите сумму пополнения</b>\n\n"
        f"Минимум: {MIN_PAYMENT_AMOUNT} ₽\n"
        f"Максимум: {MAX_PAYMENT_AMOUNT} ₽\n\n"
        "Отправьте число:"
    )


@router.message(PaymentStates.waiting_for_amount)
async def process_custom_amount(
    message: Message,
    state: FSMContext,
    db_user: User,
    session: AsyncSession,
) -> None:
    """Process custom payment amount."""
    
    # Handle cancel
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "✅ Отменено",
            reply_markup=get_main_menu_keyboard(),
        )
        return
    
    # Validate amount
    try:
        amount = int(message.text.strip())
    except ValueError:
        logger.debug(f"Invalid payment amount format | user_id={db_user.telegram_id}, input={message.text}")
        await message.answer(
            "❌ Введите число. Например: 500"
        )
        return
    
    if amount < MIN_PAYMENT_AMOUNT:
        logger.debug(f"Payment amount too low | user_id={db_user.telegram_id}, amount={amount}")
        await message.answer(
            f"❌ Минимальная сумма: {MIN_PAYMENT_AMOUNT} ₽"
        )
        return
    
    if amount > MAX_PAYMENT_AMOUNT:
        logger.debug(f"Payment amount too high | user_id={db_user.telegram_id}, amount={amount}")
        await message.answer(
            f"❌ Максимальная сумма: {MAX_PAYMENT_AMOUNT} ₽"
        )
        return
    
    await state.clear()
    
    # Create payment
    payment_service = PaymentService(session)
    
    try:
        payment, confirmation_url = await payment_service.create_payment(
            user_id=db_user.id,
            amount=amount,
        )
        
        text = (
            f"💳 <b>Оплата</b>\n\n"
            f"💰 Сумма: <b>{amount} ₽</b>\n"
            f"🪙 Получите: <b>{amount} токенов</b>\n\n"
            "Нажмите кнопку «Оплатить» для перехода к оплате.\n"
            "После оплаты нажмите «Проверить оплату»."
        )
        
        await message.answer(
            text,
            reply_markup=get_payment_keyboard(confirmation_url, str(payment.id)),
        )
        
        logger.info(f"Custom payment created | user_id={db_user.telegram_id}, payment_id={payment.id}, amount={amount}")
        
    except Exception as e:
        logger.error(f"Custom payment creation failed | user_id={db_user.telegram_id}, amount={amount}, error={e}")
        await message.answer(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


@router.callback_query(F.data.startswith("check_payment:"))
async def callback_check_payment(
    callback: CallbackQuery,
    db_user: User,
    session: AsyncSession,
) -> None:
    """Handle payment check button."""
    payment_id = callback.data.split(":")[1]
    logger.info(f"Payment check requested | user_id={db_user.telegram_id}, payment_id={payment_id}")
    
    payment_service = PaymentService(session)
    
    try:
        payment_uuid = uuid.UUID(payment_id)
        payment = await payment_service.get_payment(payment_uuid)
        
        if not payment:
            logger.warning(f"Payment not found | user_id={db_user.telegram_id}, payment_id={payment_id}")
            await callback.answer("❌ Платёж не найден", show_alert=True)
            return
        
        if payment.user_id != db_user.id:
            logger.warning(f"Payment access denied | user_id={db_user.telegram_id}, payment_id={payment_id}, owner_id={payment.user_id}")
            await callback.answer("❌ Это не ваш платёж", show_alert=True)
            return
        
        # Check payment status
        result = await payment_service.check_payment_status(payment)
        
        if result["success"]:
            await callback.answer("✅ Оплата прошла успешно!", show_alert=True)
            
            await callback.message.edit_text(
                f"✅ <b>Оплата успешна!</b>\n\n"
                f"💰 Сумма: {payment.amount} ₽\n"
                f"🪙 Начислено: {payment.tokens} токенов\n\n"
                f"💳 Ваш новый баланс: <b>{result['new_balance']} токенов</b>"
            )
            
            logger.info(
                f"Payment successful | user_id={db_user.telegram_id}, payment_id={payment.id}, "
                f"amount={payment.amount}, tokens={payment.tokens}, new_balance={result['new_balance']}"
            )
        else:
            status_text = {
                "pending": "⏳ Ожидание оплаты",
                "canceled": "❌ Платёж отменён",
            }.get(result["status"], f"❓ Статус: {result['status']}")
            
            logger.debug(f"Payment pending | user_id={db_user.telegram_id}, payment_id={payment.id}, status={result['status']}")
            await callback.answer(status_text, show_alert=True)
            
    except Exception as e:
        logger.error(f"Payment check failed | user_id={db_user.telegram_id}, payment_id={payment_id}, error={e}")
        await callback.answer("❌ Ошибка проверки платежа", show_alert=True)


@router.callback_query(F.data.startswith("cancel_payment:"))
async def callback_cancel_payment(
    callback: CallbackQuery,
    db_user: User,
) -> None:
    """Handle payment cancellation."""
    await callback.answer()
    payment_id = callback.data.split(":")[1]
    logger.info(f"Payment cancelled by user | user_id={db_user.telegram_id}, payment_id={payment_id}")
    
    await callback.message.edit_text(
        "❌ Платёж отменён.\n\n"
        "Выберите сумму для пополнения:",
        reply_markup=get_payment_amounts_keyboard(),
    )


@router.callback_query(F.data == "pay_cancel")
async def callback_pay_cancel(callback: CallbackQuery) -> None:
    """Handle payment menu cancel."""
    await callback.answer()
    await callback.message.delete()
