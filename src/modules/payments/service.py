"""Payment service for business logic."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration, Payment as YooPayment

from src.config import settings
from src.core.exceptions import NotFoundError, PaymentError
from src.modules.payments.models import Payment
from src.modules.payments.repository import BalanceHistoryRepository, PaymentRepository
from src.modules.user.repository import UserRepository
from src.shared.enums import BalanceOperationType, PaymentStatus
from src.shared.logger import logger


class PaymentService:
    """Service for payment-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.user_repo = UserRepository(session)
        self.balance_history_repo = BalanceHistoryRepository(session)

        # Configure YooKassa
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET.get_secret_value()

    async def create_payment(
        self,
        user_id: int,
        amount: int,
        tokens: int,
        package_name: str,
    ) -> tuple[Payment, str]:
        """
        Create new payment.

        Args:
            user_id: User ID
            amount: Payment amount in USD
            tokens: Tokens to credit
            package_name: Human-readable package name

        Returns:
            tuple of (Payment, confirmation_url)
        """
        # Create payment in database
        payment = await self.payment_repo.create(
            user_id=user_id,
            amount=amount,
            tokens=tokens,
        )

        # Create YooKassa payment
        try:
            yoo_payment = YooPayment.create({
                "amount": {
                    "value": f"{amount}.00",
                    "currency": "USD",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.YOOKASSA_RETURN_URL,
                },
                "capture": True,
                "description": f"Пакет «{package_name}» — {tokens} токенов",
                "metadata": {
                    "payment_id": str(payment.id),
                    "user_id": user_id,
                    "package_name": package_name,
                },
            }, uuid.uuid4())

            # Update payment with YooKassa data
            await self.payment_repo.update(
                payment,
                yookassa_id=yoo_payment.id,
                yookassa_status=yoo_payment.status,
                confirmation_url=yoo_payment.confirmation.confirmation_url,
            )

            logger.info(
                f"YooKassa payment created | payment_id={payment.id}, "
                f"yookassa_id={yoo_payment.id}, package={package_name}"
            )

            return payment, yoo_payment.confirmation.confirmation_url

        except Exception as e:
            logger.error(f"YooKassa payment creation failed | error={e}")
            await self.payment_repo.mark_as_failed(payment.id)
            raise PaymentError(f"Не удалось создать платёж: {e}")

    async def get_payment(self, payment_id: uuid.UUID) -> Payment | None:
        """Get payment by ID."""
        return await self.payment_repo.get_by_id(payment_id)

    async def check_payment_status(self, payment: Payment) -> dict:
        """
        Check payment status in YooKassa and update if needed.

        Returns:
            dict with status info and new_balance if successful
        """
        if payment.status == PaymentStatus.SUCCESS:
            return {
                "success": True,
                "status": "success",
                "new_balance": None,
            }

        if payment.status in (PaymentStatus.FAILED, PaymentStatus.CANCELLED):
            return {
                "success": False,
                "status": payment.status.value,
            }

        if not payment.yookassa_id:
            return {
                "success": False,
                "status": "no_yookassa_id",
            }

        # Check status in YooKassa
        try:
            yoo_payment = YooPayment.find_one(payment.yookassa_id)

            logger.debug(
                f"YooKassa status check | payment_id={payment.id}, "
                f"status={yoo_payment.status}"
            )

            if yoo_payment.status == "succeeded":
                # Payment successful - add tokens
                new_balance = await self._process_successful_payment(payment)

                return {
                    "success": True,
                    "status": "success",
                    "new_balance": new_balance,
                }

            elif yoo_payment.status == "canceled":
                await self.payment_repo.mark_as_failed(
                    payment.id,
                    yookassa_status=yoo_payment.status,
                )
                return {
                    "success": False,
                    "status": "canceled",
                }

            else:
                # Still pending
                return {
                    "success": False,
                    "status": yoo_payment.status,
                }

        except Exception as e:
            logger.error(f"YooKassa status check failed | error={e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
            }

    async def _process_successful_payment(self, payment: Payment) -> int:
        """Process successful payment - add tokens to user."""
        # Mark payment as paid
        await self.payment_repo.mark_as_paid(payment.id, yookassa_status="succeeded")

        # Add tokens to user balance
        new_balance = await self.user_repo.update_balance(
            payment.user_id,
            payment.tokens,
        )

        # Record in history
        await self.balance_history_repo.create(
            user_id=payment.user_id,
            amount=payment.tokens,
            balance_after=new_balance,
            operation_type=BalanceOperationType.DEPOSIT,
            description=f"Пополнение — ${payment.amount} ({payment.tokens} токенов)",
            reference_id=str(payment.id),
        )

        logger.info(
            f"Payment processed | payment_id={payment.id}, "
            f"tokens={payment.tokens}, new_balance={new_balance}"
        )

        return new_balance

    async def get_user_payments(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Payment]:
        """Get user's payment history."""
        return await self.payment_repo.get_user_payments(user_id, offset, limit)

    async def get_stats(self) -> dict:
        """Get payment statistics."""
        return await self.payment_repo.get_stats()

