"""Reply keyboards for bot."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from src.config import settings
from src.shared.constants import (
    CREATE_IMAGE_BUTTON_TEXT,
    CREATE_VIDEO_BUTTON_TEXT,
    TRENDING_PROMPTS_BUTTON_TEXT,
    EARN_TOKENS_BUTTON_TEXT,
    HELP_BUTTON_TEXT,
)


def get_main_menu_keyboard(user_id: int, token: str) -> ReplyKeyboardMarkup:
    """Get main menu reply keyboard."""
    base_url = f"{settings.WEBAPP_URL}?uid={user_id}&token={token}"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=CREATE_IMAGE_BUTTON_TEXT,
                    web_app=WebAppInfo(url=f"{base_url}&tab=image"),
                ),
                KeyboardButton(
                    text=CREATE_VIDEO_BUTTON_TEXT,
                    web_app=WebAppInfo(url=f"{base_url}&tab=video"),
                ),
            ],
            [
                KeyboardButton(text=TRENDING_PROMPTS_BUTTON_TEXT),
                KeyboardButton(
                    text=EARN_TOKENS_BUTTON_TEXT,
                    web_app=WebAppInfo(url=f"{base_url}&page=profile"),
                ),
            ],
            [
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

