"""Generation schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from src.shared.enums import GenerationStatus, GenerationType


class GenerationCreateRequest(BaseModel):
    """Create generation request."""
    model_code: str
    prompt: str | None = None
    image_url: str | None = None
    video_url: str | None = None  # NEW: для motion control
    aspect_ratio: str = "1:1"
    duration: int | None = None
    extra_params: dict | None = None


class GenerationResponse(BaseModel):
    """Generation response."""
    id: UUID
    generation_type: GenerationType
    status: GenerationStatus
    prompt: str | None
    tokens_spent: int
    result_url: str | None
    result_file_url: str | None = None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    model_code: str | None = None
    model_name: str | None = None

    class Config:
        from_attributes = True


class GenerationListResponse(BaseModel):
    """List of generations response."""
    items: list[GenerationResponse]
    total: int


class GenerationStatusResponse(BaseModel):
    """Generation status response."""
    id: UUID
    status: GenerationStatus
    result_url: str | None = None
    result_file_url: str | None = None
    error_message: str | None = None
    progress: int | None = None

