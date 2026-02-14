"""Common schemas."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    code: str | None = None


class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int
    offset: int
    limit: int
