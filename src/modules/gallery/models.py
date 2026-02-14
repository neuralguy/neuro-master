"""Gallery database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class GalleryItem(Base):
    """Gallery item model."""

    __tablename__ = "gallery_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # image, video
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    generation: Mapped["Generation"] = relationship(
        "Generation", back_populates="gallery_item"
    )

    def __repr__(self) -> str:
        return f"<GalleryItem(id={self.id}, user_id={self.user_id}, type={self.file_type})>"


# Import to avoid circular imports
from src.modules.generation.models import Generation
