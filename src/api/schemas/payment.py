"""Payment schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from src.shared.enums import PaymentStatus


class PaymentCreateRequest(BaseModel):
    """Create payment request."""
    amount: int = Field(..., ge=50, le=50000)


class PaymentCreateResponse(BaseModel):
    """Create payment response."""
    payment_id: UUID
    amount: int
    tokens: int
    confirmation_url: str


class PaymentCheckResponse(BaseModel):
    """Payment check response."""
    payment_id: UUID
    status: PaymentStatus
    success: bool
    new_balance: int | None = None
    message: str


class PaymentResponse(BaseModel):
    """Payment response."""
    id: UUID
    amount: int
    tokens: int
    status: PaymentStatus
    created_at: datetime
    paid_at: datetime | None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """List of payments response."""
    items: list[PaymentResponse]
    total: int
