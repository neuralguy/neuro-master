"""Authentication middleware for user registration/retrieval."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import UserBannedError
from src.modules.user.service import UserService
from src.shared.logger import logger, set_context


class AuthMiddleware(BaseMiddleware):
    """Middleware that handles user authentication and registration."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user from event
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        if not user:
            return await handler(event, data)
        
        # Set logging context
        set_context(user_id=user.id)
        
        # Get session from data (should be set by DatabaseMiddleware)
        session: AsyncSession = data.get("session")
        if not session:
            logger.error("Session not found in middleware data")
            return await handler(event, data)
        
        # Get or create user
        user_service = UserService(session)
        
        # Extract referral code from /start command
        referral_code = None
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            parts = event.text.split()
            if len(parts) > 1:
                referral_code = parts[1]
        
        try:
            db_user, is_new = await user_service.get_or_create_user(
                telegram_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                referral_code=referral_code,
            )
            
            if is_new:
                logger.info(f"New user registered | user_id={user.id}, username={user.username}, referral_code={referral_code}")
            
            # Check if user is banned
            if db_user.is_banned:
                logger.warning(f"Banned user attempt | user_id={user.id}, username={user.username}")
                if isinstance(event, Message):
                    await event.answer(
                        "❌ Ваш аккаунт заблокирован. "
                        "Если вы считаете это ошибкой, обратитесь в поддержку."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "❌ Ваш аккаунт заблокирован",
                        show_alert=True,
                    )
                return
            
            # Add user to data
            data["db_user"] = db_user
            data["is_new_user"] = is_new
            data["user_service"] = user_service
            
        except Exception as e:
            logger.exception(f"Auth middleware error | error={e}")
            raise
        
        return await handler(event, data)
