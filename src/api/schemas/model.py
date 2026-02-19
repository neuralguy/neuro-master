"""AI Model schemas."""

from pydantic import BaseModel
from src.shared.enums import GenerationType


class AIModelConfig(BaseModel):
    """Model configuration."""
    mode: str | None = None
    aspect_ratios: list[str] | None = None
    durations: list[int] | None = None
    supports_image_input: bool = False
    supports_audio: bool = False
    max_reference_images: int | None = None
    requires_source_image: bool = False
    requires_target_image: bool = False


class AIModelResponse(BaseModel):
    """AI Model response."""
    id: int
    code: str
    name: str
    description: str | None
    generation_type: GenerationType
    price_tokens: float
    price_per_second: float | None = None
    is_enabled: bool
    config: AIModelConfig | dict
    icon: str | None
    sort_order: int

    class Config:
        from_attributes = True


class AIModelsGroupedResponse(BaseModel):
    """Grouped AI models response."""
    image: list[AIModelResponse]
    video: list[AIModelResponse]
    faceswap: list[AIModelResponse]


class AIModelUpdateRequest(BaseModel):
    """Update AI model request."""
    name: str | None = None
    description: str | None = None
    price_tokens: float | None = None
    price_per_second: float | None = None
    is_enabled: bool | None = None
    config: dict | None = None
    icon: str | None = None
    sort_order: int | None = None


class AIModelCreateRequest(BaseModel):
    """Create AI model request."""
    code: str
    name: str
    provider_model: str
    generation_type: GenerationType
    price_tokens: float = 10.0
    description: str | None = None
    config: dict | None = None
    icon: str | None = None
