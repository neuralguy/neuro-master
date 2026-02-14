"""Referral repository for database operations."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.referral.models import Referral
from src.modules.user.models import User
from src.shared.logger import logger


class ReferralRepository:
    """Repository for Referral database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        referrer_id: int,
        referred_id: int,
        bonus_amount: int = 0,
    ) -> Referral:
        """Create new referral relationship."""
        referral = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id,
            bonus_amount=bonus_amount,
            bonus_given=False,
        )
        self.session.add(referral)
        await self.session.flush()
        await self.session.refresh(referral)
        
        logger.info(
            f"Referral created | referrer_id={referrer_id}, referred_id={referred_id}"
        )
        return referral

    async def get_by_referred_id(self, referred_id: int) -> Referral | None:
        """Get referral by referred user ID."""
        result = await self.session.execute(
            select(Referral)
            .where(Referral.referred_id == referred_id)
            .options(selectinload(Referral.referrer))
        )
        return result.scalar_one_or_none()

    async def get_referrals_by_referrer(
        self,
        referrer_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Referral]:
        """Get all referrals made by user."""
        result = await self.session.execute(
            select(Referral)
            .where(Referral.referrer_id == referrer_id)
            .options(selectinload(Referral.referred))
            .order_by(Referral.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_referrals(self, referrer_id: int) -> int:
        """Count referrals made by user."""
        result = await self.session.execute(
            select(func.count(Referral.id))
            .where(Referral.referrer_id == referrer_id)
        )
        return result.scalar_one()

    async def mark_bonus_given(self, referral_id: int, bonus_amount: int) -> None:
        """Mark referral bonus as given."""
        await self.session.execute(
            update(Referral)
            .where(Referral.id == referral_id)
            .values(bonus_given=True, bonus_amount=bonus_amount)
        )
        await self.session.flush()
        
        logger.info(f"Referral bonus marked | referral_id={referral_id}, amount={bonus_amount}")

    async def get_referrer_by_code(self, referral_code: str) -> User | None:
        """Get referrer user by referral code (ref_{telegram_id})."""
        if not referral_code.startswith("ref_"):
            return None
        
        try:
            telegram_id = int(referral_code[4:])
        except ValueError:
            return None
        
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def is_already_referred(self, user_id: int) -> bool:
        """Check if user was already referred."""
        result = await self.session.execute(
            select(func.count(Referral.id))
            .where(Referral.referred_id == user_id)
        )
        return result.scalar_one() > 0

    async def get_stats(self, referrer_id: int) -> dict:
        """Get referral statistics for user."""
        total = await self.count_referrals(referrer_id)
        
        bonus_result = await self.session.execute(
            select(func.sum(Referral.bonus_amount))
            .where(Referral.referrer_id == referrer_id)
            .where(Referral.bonus_given == True)
        )
        total_bonus = bonus_result.scalar_one() or 0
        
        return {
            "total_referrals": total,
            "total_bonus_earned": total_bonus,
        }
