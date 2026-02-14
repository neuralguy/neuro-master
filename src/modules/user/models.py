from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.modules.generation.models import Generation
    from src.modules.payments.models import BalanceHistory, Payment
    from src.modules.referral.models import Referral


class User(Base):
    """User model."""

    __tablename__ = "users"

    # Integer для совместимости с SQLite autoincrement
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    generations: Mapped[list["Generation"]] = relationship(
        "Generation", back_populates="user", lazy="selectin"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="user", lazy="selectin"
    )
    balance_history: Mapped[list["BalanceHistory"]] = relationship(
        "BalanceHistory", back_populates="user", lazy="selectin"
    )
    
    # Referral relationships
    referrals_made: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.referrer_id",
        back_populates="referrer",
        lazy="selectin",
    )
    referred_by: Mapped["Referral | None"] = relationship(
        "Referral",
        foreign_keys="Referral.referred_id",
        back_populates="referred",
        uselist=False,
        lazy="selectin",
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def display_name(self) -> str:
        """Get display name (username or full name)."""
        if self.username:
            return f"@{self.username}"
        return self.full_name

    @property
    def referral_code(self) -> str:
        """Get referral code (base36 of user id)."""
        import base64
        return base64.b64encode(str(self.id).encode()).decode()[:8]

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} username={self.username}>"

