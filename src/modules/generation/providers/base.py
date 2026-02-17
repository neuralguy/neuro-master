"""Base provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationTask:
    """Task data for generation."""
    task_id: str
    status: str
    result_url: str | None = None
    error: str | None = None
    raw_response: dict | None = None


@dataclass
class GenerationRequest:
    """Request data for generation."""
    model: str
    prompt: str | None = None
    image_url: str | None = None
    image_urls: list[str] | None = None
    video_url: str | None = None       # NEW: for motion control
    video_urls: list[str] | None = None # NEW: for motion control
    aspect_ratio: str = "1:1"
    duration: int | None = None
    output_format: str = "png"
    extra_params: dict | None = None


class BaseGenerationProvider(ABC):
    """Abstract base class for generation providers."""

    @abstractmethod
    async def create_task(self, request: GenerationRequest) -> GenerationTask:
        """Create a new generation task."""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> GenerationTask:
        """Get status of a generation task."""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a generation task."""
        pass

