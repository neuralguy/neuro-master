"""Generation service."""

import asyncio
import uuid
from pathlib import Path

import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import STORAGE_DIR, settings
from src.core.exceptions import InsufficientBalanceError, NotFoundError, ValidationError
from src.modules.ai_models.repository import AIModelRepository
from src.modules.gallery.repository import GalleryRepository
from src.modules.generation.models import Generation
from src.modules.generation.providers import GenerationRequest, kie_provider
from src.modules.generation.repository import GenerationRepository
from src.modules.payments.repository import BalanceHistoryRepository
from src.modules.user.repository import UserRepository
from src.shared.enums import BalanceOperationType, GenerationStatus, GenerationType
from src.shared.logger import logger


class GenerationService:
    """Service for generation business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.generation_repo = GenerationRepository(session)
        self.user_repo = UserRepository(session)
        self.model_repo = AIModelRepository(session)
        self.gallery_repo = GalleryRepository(session)
        self.balance_history_repo = BalanceHistoryRepository(session)
        self.provider = kie_provider

    async def create_generation(
        self,
        user_id: int,
        model_code: str,
        prompt: str | None = None,
        image_url: str | None = None,
        aspect_ratio: str = "1:1",
        duration: int | None = None,
        extra_params: dict | None = None,
    ) -> Generation:
        """
        Create and start a new generation task.
        
        Args:
            user_id: User ID
            model_code: AI model code
            prompt: Text prompt
            image_url: Input image URL (for img2img or faceswap)
            aspect_ratio: Output aspect ratio
            duration: Video duration in seconds
            extra_params: Additional model-specific parameters
        """
        # Get model
        model = await self.model_repo.get_by_code(model_code)
        if not model:
            raise NotFoundError("Модель", model_code)
        
        if not model.is_enabled:
            raise ValidationError("Эта модель временно недоступна")
        
        # Check user balance
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь", user_id)
        
        if user.balance < model.price_tokens:
            raise InsufficientBalanceError(
                required=model.price_tokens,
                available=user.balance,
            )
        
        # Deduct tokens
        new_balance = await self.user_repo.update_balance(
            user_id, -model.price_tokens
        )
        
        # Create generation record
        generation = await self.generation_repo.create(
            user_id=user_id,
            model_id=model.id,
            generation_type=model.generation_type,
            tokens_spent=model.price_tokens,
            prompt=prompt,
            input_file_url=image_url,
            params={
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                **(extra_params or {}),
            },
        )
        
        # Record balance change
        await self.balance_history_repo.create(
            user_id=user_id,
            amount=-model.price_tokens,
            balance_after=new_balance,
            operation_type=BalanceOperationType.GENERATION,
            description=f"Генерация: {model.name}",
            reference_id=str(generation.id),
        )
        
        # Start generation task in background
        asyncio.create_task(
            self._process_generation(generation, model.provider_model)
        )
        
        logger.info(
            f"Generation started | id={generation.id}, model={model_code}, "
            f"user_id={user_id}, tokens={model.price_tokens}"
        )
        
        return generation

    async def _process_generation(
        self,
        generation: Generation,
        provider_model: str,
    ) -> None:
        """Process generation in background."""
        try:
            # Build request
            request = GenerationRequest(
                model=provider_model,
                prompt=generation.prompt,
                image_url=generation.input_file_url,
                aspect_ratio=generation.params.get("aspect_ratio", "1:1"),
                duration=generation.params.get("duration"),
                output_format="png" if generation.generation_type == GenerationType.IMAGE else "mp4",
                extra_params=generation.params,
            )
            
            # Create task on provider
            task = await self.provider.create_task(request)
            
            # Update generation with task ID
            async with self.session.begin_nested():
                await self.generation_repo.set_processing(
                    generation.id,
                    task.task_id,
                )
            await self.session.commit()
            
            # Poll for completion
            await self._poll_generation(generation.id, task.task_id)
            
        except Exception as e:
            logger.exception(f"Generation processing failed | id={generation.id}, error={e}")
            async with self.session.begin_nested():
                await self.generation_repo.set_failed(
                    generation.id,
                    error_message=str(e),
                )
            await self.session.commit()
            
            # Refund tokens
            await self._refund_tokens(generation)

    async def _poll_generation(
        self,
        generation_id: uuid.UUID,
        task_id: str,
        max_attempts: int = 120,
        interval: float = 3.0,
    ) -> None:
        """Poll for generation completion."""
        
        for attempt in range(max_attempts):
            await asyncio.sleep(interval)
            
            try:
                task = await self.provider.get_task_status(task_id)
                
                if task.status == "success":
                    # Download and save result
                    file_path = await self._download_result(
                        generation_id,
                        task.result_url,
                    )
                    
                    async with self.session.begin_nested():
                        await self.generation_repo.set_success(
                            generation_id,
                            result_url=task.result_url,
                            result_file_path=file_path,
                        )
                        
                        # Add to gallery
                        generation = await self.generation_repo.get_by_id(generation_id)
                        if generation:
                            await self.gallery_repo.create(
                                user_id=generation.user_id,
                                generation_id=generation.id,
                                file_path=file_path,
                                file_type="video" if generation.generation_type == GenerationType.VIDEO else "image",
                            )
                    
                    await self.session.commit()
                    
                    logger.info(f"Generation completed | id={generation_id}")
                    return
                
                elif task.status == "failed":
                    async with self.session.begin_nested():
                        await self.generation_repo.set_failed(
                            generation_id,
                            error_message=task.error or "Unknown error",
                        )
                    await self.session.commit()
                    
                    # Refund tokens
                    generation = await self.generation_repo.get_by_id(generation_id)
                    if generation:
                        await self._refund_tokens(generation)
                    
                    return
                
                # Still processing, continue polling
                logger.debug(
                    f"Generation polling | id={generation_id}, "
                    f"attempt={attempt + 1}, status={task.status}"
                )
                
            except Exception as e:
                logger.error(f"Polling error | id={generation_id}, error={e}")
        
        # Max attempts reached
        async with self.session.begin_nested():
            await self.generation_repo.set_failed(
                generation_id,
                error_message="Timeout: превышено время ожидания",
            )
        await self.session.commit()
        
        generation = await self.generation_repo.get_by_id(generation_id)
        if generation:
            await self._refund_tokens(generation)

    async def _download_result(
        self,
        generation_id: uuid.UUID,
        url: str,
    ) -> str:
        """Download result file from URL."""
        
        # Determine file extension from URL
        ext = ".png"
        if ".mp4" in url or "video" in url:
            ext = ".mp4"
        elif ".webp" in url:
            ext = ".webp"
        elif ".jpg" in url or ".jpeg" in url:
            ext = ".jpg"
        
        # Create file path
        file_name = f"{generation_id}{ext}"
        file_path = STORAGE_DIR / "generations" / file_name
        
        # Download file
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(response.content)
        
        logger.debug(f"Result downloaded | id={generation_id}, path={file_path}")
        
        return str(file_path)

    async def _refund_tokens(self, generation: Generation) -> None:
        """Refund tokens for failed generation."""
        try:
            new_balance = await self.user_repo.update_balance(
                generation.user_id,
                generation.tokens_spent,
            )
            
            await self.balance_history_repo.create(
                user_id=generation.user_id,
                amount=generation.tokens_spent,
                balance_after=new_balance,
                operation_type=BalanceOperationType.REFUND,
                description="Возврат за неудачную генерацию",
                reference_id=str(generation.id),
            )
            
            await self.session.commit()
            
            logger.info(
                f"Tokens refunded | user_id={generation.user_id}, "
                f"amount={generation.tokens_spent}"
            )
            
        except Exception as e:
            logger.error(f"Refund failed | generation_id={generation.id}, error={e}")

    async def get_generation(self, generation_id: uuid.UUID) -> Generation:
        """Get generation by ID."""
        generation = await self.generation_repo.get_by_id(generation_id)
        if not generation:
            raise NotFoundError("Генерация", str(generation_id))
        return generation

    async def get_user_generations(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        generation_type: GenerationType | None = None,
    ) -> list[Generation]:
        """Get user's generations."""
        return await self.generation_repo.get_user_generations(
            user_id, offset, limit, generation_type
        )

    async def get_stats(self) -> dict:
        """Get generation statistics."""
        return await self.generation_repo.get_stats()
