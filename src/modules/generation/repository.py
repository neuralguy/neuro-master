"""Generation repository."""

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.generation.models import Generation
from src.shared.enums import GenerationStatus, GenerationType
from src.shared.logger import logger


class GenerationRepository:
    """Repository for Generation database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        model_id: int,
        generation_type: GenerationType,
        tokens_spent: int,
        prompt: str | None = None,
        input_file_path: str | None = None,
        input_file_url: str | None = None,
        params: dict | None = None,
    ) -> Generation:
        """Create new generation task."""
        generation = Generation(
            user_id=user_id,
            model_id=model_id,
            generation_type=generation_type,
            tokens_spent=tokens_spent,
            prompt=prompt,
            input_file_path=input_file_path,
            input_file_url=input_file_url,
            params=params or {},
            status=GenerationStatus.PENDING,
        )
        self.session.add(generation)
        await self.session.flush()
        await self.session.refresh(generation)
        
        logger.info(
            f"Generation created | id={generation.id}, "
            f"type={generation_type.value}, tokens={tokens_spent}"
        )
        return generation

    async def get_by_id(self, generation_id: uuid.UUID) -> Generation | None:
        """Get generation by ID."""
        result = await self.session.execute(
            select(Generation)
            .where(Generation.id == generation_id)
            .options(selectinload(Generation.model))
        )
        return result.scalar_one_or_none()

    async def get_by_kie_task_id(self, kie_task_id: str) -> Generation | None:
        """Get generation by kie.ai task ID."""
        result = await self.session.execute(
            select(Generation)
            .where(Generation.kie_task_id == kie_task_id)
            .options(selectinload(Generation.model))
        )
        return result.scalar_one_or_none()

    async def update(self, generation: Generation, **kwargs) -> Generation:
        """Update generation fields."""
        for key, value in kwargs.items():
            if hasattr(generation, key):
                setattr(generation, key, value)
        
        await self.session.flush()
        await self.session.refresh(generation)
        return generation

    async def set_processing(
        self,
        generation_id: uuid.UUID,
        kie_task_id: str,
    ) -> None:
        """Set generation status to processing."""
        await self.session.execute(
            update(Generation)
            .where(Generation.id == generation_id)
            .values(
                status=GenerationStatus.PROCESSING,
                kie_task_id=kie_task_id,
            )
        )
        await self.session.flush()
        
        logger.debug(f"Generation processing | id={generation_id}, task_id={kie_task_id}")

    async def set_success(
        self,
        generation_id: uuid.UUID,
        result_url: str,
        result_file_path: str | None = None,
    ) -> None:
        """Set generation as successful."""
        await self.session.execute(
            update(Generation)
            .where(Generation.id == generation_id)
            .values(
                status=GenerationStatus.SUCCESS,
                result_url=result_url,
                result_file_path=result_file_path,
                completed_at=datetime.utcnow(),
            )
        )
        await self.session.flush()
        
        logger.info(f"Generation success | id={generation_id}")

    async def set_failed(
        self,
        generation_id: uuid.UUID,
        error_message: str,
    ) -> None:
        """Set generation as failed."""
        await self.session.execute(
            update(Generation)
            .where(Generation.id == generation_id)
            .values(
                status=GenerationStatus.FAILED,
                error_message=error_message,
                completed_at=datetime.utcnow(),
            )
        )
        await self.session.flush()
        
        logger.warning(f"Generation failed | id={generation_id}, error={error_message}")

    async def get_pending_generations(self, limit: int = 100) -> list[Generation]:
        """Get all pending/processing generations for polling."""
        result = await self.session.execute(
            select(Generation)
            .where(Generation.status.in_([
                GenerationStatus.PENDING,
                GenerationStatus.PROCESSING,
            ]))
            .where(Generation.kie_task_id.isnot(None))
            .order_by(Generation.created_at)
            .limit(limit)
            .options(selectinload(Generation.model))
        )
        return list(result.scalars().all())

    async def get_user_generations(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        generation_type: GenerationType | None = None,
        status: GenerationStatus | None = None,
    ) -> list[Generation]:
        """Get user's generations."""
        query = select(Generation).where(Generation.user_id == user_id)
        
        if generation_type:
            query = query.where(Generation.generation_type == generation_type)
        
        if status:
            query = query.where(Generation.status == status)
        
        query = (
            query
            .order_by(Generation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(Generation.model))
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_generations(
        self,
        user_id: int,
        generation_type: GenerationType | None = None,
    ) -> int:
        """Count user's generations."""
        query = select(func.count(Generation.id)).where(Generation.user_id == user_id)
        
        if generation_type:
            query = query.where(Generation.generation_type == generation_type)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_stats(self) -> dict:
        """Get generation statistics."""
        total = await self.session.execute(
            select(func.count(Generation.id))
        )
        
        success = await self.session.execute(
            select(func.count(Generation.id))
            .where(Generation.status == GenerationStatus.SUCCESS)
        )
        
        failed = await self.session.execute(
            select(func.count(Generation.id))
            .where(Generation.status == GenerationStatus.FAILED)
        )
        
        pending = await self.session.execute(
            select(func.count(Generation.id))
            .where(Generation.status.in_([
                GenerationStatus.PENDING,
                GenerationStatus.PROCESSING,
            ]))
        )
        
        tokens_spent = await self.session.execute(
            select(func.sum(Generation.tokens_spent))
            .where(Generation.status == GenerationStatus.SUCCESS)
        )
        
        return {
            "total": total.scalar_one(),
            "success": success.scalar_one(),
            "failed": failed.scalar_one(),
            "pending": pending.scalar_one(),
            "tokens_spent": tokens_spent.scalar_one() or 0,
        }
