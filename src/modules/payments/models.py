"""Payment database models."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.shared.enums import BalanceOperationType, PaymentStatus


class Payment(Base):
    """Payment model."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # в рублях
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)  # токены = amount
    
    yookassa_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    yookassa_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confirmation_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"


class BalanceHistory(Base):
    """Balance history model for tracking all balance changes."""

    __tablename__ = "balance_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # + или -
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    
    operation_type: Mapped[BalanceOperationType] = mapped_column(
        Enum(BalanceOperationType), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    reference_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # payment_id, generation_id, etc.
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="balance_history")

    def __repr__(self) -> str:
        return f"<BalanceHistory(user_id={self.user_id}, amount={self.amount}, type={self.operation_type})>"


# Import to avoid circular imports
from src.modules.user.models import User
