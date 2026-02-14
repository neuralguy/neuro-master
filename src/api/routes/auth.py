"""Authentication routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import CurrentUser, SessionDep
from src.api.schemas.user import UserResponse
from src.core.security import validate_telegram_webapp_data, validate_webapp_token
from src.modules.user.service import UserService
from src.shared.logger import logger

router = APIRouter()


class TokenAuthRequest(BaseModel):
    telegram_id: int
    token: str


@router.post("/telegram", response_model=UserResponse)
async def authenticate_telegram(
    session: SessionDep,
    init_data: str,
) -> UserResponse:
    """Authenticate user with Telegram WebApp init data."""
    try:
        data = validate_telegram_webapp_data(init_data)
        telegram_user = data["user"]
        
        user_service = UserService(session)
        user, is_new = await user_service.get_or_create_user(
            telegram_id=telegram_user["id"],
            first_name=telegram_user.get("first_name", "User"),
            last_name=telegram_user.get("last_name"),
            username=telegram_user.get("username"),
        )
        
        if user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is banned",
            )
        
        logger.info(f"User authenticated | telegram_id={user.telegram_id}, is_new={is_new}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/token", response_model=UserResponse)
async def authenticate_token(
    request: TokenAuthRequest,
    session: SessionDep,
) -> UserResponse:
    """Authenticate user with token (for reply keyboard mini app)."""
    if not validate_webapp_token(request.telegram_id, request.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    user_service = UserService(session)
    try:
        user = await user_service.get_user_by_telegram_id(request.telegram_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        )
    
    logger.info(f"Token auth | telegram_id={request.telegram_id}")
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current authenticated user."""
    return current_user

