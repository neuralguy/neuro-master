"""AI Models repository."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.ai_models.models import AIModel
from src.shared.enums import GenerationType
from src.shared.logger import logger


class AIModelRepository:
    """Repository for AIModel database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_id: int) -> AIModel | None:
        """Get model by ID."""
        result = await self.session.execute(
            select(AIModel).where(AIModel.id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> AIModel | None:
        """Get model by code."""
        result = await self.session.execute(
            select(AIModel).where(AIModel.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        enabled_only: bool = False,
        generation_type: GenerationType | None = None,
    ) -> list[AIModel]:
        """Get all models with optional filtering."""
        query = select(AIModel)
        
        if enabled_only:
            query = query.where(AIModel.is_enabled == True)
        
        if generation_type:
            query = query.where(AIModel.generation_type == generation_type)
        
        query = query.order_by(AIModel.sort_order, AIModel.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        code: str,
        name: str,
        provider_model: str,
        generation_type: GenerationType,
        price_tokens: int = 10,
        description: str | None = None,
        provider: str = "kie.ai",
        config: dict | None = None,
        icon: str | None = None,
        sort_order: int = 0,
    ) -> AIModel:
        """Create new AI model."""
        model = AIModel(
            code=code,
            name=name,
            description=description,
            provider=provider,
            provider_model=provider_model,
            generation_type=generation_type,
            price_tokens=price_tokens,
            config=config or {},
            icon=icon,
            sort_order=sort_order,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        
        logger.info(f"AI model created | code={code}, type={generation_type}")
        return model

    async def update(self, model: AIModel, **kwargs) -> AIModel:
        """Update model fields."""
        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        await self.session.flush()
        await self.session.refresh(model)
        
        logger.info(f"AI model updated | code={model.code}")
        return model

    async def set_enabled(self, model_id: int, enabled: bool) -> None:
        """Enable or disable model."""
        await self.session.execute(
            update(AIModel)
            .where(AIModel.id == model_id)
            .values(is_enabled=enabled)
        )
        await self.session.flush()
        
        logger.info(f"AI model {'enabled' if enabled else 'disabled'} | id={model_id}")

    async def update_price(self, model_id: int, price_tokens: int) -> None:
        """Update model price."""
        await self.session.execute(
            update(AIModel)
            .where(AIModel.id == model_id)
            .values(price_tokens=price_tokens)
        )
        await self.session.flush()
        
        logger.info(f"AI model price updated | id={model_id}, price={price_tokens}")

    async def count(self, enabled_only: bool = False) -> int:
        """Count models."""
        query = select(func.count(AIModel.id))
        
        if enabled_only:
            query = query.where(AIModel.is_enabled == True)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete(self, model_id: int) -> None:
        """Delete model."""
        model = await self.get_by_id(model_id)
        if model:
            await self.session.delete(model)
            await self.session.flush()
            logger.info(f"AI model deleted | id={model_id}")
