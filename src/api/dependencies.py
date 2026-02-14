"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_maker
from src.core.security import validate_telegram_webapp_data, validate_webapp_token
from src.modules.user.models import User
from src.modules.user.service import UserService
from src.shared.logger import logger, set_context


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    x_telegram_init_data: Annotated[str | None, Header()] = None,
    x_telegram_id: Annotated[str | None, Header()] = None,
    x_telegram_token: Annotated[str | None, Header()] = None,
) -> User:
    """
    Get current user. Supports two auth methods:
    1. Telegram WebApp initData (inline button, menu button)
    2. Token auth (reply keyboard button)
    """
    
    # Method 1: initData
    if x_telegram_init_data:
        try:
            data = validate_telegram_webapp_data(x_telegram_init_data)
            telegram_user = data["user"]
            telegram_id = telegram_user["id"]
            set_context(user_id=telegram_id)
            
            user_service = UserService(session)
            user, is_new = await user_service.get_or_create_user(
                telegram_id=telegram_id,
                first_name=telegram_user.get("first_name", "User"),
                last_name=telegram_user.get("last_name"),
                username=telegram_user.get("username"),
            )
            
            if user.is_banned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is banned",
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"InitData auth failed | error={e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid init data: {e}",
            )
    
    # Method 2: Token
    if x_telegram_id and x_telegram_token:
        try:
            telegram_id = int(x_telegram_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid telegram_id",
            )
        
        if not validate_webapp_token(telegram_id, x_telegram_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        
        set_context(user_id=telegram_id)
        
        user_service = UserService(session)
        user = await user_service.user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is banned",
            )
        
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing auth data",
    )


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_admin_user(
    current_user: CurrentUser,
) -> User:
    """Get current user and verify admin status."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


AdminUser = Annotated[User, Depends(get_admin_user)]

