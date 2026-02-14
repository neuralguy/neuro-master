"""Admin filter for bot handlers."""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from src.config import settings


class AdminFilter(BaseFilter):
    """Filter to check if user is admin."""
    
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else None
        
        if not user_id:
            return False
        
        return user_id in settings.admin_ids_list
