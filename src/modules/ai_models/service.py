"""AI Models service."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.ai_models.models import AIModel
from src.modules.ai_models.repository import AIModelRepository
from src.shared.enums import GenerationType
from src.shared.logger import logger


class AIModelService:
    """Service for AI model management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AIModelRepository(session)

    async def get_model(self, model_id: int) -> AIModel:
        """Get model by ID."""
        model = await self.repo.get_by_id(model_id)
        if not model:
            raise NotFoundError("Модель", model_id)
        return model

    async def get_model_by_code(self, code: str) -> AIModel:
        """Get model by code."""
        model = await self.repo.get_by_code(code)
        if not model:
            raise NotFoundError("Модель", code)
        return model

    async def get_available_models(
        self,
        generation_type: GenerationType | None = None,
    ) -> list[AIModel]:
        """Get all enabled models for users."""
        return await self.repo.get_all(
            enabled_only=True,
            generation_type=generation_type,
        )

    async def get_all_models(
        self,
        generation_type: GenerationType | None = None,
    ) -> list[AIModel]:
        """Get all models for admin."""
        return await self.repo.get_all(
            enabled_only=False,
            generation_type=generation_type,
        )

    async def create_model(
        self,
        code: str,
        name: str,
        provider_model: str,
        generation_type: GenerationType,
        price_tokens: int = 10,
        description: str | None = None,
        config: dict | None = None,
        icon: str | None = None,
    ) -> AIModel:
        """Create new AI model."""
        # Check if code already exists
        existing = await self.repo.get_by_code(code)
        if existing:
            raise ValidationError(f"Модель с кодом {code} уже существует")
        
        return await self.repo.create(
            code=code,
            name=name,
            provider_model=provider_model,
            generation_type=generation_type,
            price_tokens=price_tokens,
            description=description,
            config=config,
            icon=icon,
        )

    async def update_model(
        self,
        model_id: int,
        **kwargs,
    ) -> AIModel:
        """Update model."""
        model = await self.get_model(model_id)
        return await self.repo.update(model, **kwargs)

    async def toggle_model(self, model_id: int) -> bool:
        """Toggle model enabled status. Returns new status."""
        model = await self.get_model(model_id)
        new_status = not model.is_enabled
        await self.repo.set_enabled(model_id, new_status)
        return new_status

    async def set_price(self, model_id: int, price_tokens: int) -> None:
        """Set model price."""
        if price_tokens < 1:
            raise ValidationError("Цена должна быть минимум 1 токен")
        
        await self.get_model(model_id)  # Check exists
        await self.repo.update_price(model_id, price_tokens)

    async def delete_model(self, model_id: int) -> None:
        """Delete model."""
        await self.get_model(model_id)  # Check exists
        await self.repo.delete(model_id)

    async def get_models_grouped(self) -> dict[str, list[AIModel]]:
        """Get models grouped by type for frontend."""
        models = await self.get_available_models()
        
        grouped = {
            "image": [],
            "video": [],
            "faceswap": [],
        }
        
        for model in models:
            grouped[model.generation_type.value].append(model)
        
        return grouped


