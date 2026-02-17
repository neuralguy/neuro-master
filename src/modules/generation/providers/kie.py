"""kie.ai provider implementation."""

import json
import httpx
from typing import Any

from src.config import settings
from src.core.exceptions import ExternalAPIError
from src.modules.generation.providers.base import (
    BaseGenerationProvider,
    GenerationRequest,
    GenerationTask,
)
from src.shared.logger import logger


class KieProvider(BaseGenerationProvider):
    """kie.ai API provider."""

    BASE_URL = "https://api.kie.ai/api/v1"
    
    def __init__(self):
        self.api_key = settings.KIE_API_KEY.get_secret_value()
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
        """Make HTTP request to kie.ai API."""
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
                    f"kie.ai response | endpoint={endpoint}, "
                    f"status={response.status_code}, code={data.get('code')}"
                )
                
                if response.status_code != 200:
                    raise ExternalAPIError(
                        service="kie.ai",
                        message=data.get("msg", "Unknown error"),
                        status_code=response.status_code,
                    )
                
                if data.get("code") != 200:
                    raise ExternalAPIError(
                        service="kie.ai",
                        message=data.get("msg", "API error"),
                        status_code=data.get("code"),
                    )
                
                return data
                
            except httpx.RequestError as e:
                logger.error(f"kie.ai request failed | error={e}")
                raise ExternalAPIError(
                    service="kie.ai",
                    message=str(e),
                )

    async def create_task(self, request: GenerationRequest) -> GenerationTask:
        """Create a new generation task on kie.ai."""
        
        # Check if this is a motion control request
        is_motion_control = "motion-control" in request.model
        
        # Build input based on request
        input_data = {
            "prompt": request.prompt or "",
        }
        
        if is_motion_control:
            # Motion control uses input_urls for images and video_urls for videos
            if request.image_urls:
                input_data["input_urls"] = request.image_urls
            elif request.image_url:
                input_data["input_urls"] = [request.image_url]
            
            if request.video_urls:
                input_data["video_urls"] = request.video_urls
            elif request.video_url:
                input_data["video_urls"] = [request.video_url]
            
            # Motion control specific params
            input_data["mode"] = request.extra_params.get("mode", "720p") if request.extra_params else "720p"
            input_data["character_orientation"] = request.extra_params.get("character_orientation", "image") if request.extra_params else "image"
        else:
            # Standard request
            input_data["aspect_ratio"] = request.aspect_ratio
            input_data["output_format"] = request.output_format
            
            # Add image URLs if provided
            if request.image_urls:
                input_data["image_urls"] = request.image_urls
            elif request.image_url:
                input_data["image_urls"] = [request.image_url]
            
            # Add duration for video
            if request.duration:
                input_data["duration"] = request.duration
        
        # Add extra params
        if request.extra_params:
            for k, v in request.extra_params.items():
                if k not in input_data and not k.startswith("_"):
                    input_data[k] = v
        
        payload = {
            "model": request.model,
            "input": input_data,
        }
        
        logger.info(f"Creating kie.ai task | model={request.model}, motion_control={is_motion_control}")
        logger.debug(f"kie.ai payload | {payload}")
        
        response = await self._request(
            method="POST",
            endpoint="/jobs/createTask",
            json_data=payload,
        )
        
        task_id = response.get("data", {}).get("taskId")
        
        if not task_id:
            raise ExternalAPIError(
                service="kie.ai",
                message="No taskId in response",
            )
        
        logger.info(f"kie.ai task created | task_id={task_id}")
        
        return GenerationTask(
            task_id=task_id,
            status="pending",
            raw_response=response,
        )

    async def get_task_status(self, task_id: str) -> GenerationTask:
        """Get status of a generation task."""
        
        response = await self._request(
            method="GET",
            endpoint="/jobs/recordInfo",
            params={"taskId": task_id},
        )
        
        data = response.get("data", {})
        state = data.get("state", "unknown")
        
        # Map kie.ai states to our states
        status_map = {
            "waiting": "pending",
            "queuing": "pending",
            "generating": "processing",
            "success": "success",
            "fail": "failed",
            "failed": "failed",
        }
        
        status = status_map.get(state, state)
        
        result_url = None
        error = None
        
        if status == "success":
            result_json = data.get("resultJson", {})
            
            if isinstance(result_json, str):
                try:
                    result_json = json.loads(result_json)
                except json.JSONDecodeError:
                    result_json = {}
            
            result_urls = result_json.get("resultUrls", [])
            if result_urls:
                result_url = result_urls[0]
            else:
                result_url = (
                    result_json.get("url") or 
                    result_json.get("video_url") or
                    result_json.get("image_url") or
                    data.get("resultUrl") or
                    data.get("url")
                )
        
        elif status == "failed":
            error = data.get("errorMessage") or data.get("error") or data.get("failMsg") or "Generation failed"
        
        logger.debug(f"kie.ai task status | task_id={task_id}, status={status}, result_url={result_url}")
        
        return GenerationTask(
            task_id=task_id,
            status=status,
            result_url=result_url,
            error=error,
            raw_response=response,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a generation task (if supported)."""
        logger.debug(f"Task cancellation not supported | task_id={task_id}")
        return False

    async def get_credits(self) -> int:
        """Get remaining credits."""
        response = await self._request(
            method="GET",
            endpoint="/user/credits",
        )
        return response.get("data", {}).get("credits", 0)


# Singleton instance
kie_provider = KieProvider()

