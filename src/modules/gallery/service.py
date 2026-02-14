"""Gallery service."""

import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.modules.gallery.models import GalleryItem
from src.modules.gallery.repository import GalleryRepository
from src.shared.logger import logger


class GalleryService:
    """Service for gallery operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GalleryRepository(session)

    async def get_item(self, item_id: uuid.UUID, user_id: int) -> GalleryItem:
        """Get gallery item with ownership check."""
        item = await self.repo.get_by_id(item_id)
        
        if not item:
            raise NotFoundError("Элемент галереи", str(item_id))
        
        if item.user_id != user_id:
            raise NotFoundError("Элемент галереи", str(item_id))
        
        return item

    async def get_user_gallery(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        file_type: str | None = None,
        favorites_only: bool = False,
    ) -> tuple[list[GalleryItem], int]:
        """Get user's gallery with total count."""
        items = await self.repo.get_user_gallery(
            user_id, offset, limit, file_type, favorites_only
        )
        total = await self.repo.count_user_gallery(user_id, file_type)
        
        return items, total

    async def toggle_favorite(self, item_id: uuid.UUID, user_id: int) -> bool:
        """Toggle favorite status. Returns new status."""
        await self.get_item(item_id, user_id)  # Check ownership
        return await self.repo.toggle_favorite(item_id)

    async def delete_item(self, item_id: uuid.UUID, user_id: int) -> None:
        """Delete gallery item and associated file."""
        item = await self.get_item(item_id, user_id)
        
        # Delete file from storage
        if item.file_path:
            try:
                file_path = Path(item.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"File deleted | path={file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file | path={item.file_path}, error={e}")
        
        # Delete thumbnail if exists
        if item.thumbnail_path:
            try:
                thumb_path = Path(item.thumbnail_path)
                if thumb_path.exists():
                    thumb_path.unlink()
            except Exception:
                pass
        
        # Delete from database
        await self.repo.delete(item_id)
        
        logger.info(f"Gallery item deleted | id={item_id}, user_id={user_id}")
