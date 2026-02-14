"""Gallery repository."""

import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.gallery.models import GalleryItem
from src.shared.logger import logger


class GalleryRepository:
    """Repository for GalleryItem database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        generation_id: uuid.UUID,
        file_path: str,
        file_type: str,
        thumbnail_path: str | None = None,
    ) -> GalleryItem:
        """Create gallery item."""
        item = GalleryItem(
            user_id=user_id,
            generation_id=generation_id,
            file_path=file_path,
            file_type=file_type,
            thumbnail_path=thumbnail_path,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        
        logger.debug(f"Gallery item created | id={item.id}, user_id={user_id}")
        return item

    async def get_by_id(self, item_id: uuid.UUID) -> GalleryItem | None:
        """Get gallery item by ID."""
        result = await self.session.execute(
            select(GalleryItem)
            .where(GalleryItem.id == item_id)
            .options(selectinload(GalleryItem.generation))
        )
        return result.scalar_one_or_none()

    async def get_user_gallery(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        file_type: str | None = None,
        favorites_only: bool = False,
    ) -> list[GalleryItem]:
        """Get user's gallery items."""
        query = select(GalleryItem).where(GalleryItem.user_id == user_id)
        
        if file_type:
            query = query.where(GalleryItem.file_type == file_type)
        
        if favorites_only:
            query = query.where(GalleryItem.is_favorite == True)
        
        query = (
            query
            .order_by(GalleryItem.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(GalleryItem.generation))
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_gallery(
        self,
        user_id: int,
        file_type: str | None = None,
    ) -> int:
        """Count user's gallery items."""
        query = select(func.count(GalleryItem.id)).where(GalleryItem.user_id == user_id)
        
        if file_type:
            query = query.where(GalleryItem.file_type == file_type)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def toggle_favorite(self, item_id: uuid.UUID) -> bool:
        """Toggle favorite status. Returns new status."""
        item = await self.get_by_id(item_id)
        if not item:
            return False
        
        new_status = not item.is_favorite
        await self.session.execute(
            update(GalleryItem)
            .where(GalleryItem.id == item_id)
            .values(is_favorite=new_status)
        )
        await self.session.flush()
        
        return new_status

    async def delete(self, item_id: uuid.UUID) -> bool:
        """Delete gallery item."""
        result = await self.session.execute(
            delete(GalleryItem).where(GalleryItem.id == item_id)
        )
        await self.session.flush()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.debug(f"Gallery item deleted | id={item_id}")
        
        return deleted

    async def delete_user_gallery(self, user_id: int) -> int:
        """Delete all user's gallery items. Returns count deleted."""
        result = await self.session.execute(
            delete(GalleryItem).where(GalleryItem.user_id == user_id)
        )
        await self.session.flush()
        
        logger.info(f"User gallery cleared | user_id={user_id}, count={result.rowcount}")
        return result.rowcount
