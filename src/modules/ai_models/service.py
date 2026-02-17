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

        await self.get_model(model_id)
        await self.repo.update_price(model_id, price_tokens)

    async def delete_model(self, model_id: int) -> None:
        """Delete model."""
        await self.get_model(model_id)
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
#
# RULES:
#   - ALL image models → provider: poyo.ai
#   - Video: veo3 models → provider: poyo.ai
#   - Video: everything else (kling, sora, hailuo, wan, runway, grok-imagine) → provider: kie.ai
#
# poyo.ai provider_model = the model name as listed in poyo.ai docs
# kie.ai provider_model = the model string for kie.ai API
#

DEFAULT_MODELS = [
    # =============================================
    # IMAGE: TEXT-TO-IMAGE (all poyo.ai)
    # =============================================
    {
        "code": "nano-banana",
        "name": "Nano Banana",
        "description": "Google Gemini — быстрая генерация",
        "provider": "poyo.ai",
        "provider_model": "nano-banana",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "nano-banana-2",
        "name": "Nano Banana 2",
        "description": "Google Gemini — улучшенное качество",
        "provider": "poyo.ai",
        "provider_model": "nano-banana-2",
        "generation_type": "image",
        "price_tokens": 6,
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "gpt-image-1.5",
        "name": "GPT Image 1.5",
        "description": "OpenAI GPT Image 1.5",
        "provider": "poyo.ai",
        "provider_model": "gpt-image-1.5",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "🎨",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "gpt-4o-image",
        "name": "GPT-4o Image",
        "description": "OpenAI GPT-4o Image — премиум качество",
        "provider": "poyo.ai",
        "provider_model": "gpt-4o-image",
        "generation_type": "image",
        "price_tokens": 8,
        "icon": "🎨",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "seedream-4.5",
        "name": "Seedream 4.5",
        "description": "Seedream 4.5 — высокое качество",
        "provider": "poyo.ai",
        "provider_model": "seedream-4.5",
        "generation_type": "image",
        "price_tokens": 5,
        "icon": "🌱",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "flux-2-pro",
        "name": "Flux 2 Pro",
        "description": "Black Forest Labs Flux 2 Pro",
        "provider": "poyo.ai",
        "provider_model": "flux-2-pro",
        "generation_type": "image",
        "price_tokens": 6,
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "text-to-image"},
    },
    {
        "code": "flux-2-flex",
        "name": "Flux 2 Flex",
        "description": "Flux 2 Flex — высокое разрешение",
        "provider": "poyo.ai",
        "provider_model": "flux-2-flex",
        "generation_type": "image",
        "price_tokens": 14,
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "text-to-image"},
    },
    {
        "code": "grok-imagine",
        "name": "Grok Imagine",
        "description": "xAI Grok — генерация изображений",
        "provider": "poyo.ai",
        "provider_model": "grok-imagine-image",
        "generation_type": "image",
        "price_tokens": 6,
        "icon": "🚀",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "z-image",
        "name": "Z Image",
        "description": "Z Image — быстрая генерация",
        "provider": "poyo.ai",
        "provider_model": "z-image",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },

    # =============================================
    # IMAGE: IMAGE-TO-IMAGE / EDIT (all poyo.ai)
    # =============================================
    {
        "code": "nano-banana-edit",
        "name": "Nano Banana",
        "description": "Google — редактирование изображений",
        "provider": "poyo.ai",
        "provider_model": "nano-banana-edit",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "nano-banana-2-edit",
        "name": "Nano Banana 2",
        "description": "Google — улучшенное редактирование",
        "provider": "poyo.ai",
        "provider_model": "nano-banana-2-edit",
        "generation_type": "image",
        "price_tokens": 6,
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "gpt-image-1.5-edit",
        "name": "GPT Image 1.5",
        "description": "OpenAI GPT Image 1.5 — редактирование",
        "provider": "poyo.ai",
        "provider_model": "gpt-image-1.5-edit",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "🎨",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "gpt-4o-image-edit",
        "name": "GPT-4o Image",
        "description": "OpenAI GPT-4o Image — редактирование",
        "provider": "poyo.ai",
        "provider_model": "gpt-4o-image-edit",
        "generation_type": "image",
        "price_tokens": 8,
        "icon": "🎨",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "seedream-4.5-edit",
        "name": "Seedream 4.5",
        "description": "Seedream 4.5 — редактирование",
        "provider": "poyo.ai",
        "provider_model": "seedream-4.5-edit",
        "generation_type": "image",
        "price_tokens": 5,
        "icon": "🌱",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "flux-2-pro-edit",
        "name": "Flux 2 Pro",
        "description": "Flux 2 Pro — редактирование",
        "provider": "poyo.ai",
        "provider_model": "flux-2-pro-edit",
        "generation_type": "image",
        "price_tokens": 6,
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "flux-2-flex-edit",
        "name": "Flux 2 Flex",
        "description": "Flux 2 Flex — редактирование",
        "provider": "poyo.ai",
        "provider_model": "flux-2-flex-edit",
        "generation_type": "image",
        "price_tokens": 14,
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },

    # =============================================
    # VIDEO: TEXT-TO-VIDEO
    # =============================================

    # veo3 → poyo.ai
    {
        "code": "veo3-fast",
        "name": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 — быстрая генерация видео со звуком",
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
        "description": "Google Veo 3.1 — высокое качество видео",
        "provider": "poyo.ai",
        "provider_model": "veo3",
        "generation_type": "video",
        "price_tokens": 100,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "text-to-video"},
    },

    # sora → kie.ai
    {
        "code": "sora-2-pro",
        "name": "Sora 2 Pro",
        "description": "OpenAI Sora 2 Pro — генерация видео",
        "provider": "kie.ai",
        "provider_model": "sora-2-pro-text-to-video",
        "generation_type": "video",
        "price_tokens": 80,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "mode": "text-to-video"},
    },

    # kling → kie.ai
    {
        "code": "kling-2.6",
        "name": "Kling 2.6",
        "description": "Kling 2.6 — высокое качество видео",
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
        "description": "Kling 2.5 Turbo — быстрое видео",
        "provider": "kie.ai",
        "provider_model": "kling/v2-5-turbo-text-to-video-pro",
        "generation_type": "video",
        "price_tokens": 30,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": ["5", "10"], "mode": "text-to-video"},
    },

    # hailuo → kie.ai
    {
        "code": "hailuo-pro",
        "name": "Hailuo Pro",
        "description": "Hailuo Pro — высокое качество видео",
        "provider": "kie.ai",
        "provider_model": "hailuo/02-text-to-video-pro",
        "generation_type": "video",
        "price_tokens": 35,
        "icon": "🌊",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "text-to-video"},
    },

    # wan → kie.ai
    {
        "code": "wan-2.6",
        "name": "Wan 2.6",
        "description": "Wan 2.6 — генерация видео",
        "provider": "kie.ai",
        "provider_model": "wan/2-6-text-to-video",
        "generation_type": "video",
        "price_tokens": 25,
        "icon": "🎭",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": ["5", "10"], "mode": "text-to-video"},
    },

    # runway → kie.ai
    {
        "code": "runway-gen4",
        "name": "Runway Gen-4",
        "description": "Runway Gen-4 Turbo — генерация видео",
        "provider": "kie.ai",
        "provider_model": "runway",
        "generation_type": "video",
        "price_tokens": 45,
        "icon": "🛫",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"], "durations": ["5", "10"], "mode": "text-to-video"},
    },

    # =============================================
    # VIDEO: IMAGE-TO-VIDEO
    # =============================================

    # veo3 i2v → poyo.ai
    {
        "code": "veo3-fast-i2v",
        "name": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 — видео из изображения",
        "provider": "poyo.ai",
        "provider_model": "veo3_fast",
        "generation_type": "video",
        "price_tokens": 50,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "image-to-video"},
    },

    # sora i2v → kie.ai
    {
        "code": "sora-2-i2v",
        "name": "Sora 2",
        "description": "OpenAI Sora 2 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "sora-2-image-to-video",
        "generation_type": "video",
        "price_tokens": 60,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "mode": "image-to-video"},
    },

    # kling i2v → kie.ai
    {
        "code": "kling-turbo-i2v",
        "name": "Kling 2.5 Turbo",
        "description": "Kling 2.5 Turbo — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "kling/v2-5-turbo-image-to-video-pro",
        "generation_type": "video",
        "price_tokens": 30,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": ["5", "10"], "mode": "image-to-video"},
    },

    # wan i2v → kie.ai
    {
        "code": "wan-2.6-i2v",
        "name": "Wan 2.6",
        "description": "Wan 2.6 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "wan/2-6-image-to-video",
        "generation_type": "video",
        "price_tokens": 25,
        "icon": "🎭",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": ["5", "10"], "mode": "image-to-video"},
    },

    # hailuo i2v → kie.ai
    {
        "code": "hailuo-i2v",
        "name": "Hailuo",
        "description": "Hailuo — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "hailuo/2-3-image-to-video-pro",
        "generation_type": "video",
        "price_tokens": 35,
        "icon": "🌊",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "image-to-video"},
    },

    # grok-imagine i2v → kie.ai
    {
        "code": "grok-imagine-i2v",
        "name": "Grok Imagine",
        "description": "xAI Grok — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "grok-imagine/image-to-video",
        "generation_type": "video",
        "price_tokens": 30,
        "icon": "🚀",
        "config": {"aspect_ratios": ["16:9", "9:16"], "mode": "image-to-video"},
    },

    # runway i2v → kie.ai
    {
        "code": "runway-gen4-i2v",
        "name": "Runway Gen-4",
        "description": "Runway Gen-4 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "runway",
        "generation_type": "video",
        "price_tokens": 45,
        "icon": "🛫",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"], "durations": ["5", "10"], "mode": "image-to-video"},
    },
    {
        "code": "kling-2.6-motion-control",
        "name": "Kling 2.6 Motion Control",
        "description": "Перенос движения с видео на изображение — танцы, жесты, движения",
        "provider": "kie.ai",
        "provider_model": "kling-2.6/motion-control",
        "generation_type": "video",
        "price_tokens": 50,
        "icon": "🕺",
        "config": {
            "mode": "motion-control",
            "requires_image": True,
            "requires_video": True,
        },
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
            logger.info(f"Seeded model | code={model_data['code']}, provider={model_data['provider']}")
        else:
            # Update provider and provider_model for existing models
            # in case they were seeded with old values
            changed = False
            if existing.provider != model_data["provider"]:
                existing.provider = model_data["provider"]
                changed = True
            if existing.provider_model != model_data["provider_model"]:
                existing.provider_model = model_data["provider_model"]
                changed = True
            if changed:
                await session.flush()
                logger.info(
                    f"Updated model provider | code={model_data['code']}, "
                    f"provider={model_data['provider']}, provider_model={model_data['provider_model']}"
                )

    await session.commit()

