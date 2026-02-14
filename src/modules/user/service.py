"""User service for business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.exceptions import NotFoundError, UserBannedError
from src.modules.payments.repository import BalanceHistoryRepository
from src.modules.referral.repository import ReferralRepository
from src.modules.user.models import User
from src.modules.user.repository import UserRepository
from src.shared.enums import BalanceOperationType
from src.shared.logger import logger


class UserService:
    """Service for user-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.referral_repo = ReferralRepository(session)
        self.balance_history_repo = BalanceHistoryRepository(session)

    async def get_or_create_user(
        self,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
        referral_code: str | None = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        
        Returns:
            tuple of (User, is_new_user)
        """
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        
        if user:
            # Update user info if changed
            updates = {}
            if user.first_name != first_name:
                updates["first_name"] = first_name
            if user.last_name != last_name:
                updates["last_name"] = last_name
            if user.username != username:
                updates["username"] = username
            
            if updates:
                user = await self.user_repo.update(user, **updates)
                logger.debug(f"User info updated | telegram_id={telegram_id}")
            
            return user, False
        
        # Check if admin
        is_admin = telegram_id in settings.admin_ids_list
        
        # Create new user with welcome bonus
        user = await self.user_repo.create(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            balance=settings.WELCOME_BONUS,
            is_admin=is_admin,
        )
        
        # Record welcome bonus
        await self.balance_history_repo.create(
            user_id=user.id,
            amount=settings.WELCOME_BONUS,
            balance_after=user.balance,
            operation_type=BalanceOperationType.WELCOME,
            description="Приветственный бонус",
        )
        
        # Process referral if provided
        if referral_code:
            await self._process_referral(user, referral_code)
        
        logger.info(
            f"New user registered | telegram_id={telegram_id}, "
            f"is_admin={is_admin}, referral={referral_code or 'none'}"
        )
        
        return user, True

    async def _process_referral(self, user: User, referral_code: str) -> None:
        """Process referral code for new user."""
        referrer = await self.referral_repo.get_referrer_by_code(referral_code)
        
        if not referrer:
            logger.warning(f"Invalid referral code | code={referral_code}")
            return
        
        if referrer.id == user.id:
            logger.warning(f"Self-referral attempt | user_id={user.id}")
            return
        
        if referrer.is_banned:
            logger.warning(f"Banned referrer | referrer_id={referrer.id}")
            return
        
        # Create referral relationship
        referral = await self.referral_repo.create(
            referrer_id=referrer.id,
            referred_id=user.id,
            bonus_amount=settings.REFERRAL_BONUS,
        )
        
        # Give bonus to referrer
        new_balance = await self.user_repo.update_balance(
            referrer.id,
            settings.REFERRAL_BONUS,
        )
        
        # Mark bonus as given
        await self.referral_repo.mark_bonus_given(
            referral.id,
            settings.REFERRAL_BONUS,
        )
        
        # Record in history
        await self.balance_history_repo.create(
            user_id=referrer.id,
            amount=settings.REFERRAL_BONUS,
            balance_after=new_balance,
            operation_type=BalanceOperationType.REFERRAL,
            description=f"Бонус за приглашение {user.display_name}",
            reference_id=str(referral.id),
        )
        
        logger.info(
            f"Referral bonus given | referrer_id={referrer.id}, "
            f"referred_id={user.id}, bonus={settings.REFERRAL_BONUS}"
        )

    async def get_user(self, user_id: int) -> User:
        """Get user by internal ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь", user_id)
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        """Get user by Telegram ID."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise NotFoundError("Пользователь", telegram_id)
        return user

    async def check_user_active(self, user: User) -> None:
        """Check if user is not banned."""
        if user.is_banned:
            raise UserBannedError(user.id)

    async def update_balance(
        self,
        user_id: int,
        amount: int,
        operation_type: BalanceOperationType,
        description: str,
        reference_id: str | None = None,
    ) -> int:
        """
        Update user balance and record in history.
        
        Returns new balance.
        """
        new_balance = await self.user_repo.update_balance(user_id, amount)
        
        await self.balance_history_repo.create(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            operation_type=operation_type,
            description=description,
            reference_id=reference_id,
        )
        
        return new_balance

    async def get_balance_history(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list:
        """Get user balance history."""
        return await self.balance_history_repo.get_user_history(
            user_id, offset, limit
        )

    async def get_referral_info(self, user: User) -> dict:
        """Get user's referral information."""
        stats = await self.referral_repo.get_stats(user.id)
        referrals = await self.referral_repo.get_referrals_by_referrer(
            user.id, limit=10
        )
        
        return {
            "referral_code": user.referral_code,
            "referral_link": f"https://t.me/{settings.WEBAPP_URL.split('/')[-1]}?start={user.referral_code}",
            "total_referrals": stats["total_referrals"],
            "total_bonus_earned": stats["total_bonus_earned"],
            "recent_referrals": [
                {
                    "id": r.referred.id,
                    "name": r.referred.display_name,
                    "date": r.created_at.isoformat(),
                    "bonus": r.bonus_amount,
                }
                for r in referrals
            ],
        }

    # === Admin methods ===

    async def get_all_users(
        self,
        offset: int = 0,
        limit: int = 50,
        search: str | None = None,
        is_banned: bool | None = None,
    ) -> tuple[list[User], int]:
        """Get all users with pagination for admin."""
        users = await self.user_repo.get_all(offset, limit, search, is_banned)
        total = await self.user_repo.count(search, is_banned)
        return users, total

    async def ban_user(self, user_id: int) -> None:
        """Ban user."""
        user = await self.get_user(user_id)
        if user.is_admin:
            raise ValueError("Нельзя заблокировать администратора")
        await self.user_repo.ban(user_id)

    async def unban_user(self, user_id: int) -> None:
        """Unban user."""
        await self.user_repo.unban(user_id)

    async def set_balance(
        self,
        user_id: int,
        balance: int,
        admin_id: int,
    ) -> int:
        """Set user balance (admin action)."""
        user = await self.get_user(user_id)
        old_balance = user.balance
        diff = balance - old_balance
        
        await self.user_repo.set_balance(user_id, balance)
        
        await self.balance_history_repo.create(
            user_id=user_id,
            amount=diff,
            balance_after=balance,
            operation_type=BalanceOperationType.ADMIN,
            description=f"Изменение баланса администратором (ID: {admin_id})",
        )
        
        logger.info(
            f"Admin balance change | user_id={user_id}, "
            f"old={old_balance}, new={balance}, admin_id={admin_id}"
        )
        
        return balance

    async def get_stats(self) -> dict:
        """Get user statistics for admin."""
        return await self.user_repo.get_stats()