# === Default models to seed ===
DEFAULT_MODELS = [
    # === TEXT-TO-IMAGE ===
    {
        "code": "nano-banana",
        "name": "Nano Banana",
        "description": "Google Gemini 2.5 Flash — быстрая генерация",
        "provider": "poyo.ai",
        "provider_model": "google/nano-banana",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "nano-banana-pro",
        "name": "Nano Banana Pro",
        "description": "Google Gemini 3 Pro — высокое качество 2K/4K",
        "provider": "poyo.ai",
        "provider_model": "nano-banana-pro",
        "generation_type": "image",
        "price_tokens": 18,
        
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "gpt-image-1.5",
        "name": "GPT Image 1.5",
        "description": "OpenAI GPT Image 1.5",
        "provider": "poyo.ai",
        "provider_model": "gpt-image/1.5-text-to-image",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🎨",
        "config": {"aspect_ratios": ["1:1", "3:2", "2:3"], "quality": "medium", "mode": "text-to-image"},
    },
    {
        "code": "imagen4-fast",
        "name": "Google Imagen 4",
        "description": "Google Imagen 4 — быстрая генерация",
        "provider": "poyo.ai",
        "provider_model": "google/imagen4-fast",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🖼️",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "flux-2-pro",
        "name": "Flux 2 Pro",
        "description": "Black Forest Labs Flux 2 Pro",
        "provider": "poyo.ai",
        "provider_model": "flux-2/pro-text-to-image",
        "generation_type": "image",
        "price_tokens": 5,
        
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "resolution": "1K", "mode": "text-to-image"},
    },
    {
        "code": "flux-2-flex",
        "name": "Flux 2 Flex",
        "description": "Flux 2 Flex — генерация 1K",
        "provider": "poyo.ai",
        "provider_model": "flux-2/flex-text-to-image",
        "generation_type": "image",
        "price_tokens": 14,
        
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "resolution": "1K", "mode": "text-to-image"},
    },
    {
        "code": "grok-imagine",
        "name": "Grok Imagine",
        "description": "xAI Grok — генерация изображений",
        "provider": "poyo.ai",
        "provider_model": "grok-imagine/text-to-image",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🚀",
        "config": {"aspect_ratios": ["1:1", "3:2", "2:3", "16:9", "9:16"], "mode": "text-to-image"},
    },
    {
        "code": "qwen-image",
        "name": "Qwen Image",
        "description": "Alibaba Qwen — генерация изображений",
        "provider": "poyo.ai",
        "provider_model": "qwen/text-to-image",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🌐",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "text-to-image"},
    },
    # === IMAGE-TO-IMAGE ===
    {
        "code": "nano-banana-edit",
        "name": "Nano Banana",
        "description": "Google — редактирование изображений",
        "provider": "poyo.ai",
        "provider_model": "google/nano-banana-edit",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "gpt-image-1.5-edit",
        "name": "GPT Image 1.5",
        "description": "OpenAI GPT Image 1.5 — редактирование",
        "provider": "poyo.ai",
        "provider_model": "gpt-image/1.5-image-to-image",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🎨",
        "config": {"aspect_ratios": ["1:1", "3:2", "2:3"], "quality": "medium", "mode": "image-to-image"},
    },
    {
        "code": "flux-2-pro-edit",
        "name": "Flux 2 Pro",
        "description": "Flux 2 Pro — редактирование",
        "provider": "poyo.ai",
        "provider_model": "flux-2/pro-image-to-image",
        "generation_type": "image",
        "price_tokens": 5,
        
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "resolution": "1K", "mode": "image-to-image"},
    },
    {
        "code": "grok-imagine-edit",
        "name": "Grok Imagine",
        "description": "xAI Grok — редактирование изображений",
        "provider": "poyo.ai",
        "provider_model": "grok-imagine/image-to-image",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🚀",
        "config": {"aspect_ratios": ["1:1", "3:2", "2:3", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "qwen-image-edit",
        "name": "Qwen Image",
        "description": "Alibaba Qwen — редактирование изображений",
        "provider": "poyo.ai",
        "provider_model": "qwen/image-to-image",
        "generation_type": "image",
        "price_tokens": 4,
        
        "icon": "🌐",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    # ============ VIDEO MODELS - Text to Video ============
    {
        "code": "veo3-fast",
        "name": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 fast video generation with audio",
        "provider": "poyo.ai",
        "provider_model": "veo3_fast",
        "generation_type": "video",
        "price_tokens": 50,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "text-to-video"},
    },
    {
        "code": "veo3-quality",
        "name": "Veo 3.1 Quality",
        "description": "Google Veo 3.1 high-quality video generation",
        "provider": "poyo.ai",
        "provider_model": "veo3",
        "generation_type": "video",
        "price_tokens": 100,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "text-to-video"},
    },
    {
        "code": "sora-2-pro",
        "name": "Sora 2 Pro",
        "description": "OpenAI Sora 2 Pro video generation",
        "provider": "kie.ai",
        "provider_model": "sora-2-pro-text-to-video",
        "generation_type": "video",
        "price_tokens": 80,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "mode": "text-to-video"},
    },
    {
        "code": "kling-2.6",
        "name": "Kling 2.6",
        "description": "Kling 2.6 high-quality video generation",
        "provider": "kie.ai",
        "provider_model": "kling-2.6/text-to-video",
        "generation_type": "video",
        "price_tokens": 40,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": ["5", "10"], "mode": "text-to-video"},
    },
    {
        "code": "kling-turbo",
        "name": "Kling 2.5 Turbo",
        "description": "Kling 2.5 Turbo fast video generation",
        "provider": "kie.ai",
        "provider_model": "kling/v2-5-turbo-text-to-video-pro",
        "generation_type": "video",
        "price_tokens": 30,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": ["5", "10"], "mode": "text-to-video"},
    },
    {
        "code": "hailuo-pro",
        "name": "Hailuo Pro",
        "description": "Hailuo Pro high-quality video generation",
        "provider": "kie.ai",
        "provider_model": "hailuo/02-text-to-video-pro",
        "generation_type": "video",
        "price_tokens": 35,
        "icon": "🌊",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "text-to-video"},
    },
    {
        "code": "wan-2.6",
        "name": "Wan 2.6",
        "description": "Wan 2.6 video generation",
        "provider": "kie.ai",
        "provider_model": "wan/2-6-text-to-video",
        "generation_type": "video",
        "price_tokens": 25,
        "icon": "🎭",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": ["5", "10"], "mode": "text-to-video"},
    },
    {
        "code": "runway-gen4",
        "name": "Runway Gen-4",
        "description": "Runway Gen-4 Turbo video generation",
        "provider": "kie.ai",
        "provider_model": "runway",
        "generation_type": "video",
        "price_tokens": 45,
        "icon": "🛫",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"], "durations": ["5", "10"], "mode": "text-to-video"},
    },
    
    # ============ VIDEO MODELS - Image to Video ============
    {
        "code": "veo3-fast-i2v",
        "name": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 image to video",
        "provider": "poyo.ai",
        "provider_model": "veo3_fast",
        "generation_type": "video",
        "price_tokens": 50,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "image-to-video"},
    },
    {
        "code": "sora-2-i2v",
        "name": "Sora 2",
        "description": "OpenAI Sora 2 image to video",
        "provider": "kie.ai",
        "provider_model": "sora-2-image-to-video",
        "generation_type": "video",
        "price_tokens": 60,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "mode": "image-to-video"},
    },
    {
        "code": "kling-turbo-i2v",
        "name": "Kling 2.5 Turbo",
        "description": "Kling 2.5 Turbo image to video",
        "provider": "kie.ai",
        "provider_model": "kling/v2-5-turbo-image-to-video-pro",
        "generation_type": "video",
        "price_tokens": 30,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": ["5", "10"], "mode": "image-to-video"},
    },
    {
        "code": "wan-2.6-i2v",
        "name": "Wan 2.6",
        "description": "Wan 2.6 image to video",
        "provider": "kie.ai",
        "provider_model": "wan/2-6-image-to-video",
        "generation_type": "video",
        "price_tokens": 25,
        "icon": "🎭",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": ["5", "10"], "mode": "image-to-video"},
    },
    {
        "code": "hailuo-i2v",
        "name": "Hailuo",
        "description": "Hailuo image to video",
        "provider": "kie.ai",
        "provider_model": "hailuo/2-3-image-to-video-pro",
        "generation_type": "video",
        "price_tokens": 35,
        "icon": "🌊",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "image-to-video"},
    },
    {
        "code": "grok-imagine-i2v",
        "name": "Grok Imagine",
        "description": "xAI Grok image to video",
        "provider": "kie.ai",
        "provider_model": "grok-imagine/image-to-video",
        "generation_type": "video",
        "price_tokens": 30,
        "icon": "🚀",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "image-to-video"},
    },
    {
        "code": "runway-gen4-i2v",
        "name": "Runway Gen-4",
        "description": "Runway Gen-4 image to video",
        "provider": "kie.ai",
        "provider_model": "runway",
        "generation_type": "video",
        "price_tokens": 45,
        "icon": "🛫",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"], "durations": ["5", "10"], "mode": "image-to-video"},
    },
]




async def seed_default_models(session: AsyncSession) -> None:
    """Seed default AI models to database."""
    repo = AIModelRepository(session)
    
    for i, model_data in enumerate(DEFAULT_MODELS):
        existing = await repo.get_by_code(model_data["code"])
        if not existing:
            await repo.create(
                **model_data,
                sort_order=i,
            )
            logger.info(f"Seeded model | code={model_data['code']}")
    
    await session.commit()
