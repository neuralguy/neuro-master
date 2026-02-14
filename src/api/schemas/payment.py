"""Payment schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from src.shared.enums import PaymentStatus


class PaymentPackage(BaseModel):
    """Single payment package."""
    id: str
    name: str
    amount: int
    tokens: int


class PaymentPackagesResponse(BaseModel):
    """Available payment packages."""
    packages: list[PaymentPackage]
    currency: str


class PaymentCreateRequest(BaseModel):
    """Create payment request."""
    package_id: str = Field(..., description="ID пакета: standard, vip, premium, platinum")


class PaymentCreateResponse(BaseModel):
    """Create payment response."""
    payment_id: UUID
    amount: int
    tokens: int
    package_name: str
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

