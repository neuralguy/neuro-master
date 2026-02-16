"""Payment and balance history repository."""

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.payments.models import BalanceHistory, Payment
from src.shared.enums import BalanceOperationType, PaymentStatus
from src.shared.logger import logger


class PaymentRepository:
    """Repository for Payment database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        amount: int,
        tokens: int,
    ) -> Payment:
        """Create new payment."""
        payment = Payment(
            user_id=user_id,
            amount=amount,
            tokens=tokens,
            status=PaymentStatus.PENDING,
        )
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)

        logger.info(f"Payment created | id={payment.id}, user_id={user_id}, amount={amount}")
        return payment

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        """Get payment by ID."""
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_lava_id(self, lava_id: str) -> Payment | None:
        """Get payment by Lava.top ID."""
        result = await self.session.execute(
            select(Payment).where(Payment.lava_id == lava_id)
        )
        return result.scalar_one_or_none()

    async def update(self, payment: Payment, **kwargs) -> Payment:
        """Update payment fields."""
        for key, value in kwargs.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def mark_as_paid(
        self,
        payment_id: uuid.UUID,
        lava_status: str | None = None,
    ) -> None:
        """Mark payment as successful."""
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=PaymentStatus.SUCCESS,
                lava_status=lava_status,
                paid_at=datetime.utcnow(),
            )
        )
        await self.session.flush()
        logger.info(f"Payment marked as paid | id={payment_id}")

    async def mark_as_failed(
        self,
        payment_id: uuid.UUID,
        lava_status: str | None = None,
    ) -> None:
        """Mark payment as failed."""
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=PaymentStatus.FAILED,
                lava_status=lava_status,
            )
        )
        await self.session.flush()
        logger.info(f"Payment marked as failed | id={payment_id}")

    async def get_user_payments(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        status: PaymentStatus | None = None,
    ) -> list[Payment]:
        """Get user payments with optional filtering."""
        query = select(Payment).where(Payment.user_id == user_id)

        if status:
            query = query.where(Payment.status == status)

        query = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_payments(
        self,
        offset: int = 0,
        limit: int = 50,
        status: PaymentStatus | None = None,
    ) -> list[Payment]:
        """Get all payments for admin."""
        query = select(Payment)

        if status:
            query = query.where(Payment.status == status)

        query = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_stats(self) -> dict:
        """Get payment statistics."""
        total_result = await self.session.execute(
            select(
                func.count(Payment.id),
                func.sum(Payment.amount),
            ).where(Payment.status == PaymentStatus.SUCCESS)
        )
        total_count, total_amount = total_result.one()

        pending_result = await self.session.execute(
            select(func.count(Payment.id))
            .where(Payment.status == PaymentStatus.PENDING)
        )
        pending_count = pending_result.scalar_one()

        return {
            "total_payments": total_count or 0,
            "total_amount": total_amount or 0,
            "pending_payments": pending_count,
        }


class BalanceHistoryRepository:
    """Repository for BalanceHistory database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        amount: int,
        balance_after: int,
        operation_type: BalanceOperationType,
        description: str,
        reference_id: str | None = None,
    ) -> BalanceHistory:
        """Create balance history record."""
        record = BalanceHistory(
            user_id=user_id,
            amount=amount,
            balance_after=balance_after,
            operation_type=operation_type,
            description=description,
            reference_id=reference_id,
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)

        logger.debug(
            f"Balance history created | user_id={user_id}, "
            f"amount={amount}, type={operation_type.value}"
        )
        return record

    async def get_user_history(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
        operation_type: BalanceOperationType | None = None,
    ) -> list[BalanceHistory]:
        """Get user balance history."""
        query = select(BalanceHistory).where(BalanceHistory.user_id == user_id)

        if operation_type:
            query = query.where(BalanceHistory.operation_type == operation_type)

        query = query.order_by(BalanceHistory.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_history(
        self,
        user_id: int,
        operation_type: BalanceOperationType | None = None,
    ) -> int:
        """Count user balance history records."""
        query = select(func.count(BalanceHistory.id)).where(
            BalanceHistory.user_id == user_id
        )

        if operation_type:
            query = query.where(BalanceHistory.operation_type == operation_type)

        result = await self.session.execute(query)
        return result.scalar_one()
