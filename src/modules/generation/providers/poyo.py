"""poyo.ai provider implementation."""

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
    """poyo.ai API provider."""

    BASE_URL = "https://api.poyo.ai"

    def __init__(self):
        self.api_key = settings.POYO_API_KEY.get_secret_value()
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
        url = f"{self.BASE_URL}{endpoint}"

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
                    f"status={response.status_code}, body_keys={list(data.keys()) if isinstance(data, dict) else 'not_dict'}"
                )

                if response.status_code not in (200, 201):
                    error_msg = "Unknown error"
                    if isinstance(data, dict):
                        error_msg = data.get("message") or data.get("error") or data.get("detail") or str(data)
                    raise ExternalAPIError(
                        service="poyo.ai",
                        message=error_msg,
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
        """Create a new generation task on poyo.ai.

        POST /api/generate/submit
        {
            "model": "nano-banana",
            "callback_url": "",
            "input": {
                "prompt": "...",
                "size": "1:1",
                "image_urls": [...]   // for edit models
            }
        }
        """
        input_data: dict = {}

        if request.prompt:
            input_data["prompt"] = request.prompt

        # poyo.ai uses "size" instead of "aspect_ratio"
        input_data["size"] = request.aspect_ratio or "1:1"

        # Add image URLs for edit / image-to-image / image-to-video models
        if request.image_urls:
            input_data["image_urls"] = request.image_urls
        elif request.image_url:
            input_data["image_urls"] = [request.image_url]

        # Add duration for video models (veo3)
        if request.duration:
            input_data["duration"] = request.duration

        # Merge any extra params into input
        if request.extra_params:
            for k, v in request.extra_params.items():
                # Skip internal keys
                if k.startswith("_"):
                    continue
                if k not in input_data:
                    input_data[k] = v

        payload = {
            "model": request.model,
            "callback_url": "",
            "input": input_data,
        }

        logger.info(f"Creating poyo.ai task | model={request.model}, payload_keys={list(payload.keys())}")
        logger.debug(f"poyo.ai submit payload | {payload}")

        response = await self._request(
            method="POST",
            endpoint="/api/generate/submit",
            json_data=payload,
        )

        # Response: { "data": { "task_id": "..." } }
        response_data = response.get("data", {})
        task_id = response_data.get("task_id")

        if not task_id:
            # Try top-level
            task_id = response.get("task_id") or response.get("id")

        if not task_id:
            raise ExternalAPIError(
                service="poyo.ai",
                message=f"No task_id in response: {response}",
            )

        logger.info(f"poyo.ai task created | task_id={task_id}")

        return GenerationTask(
            task_id=str(task_id),
            status="pending",
            raw_response=response,
        )

    async def get_task_status(self, task_id: str) -> GenerationTask:
        """Get status of a generation task.

        GET /api/generate/status/{task_id}
        Response: {
            "data": {
                "status": "finished" | "pending" | "processing" | "failed",
                "files": [{"file_url": "..."}],
                "error_message": "..."
            }
        }
        """
        response = await self._request(
            method="GET",
            endpoint=f"/api/generate/status/{task_id}",
        )

        data = response.get("data", {})
        if not isinstance(data, dict):
            data = {}

        raw_status = data.get("status", "unknown")

        # Map poyo.ai statuses to our internal statuses
        status_map = {
            "pending": "pending",
            "queued": "pending",
            "waiting": "pending",
            "processing": "processing",
            "running": "processing",
            "generating": "processing",
            "finished": "success",
            "completed": "success",
            "success": "success",
            "done": "success",
            "failed": "failed",
            "error": "failed",
        }

        status = status_map.get(raw_status, raw_status)
        result_url = None
        error = None

        if status == "success":
            # Extract URL from files array
            files = data.get("files", [])
            if files and isinstance(files, list):
                first_file = files[0]
                if isinstance(first_file, dict):
                    result_url = first_file.get("file_url") or first_file.get("url")
                elif isinstance(first_file, str):
                    result_url = first_file

            # Fallback: try other fields
            if not result_url:
                result_url = (
                    data.get("result_url")
                    or data.get("output_url")
                    or data.get("url")
                    or data.get("file_url")
                )

        elif status == "failed":
            error = (
                data.get("error_message")
                or data.get("error")
                or data.get("message")
                or "Generation failed"
            )

        logger.debug(
            f"poyo.ai task status | task_id={task_id}, raw_status={raw_status}, "
            f"status={status}, result_url={result_url}, error={error}"
        )

        return GenerationTask(
            task_id=task_id,
            status=status,
            result_url=result_url,
            error=error,
            raw_response=response,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a generation task (poyo.ai may not support this)."""
        logger.debug(f"poyo.ai task cancellation not implemented | task_id={task_id}")
        return False


poyo_provider = PoyoProvider()

