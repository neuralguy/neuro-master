"""User routes."""

from fastapi import APIRouter

from src.api.dependencies import CurrentUser, SessionDep
from src.api.schemas.user import (
    BalanceHistoryItem,
    BalanceHistoryResponse,
    ReferralInfoResponse,
    UserBalanceResponse,
    UserResponse,
)
from src.bot.loader import bot
from src.modules.user.service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Get current user profile."""
    return current_user


@router.get("/balance", response_model=UserBalanceResponse)
async def get_balance(current_user: CurrentUser) -> UserBalanceResponse:
    """Get current user balance."""
    return UserBalanceResponse(balance=current_user.balance)


@router.get("/history", response_model=BalanceHistoryResponse)
async def get_balance_history(
    current_user: CurrentUser,
    session: SessionDep,
    offset: int = 0,
    limit: int = 50,
) -> BalanceHistoryResponse:
    """Get user balance history."""
    user_service = UserService(session)
    
    history = await user_service.get_balance_history(
        current_user.id, offset, limit
    )
    
    from src.modules.payments.repository import BalanceHistoryRepository
    repo = BalanceHistoryRepository(session)
    total = await repo.count_user_history(current_user.id)
    
    return BalanceHistoryResponse(
        items=[BalanceHistoryItem.model_validate(h) for h in history],
        total=total,
    )


@router.get("/referral", response_model=ReferralInfoResponse)
async def get_referral_info(
    current_user: CurrentUser,
    session: SessionDep,
) -> ReferralInfoResponse:
    """Get user referral information."""
    user_service = UserService(session)
    
    bot_info = await bot.get_me()
    info = await user_service.get_referral_info(current_user)
    info["referral_link"] = f"https://t.me/{bot_info.username}?start={current_user.referral_code}"
    
    return ReferralInfoResponse(**info)
