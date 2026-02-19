"""Payment schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from src.shared.enums import PaymentStatus


class PaymentPackageItem(BaseModel):
    id: str
    name: str
    amount: int
    tokens: int


class PaymentPackagesResponse(BaseModel):
    packages: list[PaymentPackageItem]
    currency: str


class PaymentCreateRequest(BaseModel):
    package_id: str = Field(..., description="ID пакета: standard, vip, premium, platinum")
    currency: str = Field(default="USD", description="Валюта оплаты: USD или RUB")


class PaymentCreateResponse(BaseModel):
    payment_id: UUID
    amount: int
    tokens: int
    package_name: str
    confirmation_url: str


class PaymentCheckResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    success: bool
    new_balance: int | None = None
    message: str


class PaymentResponse(BaseModel):
    id: UUID
    amount: int
    tokens: int
    status: PaymentStatus
    created_at: datetime
    paid_at: datetime | None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int

