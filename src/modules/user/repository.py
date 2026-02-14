"""User repository for database operations."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.user.models import User
from src.shared.logger import logger


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by internal ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
        balance: int = 0,
        is_admin: bool = False,
    ) -> User:
        """Create new user."""
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            balance=balance,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info(f"User created | telegram_id={telegram_id}, balance={balance}")
        return user

    async def update(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_balance(self, user_id: int, amount: int) -> int:
        """
        Update user balance atomically.
        Returns new balance.
        """
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=User.balance + amount)
            .returning(User.balance)
        )
        new_balance = result.scalar_one()
        await self.session.flush()
        
        logger.debug(f"Balance updated | user_id={user_id}, change={amount}, new_balance={new_balance}")
        return new_balance

    async def set_balance(self, user_id: int, balance: int) -> int:
        """Set user balance to specific value."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=balance)
        )
        await self.session.flush()
        
        logger.debug(f"Balance set | user_id={user_id}, balance={balance}")
        return balance

    async def ban(self, user_id: int) -> None:
        """Ban user."""
        await self.session.execute(
            update(User).where(User.id == user_id).values(is_banned=True)
        )
        await self.session.flush()
        logger.info(f"User banned | user_id={user_id}")

    async def unban(self, user_id: int) -> None:
        """Unban user."""
        await self.session.execute(
            update(User).where(User.id == user_id).values(is_banned=False)
        )
        await self.session.flush()
        logger.info(f"User unbanned | user_id={user_id}")

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        search: str | None = None,
        is_banned: bool | None = None,
    ) -> list[User]:
        """Get all users with optional filtering."""
        query = select(User)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.username.ilike(search_pattern)) |
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern)) |
                (User.telegram_id.cast(str).ilike(search_pattern))
            )
        
        if is_banned is not None:
            query = query.where(User.is_banned == is_banned)
        
        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        search: str | None = None,
        is_banned: bool | None = None,
    ) -> int:
        """Count users with optional filtering."""
        query = select(func.count(User.id))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.username.ilike(search_pattern)) |
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern))
            )
        
        if is_banned is not None:
            query = query.where(User.is_banned == is_banned)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_stats(self) -> dict:
        """Get user statistics."""
        total = await self.session.execute(select(func.count(User.id)))
        banned = await self.session.execute(
            select(func.count(User.id)).where(User.is_banned == True)
        )
        total_balance = await self.session.execute(select(func.sum(User.balance)))
        
        return {
            "total_users": total.scalar_one(),
            "banned_users": banned.scalar_one(),
            "total_balance": total_balance.scalar_one() or 0,
        }

    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if user exists by Telegram ID."""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one() > 0
