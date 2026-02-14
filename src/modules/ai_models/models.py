"""AI Models database models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.shared.enums import GenerationType


class AIModel(Base):
    """AI Model configuration."""

    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identification
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Provider info
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="kie.ai")
    provider_model: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "google/nano-banana-pro"
    
    # Type
    generation_type: Mapped[GenerationType] = mapped_column(
        Enum(GenerationType), nullable=False, index=True
    )
    
    # Pricing
    price_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Configuration
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # Config can include: aspect_ratios, max_duration, supports_image_input, etc.
    
    # Display
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)  # emoji
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AIModel(code={self.code}, type={self.generation_type}, enabled={self.is_enabled})>"
