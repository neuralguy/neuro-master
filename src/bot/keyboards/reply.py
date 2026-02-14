"""Reply keyboards for bot."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from src.config import settings
from src.shared.constants import (
    BALANCE_BUTTON_TEXT,
    HELP_BUTTON_TEXT,
    PROFILE_BUTTON_TEXT,
    REFERRAL_BUTTON_TEXT,
    WEBAPP_BUTTON_TEXT,
)


def get_main_menu_keyboard(user_id: int, token: str) -> ReplyKeyboardMarkup:
    """Get main menu reply keyboard."""
    webapp_url = f"{settings.WEBAPP_URL}?uid={user_id}&token={token}"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=WEBAPP_BUTTON_TEXT,
                    web_app=WebAppInfo(url=webapp_url),
                ),
            ],
            [
                KeyboardButton(text=BALANCE_BUTTON_TEXT),
                KeyboardButton(text=PROFILE_BUTTON_TEXT),
            ],
            [
                KeyboardButton(text=REFERRAL_BUTTON_TEXT),
                KeyboardButton(text=HELP_BUTTON_TEXT),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get cancel keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )
    return keyboard

