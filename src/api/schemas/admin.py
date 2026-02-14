"""Admin schemas."""

from pydantic import BaseModel
from src.api.schemas.user import UserResponse
from src.api.schemas.payment import PaymentResponse


class AdminStatsResponse(BaseModel):
    """Admin dashboard statistics."""
    users: dict
    payments: dict
    generations: dict


class AdminUserResponse(UserResponse):
    """Admin user response with extra fields."""
    is_banned: bool
    total_generations: int = 0
    total_spent: int = 0


class AdminUserListResponse(BaseModel):
    """Admin user list response."""
    items: list[AdminUserResponse]
    total: int


class AdminUserUpdateRequest(BaseModel):
    """Admin user update request."""
    is_banned: bool | None = None
    balance: int | None = None


class AdminPaymentListResponse(BaseModel):
    """Admin payment list response."""
    items: list[PaymentResponse]
    total: int


class LogEntry(BaseModel):
    """Log entry for WebSocket."""
    timestamp: str
    level: str
    message: str
    module: str
    function: str
    line: int
    user_id: int | None
    request_id: str | None
    exception: str | None = None
