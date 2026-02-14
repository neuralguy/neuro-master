"""Logging middleware for bot events."""

from typing import Any, Awaitable, Callable, Dict
from time import perf_counter

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from src.shared.logger import logger, new_request_id, set_context


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging all bot events."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Generate request ID
        request_id = new_request_id()
        set_context(request_id=request_id)
        
        # Get event info
        event_type = type(event).__name__
        user_id = None
        event_data = ""
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if event.text:
                event_data = f"text={event.text[:50]}"
            elif event.photo:
                event_data = "photo"
            elif event.document:
                event_data = f"document={event.document.file_name}"
            else:
                event_data = "other"
                
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            event_data = f"data={event.data}"
        
        if user_id:
            set_context(user_id=user_id)
        
        logger.debug(f"→ {event_type} | {event_data}")
        
        start_time = perf_counter()
        
        try:
            result = await handler(event, data)
            elapsed = perf_counter() - start_time
            logger.debug(f"← {event_type} | OK | {elapsed:.3f}s")
            return result
            
        except Exception as e:
            elapsed = perf_counter() - start_time
            logger.error(f"✗ {event_type} | FAILED | {elapsed:.3f}s | {type(e).__name__}: {e}")
            raise
