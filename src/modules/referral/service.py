"""Referral service for business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.referral.repository import ReferralRepository
from src.modules.user.models import User


class ReferralService:
    """Service for referral-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.referral_repo = ReferralRepository(session)

    async def get_referral_link(self, user: User, bot_username: str) -> str:
        """Generate referral link for user."""
        return f"https://t.me/{bot_username}?start={user.referral_code}"

    async def get_referral_stats(self, user_id: int) -> dict:
        """Get referral statistics for user."""
        return await self.referral_repo.get_stats(user_id)

    async def get_referrals(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list:
        """Get user's referrals."""
        return await self.referral_repo.get_referrals_by_referrer(
            user_id, offset, limit
        )

    async def validate_referral_code(self, code: str, user_id: int) -> User | None:
        """
        Validate referral code.
        
        Returns referrer User if valid, None otherwise.
        """
        referrer = await self.referral_repo.get_referrer_by_code(code)
        
        if not referrer:
            return None
        
        # Can't refer yourself
        if referrer.id == user_id:
            return None
        
        # Referrer can't be banned
        if referrer.is_banned:
            return None
        
        return referrer

    @property
    def referral_bonus(self) -> int:
        """Get current referral bonus amount."""
        return settings.REFERRAL_BONUS
