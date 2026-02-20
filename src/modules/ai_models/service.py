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
        price_tokens: float = 10.0,
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

    async def set_price(self, model_id: int, price_tokens: float) -> None:
        """Set model price."""
        if price_tokens <= 0:
            raise ValidationError("Цена должна быть больше 0")

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
#   - Video: veo3 models → provider: kie.ai
#   - Video: everything else (kling, sora, hailuo, wan, runway, grok-imagine) → provider: kie.ai
#
# poyo.ai provider_model = the model name as listed in poyo.ai docs
# kie.ai provider_model = the model string for kie.ai API
#

DEFAULT_MODELS = [
    # ==================== IMAGE: Text-to-Image ====================
    {
        "code": "nano-banana",
        "name": "Nano Banana",
        "description": "Google Gemini 2.5 Flash — быстрая генерация",
        "provider": "poyo.ai",
        "provider_model": "nano-banana",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },
    {
        "code": "nano-banana-2",
        "name": "Nano Banana Pro",
        "description": "Google Gemini 3 Pro — 2K, улучшенное качество",
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
        "description": "OpenAI GPT Image 1.5 — высокое качество",
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
        "description": "ByteDance Seedream 4.5 — 4K, профессиональное качество",
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
        "description": "Black Forest Labs Flux 2 Pro — фотореализм",
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
        "description": "Flux 2 Flex — гибкое качество/скорость",
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
        "description": "xAI Aurora — генерация изображений",
        "provider": "poyo.ai",
        "provider_model": "grok-imagine-image",
        "generation_type": "image",
        "price_tokens": 6,
        "icon": "🚀",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"], "mode": "text-to-image"},
    },
    {
        "code": "z-image",
        "name": "Z Image",
        "description": "Alibaba Z-Image — сверхбыстрая генерация",
        "provider": "poyo.ai",
        "provider_model": "z-image",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "⚡",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "mode": "text-to-image"},
    },

    # ==================== IMAGE: Image-to-Image (edit) ====================
    {
        "code": "nano-banana-edit",
        "name": "Nano Banana",
        "description": "Google Gemini — редактирование изображений",
        "provider": "poyo.ai",
        "provider_model": "nano-banana-edit",
        "generation_type": "image",
        "price_tokens": 4,
        "icon": "🍌",
        "config": {"aspect_ratios": ["1:1", "16:9", "9:16"], "mode": "image-to-image"},
    },
    {
        "code": "nano-banana-2-edit",
        "name": "Nano Banana Pro",
        "description": "Google Gemini 3 Pro — улучшенное редактирование",
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
        "description": "Flux 2 Pro — редактирование с мульти-референсом",
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

    # ==================== VIDEO: Text-to-Video ====================
    {
        "code": "veo3-fast",
        "name": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 — быстрая генерация видео со звуком",
        "provider": "kie.ai",
        "provider_model": "veo3_fast",
        "generation_type": "video",
        "price_tokens": 8,
        "price_per_second": 8,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [8], "mode": "text-to-video"},
    },
    {
        "code": "veo3-quality",
        "name": "Veo 3.1 Quality",
        "description": "Google Veo 3.1 — высокое качество видео",
        "provider": "kie.ai",
        "provider_model": "veo3",
        "generation_type": "video",
        "price_tokens": 8,
        "price_per_second": 8,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [8], "mode": "text-to-video"},
    },
    {
        "code": "kling-3.0-standard",
        "name": "Kling 3.0",
        "description": "Kuaishou Kling 3.0 — 720p, мульти-шоты, аудио",
        "provider": "poyo.ai",
        "provider_model": "kling-3.0/standard",
        "generation_type": "video",
        "price_tokens": 4,
        "price_per_second": 4,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [3, 5, 10, 15], "mode": "text-to-video"},
    },
    {
        "code": "kling-3.0-pro",
        "name": "Kling 3.0 Pro",
        "description": "Kuaishou Kling 3.0 Pro — 1080p, мульти-шоты, аудио",
        "provider": "poyo.ai",
        "provider_model": "kling-3.0/pro",
        "generation_type": "video",
        "price_tokens": 6,
        "price_per_second": 6,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [3, 5, 10, 15], "mode": "text-to-video"},
    },
    {
        "code": "kling-2.6",
        "name": "Kling 2.6",
        "description": "Kling 2.6 — видео с нативным аудио",
        "provider": "poyo.ai",
        "provider_model": "kling-2.6",
        "generation_type": "video",
        "price_tokens": 4,
        "price_per_second": 4,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [5, 10], "mode": "text-to-video"},
    },
    {
        "code": "sora-2",
        "name": "Sora 2",
        "description": "OpenAI Sora 2 — генерация видео",
        "provider": "poyo.ai",
        "provider_model": "sora-2",
        "generation_type": "video",
        "price_tokens": 5,
        "price_per_second": 5,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [10, 15], "mode": "text-to-video"},
    },
    {
        "code": "sora-2-pro",
        "name": "Sora 2 Pro",
        "description": "OpenAI Sora 2 Pro — премиум HD видео",
        "provider": "poyo.ai",
        "provider_model": "sora-2-pro",
        "generation_type": "video",
        "price_tokens": 5,
        "price_per_second": 5,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [15, 25], "mode": "text-to-video"},
    },
    {
        "code": "seedance-1.5-pro",
        "name": "Seedance 1.5 Pro",
        "description": "ByteDance — аудио-визуальная генерация, lip-sync",
        "provider": "poyo.ai",
        "provider_model": "seedance-1.5-pro",
        "generation_type": "video",
        "price_tokens": 5,
        "price_per_second": 5,
        "icon": "🌱",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [4, 8, 12], "mode": "text-to-video"},
    },
    {
        "code": "hailuo-02-pro",
        "name": "Hailuo 02 Pro",
        "description": "MiniMax Hailuo 02 — 1080p кинематографичное видео",
        "provider": "poyo.ai",
        "provider_model": "hailuo-02-pro",
        "generation_type": "video",
        "price_tokens": 6,
        "price_per_second": 6,
        "icon": "🌊",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [6], "mode": "text-to-video"},
    },
    {
        "code": "wan-2.6",
        "name": "Wan 2.6",
        "description": "Alibaba Wan 2.6 — мульти-шоты, 1080p",
        "provider": "poyo.ai",
        "provider_model": "wan2.6-text-to-video",
        "generation_type": "video",
        "price_tokens": 3,
        "price_per_second": 3,
        "icon": "🎭",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [5, 10, 15], "mode": "text-to-video"},
    },
    {
        "code": "grok-imagine-video",
        "name": "Grok Imagine Video",
        "description": "xAI Aurora — генерация видео",
        "provider": "poyo.ai",
        "provider_model": "grok-imagine",
        "generation_type": "video",
        "price_tokens": 4,
        "price_per_second": 4,
        "icon": "🚀",
        "config": {"aspect_ratios": ["1:1", "2:3", "3:2"], "durations": [6, 10], "mode": "text-to-video"},
    },
    {
        "code": "runway-gen4",
        "name": "Runway Gen-4",
        "description": "Runway Gen-4 Turbo — генерация видео",
        "provider": "kie.ai",
        "provider_model": "runway",
        "generation_type": "video",
        "price_tokens": 6,
        "price_per_second": 6,
        "icon": "🛫",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"], "durations": [5, 10], "mode": "text-to-video"},
    },

    # ==================== VIDEO: Image-to-Video ====================
    {
        "code": "veo3-fast-i2v",
        "name": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "veo3_fast",
        "generation_type": "video",
        "price_tokens": 8,
        "price_per_second": 8,
        "icon": "🎬",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [8], "mode": "image-to-video"},
    },
    {
        "code": "kling-3.0-standard-i2v",
        "name": "Kling 3.0",
        "description": "Kling 3.0 — видео из изображения, 720p",
        "provider": "poyo.ai",
        "provider_model": "kling-3.0/standard",
        "generation_type": "video",
        "price_tokens": 4,
        "price_per_second": 4,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [3, 5, 10, 15], "mode": "image-to-video"},
    },
    {
        "code": "kling-2.6-i2v",
        "name": "Kling 2.6",
        "description": "Kling 2.6 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "kling-2.6/image-to-video",
        "generation_type": "video",
        "price_tokens": 4,
        "price_per_second": 4,
        "icon": "🎞️",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [5, 10], "mode": "image-to-video"},
    },
    {
        "code": "sora-2-i2v",
        "name": "Sora 2",
        "description": "OpenAI Sora 2 — видео из изображения",
        "provider": "poyo.ai",
        "provider_model": "sora-2",
        "generation_type": "video",
        "price_tokens": 5,
        "price_per_second": 5,
        "icon": "🎥",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1"], "durations": [10, 15], "mode": "image-to-video"},
    },
    {
        "code": "seedance-1.5-pro-i2v",
        "name": "Seedance 1.5 Pro",
        "description": "ByteDance Seedance — видео из изображения с аудио",
        "provider": "poyo.ai",
        "provider_model": "seedance-1.5-pro",
        "generation_type": "video",
        "price_tokens": 5,
        "price_per_second": 5,
        "icon": "🌱",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [4, 8, 12], "mode": "image-to-video"},
    },
    {
        "code": "wan-2.6-i2v",
        "name": "Wan 2.6",
        "description": "Wan 2.6 — видео из изображения",
        "provider": "poyo.ai",
        "provider_model": "wan2.6-image-to-video",
        "generation_type": "video",
        "price_tokens": 3,
        "price_per_second": 3,
        "icon": "🎭",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [5, 10, 15], "mode": "image-to-video"},
    },
    {
        "code": "hailuo-i2v",
        "name": "Hailuo 02",
        "description": "Hailuo 02 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "hailuo/02-image-to-video-pro",
        "generation_type": "video",
        "price_tokens": 6,
        "price_per_second": 6,
        "icon": "🌊",
        "config": {"aspect_ratios": ["16:9", "9:16"], "durations": [6, 10], "mode": "image-to-video"},
    },
    {
        "code": "grok-imagine-i2v",
        "name": "Grok Imagine",
        "description": "xAI Grok — видео из изображения",
        "provider": "poyo.ai",
        "provider_model": "grok-imagine",
        "generation_type": "video",
        "price_tokens": 4,
        "price_per_second": 4,
        "icon": "🚀",
        "config": {"aspect_ratios": ["1:1", "2:3", "3:2"], "durations": [6, 10], "mode": "image-to-video"},
    },
    {
        "code": "runway-gen4-i2v",
        "name": "Runway Gen-4",
        "description": "Runway Gen-4 — видео из изображения",
        "provider": "kie.ai",
        "provider_model": "runway",
        "generation_type": "video",
        "price_tokens": 6,
        "price_per_second": 6,
        "icon": "🛫",
        "config": {"aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"], "durations": [5, 10], "mode": "image-to-video"},
    },

    # ==================== VIDEO: Motion Control ====================
    {
        "code": "kling-2.6-motion-control",
        "name": "Kling 2.6 Motion Control",
        "description": "Перенос движения с видео на изображение — танцы, жесты",
        "provider": "kie.ai",
        "provider_model": "kling-2.6/motion-control",
        "generation_type": "video",
        "price_tokens": 1,
        "price_per_second": 1,
        "price_display_mode": "per_second",
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

    known_codes = {m["code"] for m in DEFAULT_MODELS}

    for i, model_data in enumerate(DEFAULT_MODELS):
        existing = await repo.get_by_code(model_data["code"])
        if not existing:
            await repo.create(
                **model_data,
                sort_order=i,
            )
            logger.info(f"Seeded model | code={model_data['code']}, provider={model_data['provider']}")
        else:
            # Update technical fields (provider, provider_model, name, description, config, icon, sort_order)
            # but preserve price_tokens set by admin
            changed = False
            for field in ("provider", "provider_model", "name", "description", "icon"):
                if getattr(existing, field) != model_data.get(field):
                    setattr(existing, field, model_data.get(field))
                    changed = True
            if existing.config != model_data.get("config"):
                existing.config = model_data.get("config")
                changed = True
            # Sync price_per_second и price_display_mode из DEFAULT_MODELS
            new_pps = model_data.get("price_per_second")
            if existing.price_per_second != new_pps:
                existing.price_per_second = new_pps
                changed = True
            new_pdm = model_data.get("price_display_mode", "fixed")
            if existing.price_display_mode != new_pdm:
                existing.price_display_mode = new_pdm
                changed = True
            if existing.sort_order != i:
                existing.sort_order = i
                changed = True
            if changed:
                await session.flush()
                logger.info(
                    f"Updated model | code={model_data['code']}, "
                    f"provider={model_data['provider']}, provider_model={model_data['provider_model']}"
                )

    # Disable models that are no longer in DEFAULT_MODELS
    all_models = await repo.get_all(enabled_only=False)
    for model in all_models:
        if model.code not in known_codes and model.is_enabled:
            await repo.set_enabled(model.id, False)
            logger.info(f"Disabled obsolete model | code={model.code}")

    await session.commit()

