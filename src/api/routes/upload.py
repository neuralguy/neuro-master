"""Upload routes."""

import uuid
import base64
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from src.api.dependencies import CurrentUser
from src.config import settings, STORAGE_DIR, STORAGE_DIR
from src.shared.logger import logger

router = APIRouter()

UPLOAD_DIR = STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class UploadResponse(BaseModel):
    url: str
    filename: str


class Base64UploadRequest(BaseModel):
    data: str  # base64 encoded image with data:image/...;base64, prefix
    filename: str | None = None


@router.post("/file", response_model=UploadResponse)
async def upload_file(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Upload a file and return its URL."""
    
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла: {file.content_type}. Разрешены: {', '.join(ALLOWED_TYPES)}"
        )
    
    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Build URL
    url = f"{settings.WEBAPP_URL}/static/uploads/{filename}"
    
    logger.info(f"File uploaded | user_id={current_user.id}, filename={filename}")
    
    return UploadResponse(url=url, filename=filename)


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
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE // 1024 // 1024}MB"
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
        
        return UploadResponse(url=url, filename=filename)
        
    except Exception as e:
        logger.error(f"Base64 upload failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка загрузки: {str(e)}"
        )

