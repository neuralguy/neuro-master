"""Generation database models."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.shared.enums import GenerationStatus, GenerationType


class Generation(Base):
    """Generation task model."""

    __tablename__ = "generations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Relations
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True
    )
    
    # Type and status
    generation_type: Mapped[GenerationType] = mapped_column(
        Enum(GenerationType), nullable=False, index=True
    )
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus), default=GenerationStatus.PENDING, nullable=False, index=True
    )
    
    # Input
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    input_file_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # For external URLs
    
    # Output
    result_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # Temporary kie.ai URL
    
    # Provider data
    kie_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Cost
    tokens_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Additional params
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # params can include: aspect_ratio, duration, etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="generations")
    model: Mapped["AIModel"] = relationship("AIModel", lazy="joined")
    gallery_item: Mapped["GalleryItem"] = relationship(
        "GalleryItem", back_populates="generation", uselist=False
    )

    @property
    def is_completed(self) -> bool:
        """Check if generation is completed (success or fail)."""
        return self.status in (GenerationStatus.SUCCESS, GenerationStatus.FAILED)

    @property
    def is_pending(self) -> bool:
        """Check if generation is still in progress."""
        return self.status in (GenerationStatus.PENDING, GenerationStatus.PROCESSING)

    def __repr__(self) -> str:
        return f"<Generation(id={self.id}, type={self.generation_type}, status={self.status})>"


# Import to avoid circular imports
from src.modules.ai_models.models import AIModel
from src.modules.gallery.models import GalleryItem
from src.modules.user.models import User
