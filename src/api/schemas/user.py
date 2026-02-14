"""User schemas."""

from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    """User response."""
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    balance: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserBalanceResponse(BaseModel):
    """User balance response."""
    balance: int


class BalanceHistoryItem(BaseModel):
    """Balance history item."""
    id: int
    amount: int
    balance_after: int
    operation_type: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class BalanceHistoryResponse(BaseModel):
    """Balance history response."""
    items: list[BalanceHistoryItem]
    total: int


class ReferralStatsResponse(BaseModel):
    """Referral statistics response."""
    referral_code: str
    referral_link: str
    total_referrals: int
    total_bonus_earned: int


class ReferralItem(BaseModel):
    """Referral item."""
    id: int
    name: str
    date: str
    bonus: int


class ReferralInfoResponse(ReferralStatsResponse):
    """Full referral info response."""
    recent_referrals: list[ReferralItem]
