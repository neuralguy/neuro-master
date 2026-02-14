"""Payment handlers."""

import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.inline import get_payment_packages_keyboard, get_payment_keyboard
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.modules.payments.service import PaymentService
from src.modules.user.models import User
from src.shared.constants import PAYMENT_PACKAGES
from src.shared.logger import logger

router = Router(name="payments")


@router.callback_query(F.data.startswith("pay_package:"))
async def callback_pay_package(
    callback: CallbackQuery,
    db_user: User,
    session: AsyncSession,
) -> None:
    """Handle payment package selection."""
    await callback.answer()

    package_id = callback.data.split(":")[1]

    # Find package
    package = next(
        (pkg for pkg in PAYMENT_PACKAGES if pkg["id"] == package_id),
        None,
    )
    if not package:
        await callback.answer("Неизвестный пакет", show_alert=True)
        return

    logger.info(
        f"Payment package selected | user_id={db_user.telegram_id}, "
        f"package={package_id}, amount=${package['amount']}"
    )

    payment_service = PaymentService(session)

    try:
        payment, confirmation_url = await payment_service.create_payment(
            user_id=db_user.id,
            amount=package["amount"],
            tokens=package["tokens"],
            package_name=package["name"],
        )

        text = (
            f"💳 <b>Оплата</b>\n\n"
            f"📦 Пакет: <b>{package['name']}</b>\n"
            f"💰 Сумма: <b>${package['amount']}</b>\n"
            f"🪙 Получите: <b>{package['tokens']} токенов</b>\n\n"
            "Нажмите «Оплатить» для перехода к оплате.\n"
            "После оплаты нажмите «Проверить оплату»."
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_payment_keyboard(confirmation_url, str(payment.id)),
        )

        logger.info(
            f"Payment created | user_id={db_user.telegram_id}, "
            f"payment_id={payment.id}, package={package_id}"
        )

    except Exception as e:
        logger.error(
            f"Payment creation failed | user_id={db_user.telegram_id}, "
            f"package={package_id}, error={e}"
        )
        await callback.message.edit_text(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            reply_markup=get_payment_packages_keyboard(),
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
            logger.warning(
                f"Payment access denied | user_id={db_user.telegram_id}, "
                f"payment_id={payment_id}, owner_id={payment.user_id}"
            )
            await callback.answer("❌ Это не ваш платёж", show_alert=True)
            return

        # Check payment status
        result = await payment_service.check_payment_status(payment)

        if result["success"]:
            await callback.answer("✅ Оплата прошла успешно!", show_alert=True)

            await callback.message.edit_text(
                f"✅ <b>Оплата успешна!</b>\n\n"
                f"💰 Сумма: ${payment.amount}\n"
                f"🪙 Начислено: {payment.tokens} токенов\n\n"
                f"💳 Ваш новый баланс: <b>{result['new_balance']} токенов</b>"
            )

            logger.info(
                f"Payment successful | user_id={db_user.telegram_id}, payment_id={payment.id}, "
                f"amount=${payment.amount}, tokens={payment.tokens}, new_balance={result['new_balance']}"
            )
        else:
            status_text = {
                "pending": "⏳ Ожидание оплаты",
                "canceled": "❌ Платёж отменён",
            }.get(result["status"], f"❓ Статус: {result['status']}")

            logger.debug(
                f"Payment pending | user_id={db_user.telegram_id}, "
                f"payment_id={payment.id}, status={result['status']}"
            )
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
        "Выберите пакет для пополнения:",
        reply_markup=get_payment_packages_keyboard(),
    )


@router.callback_query(F.data == "pay_cancel")
async def callback_pay_cancel(callback: CallbackQuery) -> None:
    """Handle payment menu cancel."""
    await callback.answer()
    await callback.message.delete()

