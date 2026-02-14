"""poyo.ai provider implementation (stub — needs API docs)."""

import httpx

from src.config import settings
from src.core.exceptions import ExternalAPIError
from src.modules.generation.providers.base import (
    BaseGenerationProvider,
    GenerationRequest,
    GenerationTask,
)
from src.shared.logger import logger


class PoyoProvider(BaseGenerationProvider):
    """poyo.ai API provider.
    
    NOTE: This is a stub implementation. Actual API endpoints,
    request/response formats need to be filled in once API docs are available.
    """

    def __init__(self):
        self.api_key = settings.POYO_API_KEY.get_secret_value()
        self.base_url = settings.POYO_API_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make HTTP request to poyo.ai API."""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    params=params,
                )

                data = response.json()

                logger.debug(
                    f"poyo.ai response | endpoint={endpoint}, "
                    f"status={response.status_code}"
                )

                if response.status_code != 200:
                    raise ExternalAPIError(
                        service="poyo.ai",
                        message=data.get("message", data.get("error", "Unknown error")),
                        status_code=response.status_code,
                    )

                return data

            except httpx.RequestError as e:
                logger.error(f"poyo.ai request failed | error={e}")
                raise ExternalAPIError(
                    service="poyo.ai",
                    message=str(e),
                )

    async def create_task(self, request: GenerationRequest) -> GenerationTask:
        """Create a new generation task on poyo.ai."""
        # TODO: Replace with actual API format once docs are available
        input_data = {
            "model": request.model,
            "prompt": request.prompt or "",
            "aspect_ratio": request.aspect_ratio,
        }

        if request.image_urls:
            input_data["image_urls"] = request.image_urls
        elif request.image_url:
            input_data["image_urls"] = [request.image_url]

        if request.duration:
            input_data["duration"] = request.duration

        if request.extra_params:
            input_data.update(request.extra_params)

        logger.debug(f"Creating poyo.ai task | model={request.model}")

        response = await self._request(
            method="POST",
            endpoint="/v1/tasks",  # placeholder endpoint
            json_data=input_data,
        )

        task_id = response.get("task_id") or response.get("id")

        if not task_id:
            raise ExternalAPIError(
                service="poyo.ai",
                message="No task_id in response",
            )

        logger.info(f"poyo.ai task created | task_id={task_id}")

        return GenerationTask(
            task_id=str(task_id),
            status="pending",
            raw_response=response,
        )

    async def get_task_status(self, task_id: str) -> GenerationTask:
        """Get status of a generation task."""
        response = await self._request(
            method="GET",
            endpoint=f"/v1/tasks/{task_id}",  # placeholder endpoint
        )

        state = response.get("status", response.get("state", "unknown"))

        status_map = {
            "waiting": "pending",
            "queued": "pending",
            "pending": "pending",
            "processing": "processing",
            "running": "processing",
            "completed": "success",
            "success": "success",
            "done": "success",
            "failed": "failed",
            "error": "failed",
        }

        status = status_map.get(state, state)
        result_url = None
        error = None

        if status == "success":
            result_url = (
                response.get("result_url")
                or response.get("output_url")
                or response.get("url")
            )
            # Try nested
            if not result_url and isinstance(response.get("result"), dict):
                result_url = response["result"].get("url")
            if not result_url and isinstance(response.get("output"), list) and response["output"]:
                result_url = response["output"][0]

        elif status == "failed":
            error = (
                response.get("error")
                or response.get("error_message")
                or response.get("message")
                or "Generation failed"
            )

        logger.debug(
            f"poyo.ai task status | task_id={task_id}, status={status}, result_url={result_url}"
        )

        return GenerationTask(
            task_id=task_id,
            status=status,
            result_url=result_url,
            error=error,
            raw_response=response,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a generation task."""
        try:
            await self._request(
                method="POST",
                endpoint=f"/v1/tasks/{task_id}/cancel",  # placeholder
            )
            return True
        except Exception:
            logger.debug(f"poyo.ai task cancellation failed | task_id={task_id}")
            return False


poyo_provider = PoyoProvider()

