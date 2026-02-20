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
from src.modules.generation.providers import GenerationRequest, kie_provider, poyo_provider
from src.modules.generation.repository import GenerationRepository
from src.modules.payments.repository import BalanceHistoryRepository
from src.modules.user.repository import UserRepository
from src.shared.enums import BalanceOperationType, GenerationStatus, GenerationType
from src.shared.logger import logger


async def _notify_user(telegram_id: int, text: str, **kwargs) -> None:
    """Send notification to user in Telegram chat. Silently ignores errors."""
    try:
        from src.bot.loader import bot
        await bot.send_message(chat_id=telegram_id, text=text, **kwargs)
    except Exception as e:
        logger.warning(f"Failed to notify user | telegram_id={telegram_id}, error={e}")


class GenerationService:
    """Service for generation business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.generation_repo = GenerationRepository(session)
        self.user_repo = UserRepository(session)
        self.model_repo = AIModelRepository(session)
        self.gallery_repo = GalleryRepository(session)
        self.balance_history_repo = BalanceHistoryRepository(session)
        self._providers = {
            "kie.ai": kie_provider,
            "poyo.ai": poyo_provider,
        }

    def _get_provider(self, provider_name: str):
        """Get provider instance by name."""
        provider = self._providers.get(provider_name)
        if not provider:
            logger.warning(f"Unknown provider '{provider_name}', falling back to kie.ai")
            return kie_provider
        return provider

    async def create_generation(
        self,
        user_id: int,
        model_code: str,
        prompt: str | None = None,
        image_url: str | None = None,
        video_url: str | None = None,
        aspect_ratio: str = "1:1",
        duration: int | None = None,
        extra_params: dict | None = None,
    ) -> Generation:
        """
        Create and start a new generation task.
        """
        # Get model
        model = await self.model_repo.get_by_code(model_code)
        if not model:
            raise NotFoundError("Модель", model_code)

        if not model.is_enabled:
            raise ValidationError("Эта модель временно недоступна")

        # Validate motion control requirements
        model_mode = model.config.get("mode", "")
        if model_mode == "motion-control":
            if not image_url:
                raise ValidationError("Для motion control необходимо загрузить изображение")
            if not video_url:
                raise ValidationError("Для motion control необходимо загрузить референсное видео")

        # Check user balance
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь", user_id)

        # Calculate cost: if model has price_per_second and duration provided — multiply
        if model.price_per_second is not None and duration is not None:
            cost = model.price_per_second * duration
        else:
            cost = model.price_tokens

        if user.balance < cost:
            raise InsufficientBalanceError(
                required=cost,
                available=user.balance,
            )

        # Deduct tokens
        new_balance = await self.user_repo.update_balance(
            user_id, -cost
        )

        # Create generation record
        generation = await self.generation_repo.create(
            user_id=user_id,
            model_id=model.id,
            generation_type=model.generation_type,
            tokens_spent=cost,
            prompt=prompt,
            input_file_url=image_url,
            params={
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "video_url": video_url,
                "_provider": model.provider,
                "_provider_model": model.provider_model,
                **(extra_params or {}),
            },
        )

        # Record balance change
        await self.balance_history_repo.create(
            user_id=user_id,
            amount=-cost,
            balance_after=new_balance,
            operation_type=BalanceOperationType.GENERATION,
            description=f"Генерация: {model.name}",
            reference_id=str(generation.id),
        )

        # Notify user that generation has started
        gen_type_text = "🎬 Видео" if model.generation_type == GenerationType.VIDEO else "🖼 Изображение"
        asyncio.create_task(
            _notify_user(
                user.telegram_id,
                f"{gen_type_text} генерируется...\n\n"
                f"🤖 Модель: <b>{model.name}</b>\n"
                f"💰 Списано: <b>{int(cost)} токенов</b>\n\n"
                f"⏳ Обычно занимает до 2 минут. Результат придёт сюда автоматически.",
                parse_mode="HTML",
            )
        )

        # Start generation task in background
        asyncio.create_task(
            self._process_generation(generation, model.provider_model, model.provider, user.telegram_id)
        )

        logger.info(
            f"Generation started | id={generation.id}, model={model_code}, "
            f"provider={model.provider}, user_id={user_id}, tokens={model.price_tokens}"
        )

        return generation

    async def _process_generation(
        self,
        generation: Generation,
        provider_model: str,
        provider_name: str,
        telegram_id: int | None = None,
    ) -> None:
        """Process generation in background."""
        try:
            # Determine output format
            if generation.generation_type == GenerationType.VIDEO:
                output_format = "mp4"
            else:
                output_format = "png"

            # Build request
            video_url = generation.params.get("video_url")

            request = GenerationRequest(
                model=provider_model,
                prompt=generation.prompt,
                image_url=generation.input_file_url,
                video_url=video_url,
                aspect_ratio=generation.params.get("aspect_ratio", "1:1"),
                duration=generation.params.get("duration"),
                output_format=output_format,
                extra_params={
                    k: v for k, v in generation.params.items()
                    if not k.startswith("_") and k != "video_url"
                },
            )

            # Select provider
            provider = self._get_provider(provider_name)

            logger.debug(
                f"Submitting to provider | provider={provider_name}, "
                f"model={provider_model}, generation_id={generation.id}"
            )

            # Create task on provider
            task = await provider.create_task(request)

            # Update generation with task ID
            async with self.session.begin_nested():
                await self.generation_repo.set_processing(
                    generation.id,
                    task.task_id,
                )
            await self.session.commit()

            # Poll for completion
            await self._poll_generation(
                generation.id,
                task.task_id,
                provider_name=provider_name,
                telegram_id=telegram_id,
            )

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

            if telegram_id:
                await _notify_user(
                    telegram_id,
                    "❌ Генерация не удалась. Токены возвращены на баланс.",
                )

    async def _poll_generation(
        self,
        generation_id: uuid.UUID,
        task_id: str,
        max_attempts: int = 120,
        interval: float = 3.0,
        provider_name: str = "kie.ai",
        telegram_id: int | None = None,
    ) -> None:
        """Poll for generation completion."""
        provider = self._get_provider(provider_name)

        for attempt in range(max_attempts):
            await asyncio.sleep(interval)

            try:
                task = await provider.get_task_status(task_id)

                if task.status == "success":
                    if not task.result_url:
                        logger.error(
                            f"Generation success but no result_url | "
                            f"id={generation_id}, task_id={task_id}, provider={provider_name}"
                        )
                        async with self.session.begin_nested():
                            await self.generation_repo.set_failed(
                                generation_id,
                                error_message="Провайдер вернул success, но без URL результата",
                            )
                        await self.session.commit()
                        generation = await self.generation_repo.get_by_id(generation_id)
                        if generation:
                            await self._refund_tokens(generation)
                        if telegram_id:
                            await _notify_user(telegram_id, "❌ Генерация не удалась. Токены возвращены на баланс.")
                        return

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

                    logger.info(f"Generation completed | id={generation_id}, provider={provider_name}")

                    # Send result to user in Telegram
                    if telegram_id and file_path:
                        await self._send_result_to_user(telegram_id, file_path, generation)

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

                    if telegram_id:
                        await _notify_user(telegram_id, "❌ Генерация не удалась. Токены возвращены на баланс.")

                    return

                # Still processing, continue polling
                if attempt % 10 == 0:
                    logger.debug(
                        f"Generation polling | id={generation_id}, "
                        f"attempt={attempt + 1}/{max_attempts}, status={task.status}, "
                        f"provider={provider_name}"
                    )

            except Exception as e:
                logger.error(
                    f"Polling error | id={generation_id}, attempt={attempt + 1}, "
                    f"provider={provider_name}, error={e}"
                )

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

        if telegram_id:
            await _notify_user(telegram_id, "❌ Генерация не удалась (timeout). Токены возвращены на баланс.")

    async def _send_result_to_user(
        self,
        telegram_id: int,
        file_path: str,
        generation: Generation | None,
    ) -> None:
        """Send generation result file to user in Telegram."""
        try:
            from aiogram.types import FSInputFile
            from src.bot.loader import bot

            path = Path(file_path)
            if not path.exists():
                await _notify_user(telegram_id, f"✅ Генерация завершена!\n\n🔗 Результат доступен в приложении.")
                return

            caption = "✅ Готово!"
            if generation and generation.prompt:
                caption += f"\n\n📝 <i>{generation.prompt[:200]}</i>"

            input_file = FSInputFile(path)

            is_video = path.suffix.lower() in (".mp4", ".webm", ".gif")
            if is_video:
                await bot.send_video(chat_id=telegram_id, video=input_file, caption=caption, parse_mode="HTML")
            else:
                await bot.send_photo(chat_id=telegram_id, photo=input_file, caption=caption, parse_mode="HTML")

        except Exception as e:
            logger.warning(f"Failed to send result to user | telegram_id={telegram_id}, error={e}")
            await _notify_user(telegram_id, "✅ Генерация завершена! Результат доступен в приложении.")

    async def _download_result(
        self,
        generation_id: uuid.UUID,
        url: str,
    ) -> str:
        """Download result file from URL."""

        url_lower = url.lower().split("?")[0]
        ext = ".png"
        if url_lower.endswith(".mp4") or "video" in url_lower:
            ext = ".mp4"
        elif url_lower.endswith(".webp"):
            ext = ".webp"
        elif url_lower.endswith(".jpg") or url_lower.endswith(".jpeg"):
            ext = ".jpg"
        elif url_lower.endswith(".gif"):
            ext = ".gif"
        elif url_lower.endswith(".webm"):
            ext = ".webm"

        file_name = f"{generation_id}{ext}"
        file_path = STORAGE_DIR / "generations" / file_name

        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if ext == ".png" and "video" in content_type:
                ext = ".mp4"
                file_name = f"{generation_id}{ext}"
                file_path = STORAGE_DIR / "generations" / file_name
            elif ext == ".png" and "jpeg" in content_type:
                ext = ".jpg"
                file_name = f"{generation_id}{ext}"
                file_path = STORAGE_DIR / "generations" / file_name

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(response.content)

        logger.debug(f"Result downloaded | id={generation_id}, path={file_path}, size={len(response.content)}")

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

