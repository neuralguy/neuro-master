"""Upload routes."""

import uuid
import base64
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from src.api.dependencies import CurrentUser
from src.config import settings, STORAGE_DIR
from src.shared.logger import logger

router = APIRouter()

UPLOAD_DIR = STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB (видео может быть больше)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


class UploadResponse(BaseModel):
    url: str
    filename: str
    file_type: str  # "image" или "video"


class Base64UploadRequest(BaseModel):
    data: str  # base64 encoded image with data:image/...;base64, prefix
    filename: str | None = None


@router.post("/file", response_model=UploadResponse)
async def upload_file(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Upload a file (image or video) and return its URL."""
    
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла: {file.content_type}. "
                   f"Разрешены изображения: {', '.join(ALLOWED_IMAGE_TYPES)} "
                   f"и видео: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )
    
    is_video = file.content_type in ALLOWED_VIDEO_TYPES
    max_size = MAX_FILE_SIZE if is_video else MAX_IMAGE_SIZE
    
    # Read and validate size
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимум {max_size // 1024 // 1024}MB"
        )
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else ("mp4" if is_video else "jpg")
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Build URL
    url = f"{settings.WEBAPP_URL}/static/uploads/{filename}"
    file_type = "video" if is_video else "image"
    
    logger.info(f"File uploaded | user_id={current_user.id}, filename={filename}, type={file_type}, size={len(content)}")
    
    return UploadResponse(url=url, filename=filename, file_type=file_type)


@router.post("/base64", response_model=UploadResponse)
async def upload_base64(
    request: Base64UploadRequest,
    current_user: CurrentUser,
) -> UploadResponse:
    """Upload a base64 encoded image and return its URL."""
    
    try:
        # Parse base64 data
        if "," in request.data:
            header, encoded = request.data.split(",", 1)
            if "image/png" in header:
                ext = "png"
            elif "image/jpeg" in header or "image/jpg" in header:
                ext = "jpg"
            elif "image/webp" in header:
                ext = "webp"
            elif "image/gif" in header:
                ext = "gif"
            else:
                ext = "png"
        else:
            encoded = request.data
            ext = "png"
        
        # Decode
        content = base64.b64decode(encoded)
        
        # Validate size
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Файл слишком большой. Максимум {MAX_IMAGE_SIZE // 1024 // 1024}MB"
            )
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = UPLOAD_DIR / filename
        
        # Save file
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        
        # Build URL
        url = f"{settings.WEBAPP_URL}/static/uploads/{filename}"
        
        logger.info(f"Base64 file uploaded | user_id={current_user.id}, filename={filename}")
        
        return UploadResponse(url=url, filename=filename, file_type="image")
        
    except Exception as e:
        logger.error(f"Base64 upload failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка загрузки: {str(e)}"
        )

