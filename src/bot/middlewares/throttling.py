"""Throttling middleware to prevent spam."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from src.core.redis import get_redis
from src.shared.logger import logger


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware for rate limiting."""
    
    def __init__(
        self,
        rate_limit: float = 0.5,  # seconds between messages
        key_prefix: str = "throttle",
    ):
        self.rate_limit = rate_limit
        self.key_prefix = key_prefix
        # Конвертируем в миллисекунды, минимум 100мс
        self.rate_limit_ms = max(int(rate_limit * 1000), 100)
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user ID
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if not user_id:
            return await handler(event, data)
        
        # Check throttle
        redis = await get_redis()
        if not redis:
            return await handler(event, data)
            
        key = f"{self.key_prefix}:{user_id}"
        
        try:
            # Используем px (миллисекунды) вместо ex (секунды)
            is_new = await redis.set(
                key,
                "1",
                px=self.rate_limit_ms,
                nx=True,
            )
            
            if not is_new:
                # User is throttled
                event_type = type(event).__name__
                logger.debug(f"Request throttled | user_id={user_id}, event_type={event_type}")
                
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ Слишком быстро! Подождите немного.")
                
                return
                
        except Exception as e:
            logger.warning(f"Throttling error | error={e}")
            # При ошибке Redis — пропускаем запрос
        
        return await handler(event, data)

