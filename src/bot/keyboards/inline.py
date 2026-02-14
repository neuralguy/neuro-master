"""Inline keyboards for bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.config import settings
from src.shared.constants import PAYMENT_PACKAGES, TELEGRAM_CHANNEL_URL


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with WebApp button."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть приложение",
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                ),
            ],
        ]
    )
    return keyboard


def get_trending_prompts_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with link to trending prompts channel."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Перейти в канал",
                    url=TELEGRAM_CHANNEL_URL,
                ),
            ],
        ]
    )
    return keyboard


def get_payment_keyboard(payment_url: str, payment_id: str) -> InlineKeyboardMarkup:
    """Get payment keyboard with pay and check buttons."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    url=payment_url,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_payment:{payment_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"cancel_payment:{payment_id}",
                ),
            ],
        ]
    )
    return keyboard


def get_payment_amounts_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with predefined payment amounts."""
    buttons = []
    row = []
    
    for i, amount in enumerate(PAYMENT_PACKAGES):
        row.append(
            InlineKeyboardButton(
                text=f"{amount} ₽",
                callback_data=f"pay_amount:{amount}",
            )
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    # Add custom amount button
    buttons.append([
        InlineKeyboardButton(
            text="💰 Другая сумма",
            callback_data="pay_custom",
        )
    ])
    
    buttons.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="pay_cancel",
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """Get referral keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Поделиться ссылкой",
                    url=f"https://t.me/share/url?url={referral_link}&text=🎁 Присоединяйся! Получи 50 бесплатных токенов для генерации AI контента!",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Скопировать ссылку",
                    callback_data="copy_referral",
                ),
            ],
        ]
    )
    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin:stats",
                ),
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin:users",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💳 Платежи",
                    callback_data="admin:payments",
                ),
                InlineKeyboardButton(
                    text="🤖 Модели",
                    callback_data="admin:models",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Открыть админку",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/admin"),
                ),
            ],
        ]
    )
    return keyboard


def get_confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да",
                    callback_data=f"confirm:{action}:{data}",
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data="cancel",
                ),
            ],
        ]
    )
    return keyboard


def get_back_keyboard(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Get back button keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=callback_data,
                ),
            ],
        ]
    )


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
) -> InlineKeyboardMarkup:
    """Get pagination keyboard."""
    buttons = []
    
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"{callback_prefix}:{current_page - 1}",
            )
        )
    
    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop",
        )
    )
    
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"{callback_prefix}:{current_page + 1}",
            )
        )
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

