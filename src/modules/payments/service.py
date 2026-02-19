"""Payment service for business logic."""

import uuid
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.exceptions import NotFoundError, PaymentError
from src.modules.payments.models import Payment
from src.modules.payments.repository import BalanceHistoryRepository, PaymentRepository
from src.modules.user.repository import UserRepository
from src.shared.constants import PAYMENT_PACKAGES
from src.shared.enums import BalanceOperationType, PaymentStatus
from src.shared.logger import logger


class PaymentService:
    """Service for payment-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.user_repo = UserRepository(session)
        self.balance_history_repo = BalanceHistoryRepository(session)

        # Lava.top configuration
        self.lava_api_url = settings.LAVA_API_URL
        self.lava_api_key = settings.LAVA_API_KEY.get_secret_value()
        self.lava_currency = settings.LAVA_CURRENCY

    async def _lava_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make request to Lava.top API."""
        url = f"{self.lava_api_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.lava_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method=method, url=url, headers=headers, **kwargs)
        if response.status_code not in (200, 201):
            logger.error(f"Lava.top API error | status={response.status_code}, body={response.text}")
            raise PaymentError(f"Lava.top API error: {response.status_code}")
        return response.json()

    async def create_payment(self, user_id: int, amount: int, tokens: int, package_name: str) -> tuple[Payment, str]:
        """
        Create new payment via Lava.top.

        Args:
            user_id: User ID
            amount: Payment amount in USD
            tokens: Tokens to credit
            package_name: Human-readable package name

        Returns:
            tuple of (Payment, payment_url)
        """
        # Find offer_id for this package
        package = next(
            (pkg for pkg in PAYMENT_PACKAGES
             if pkg["name"] == package_name and pkg["amount"] == amount),
            None,
        )
        if not package or not package.get("offer_id"):
            raise PaymentError(f"No Lava.top offer_id configured for package: {package_name}")

        # Create payment in database
        payment = await self.payment_repo.create(user_id=user_id, amount=amount, tokens=tokens)

        # Create Lava.top invoice
        try:
            # Get user for email placeholder
            user = await self.user_repo.get_by_id(user_id)
            buyer_email = f"user_{user.telegram_id}@noreply.local"

            result = await self._lava_request(
                "POST",
                "/api/v3/invoice",
                json={
                    "offerId": package["offer_id"],
                    "email": buyer_email,
                    "currency": self.lava_currency,
                    "buyerLanguage": "RU",
                },
            )

            lava_id = result.get("id", "")
            payment_url = result.get("paymentUrl", "")
            lava_status = result.get("status", "created")

            # Update payment with Lava.top data
            await self.payment_repo.update(
                payment, lava_id=lava_id, lava_status=lava_status, confirmation_url=payment_url,
            )

            logger.info(
                f"Lava.top payment created | payment_id={payment.id}, "
                f"lava_id={lava_id}, package={package_name}"
            )

            return payment, payment_url

        except PaymentError:
            await self.payment_repo.mark_as_failed(payment.id)
            raise
        except Exception as e:
            logger.error(f"Lava.top payment creation failed | error={e}")
            await self.payment_repo.mark_as_failed(payment.id)
            raise PaymentError(f"Не удалось создать платёж: {e}")

    async def get_payment(self, payment_id: uuid.UUID) -> Payment | None:
        """Get payment by ID."""
        return await self.payment_repo.get_by_id(payment_id)

    async def check_payment_status(self, payment: Payment) -> dict:
        """
        Check payment status via Lava.top API and update if needed.

        Returns:
            dict with status info and new_balance if successful
        """
        if payment.status == PaymentStatus.SUCCESS:
            return {"success": True, "status": "success", "new_balance": None}

        if payment.status in (PaymentStatus.FAILED, PaymentStatus.CANCELLED):
            return {"success": False, "status": payment.status.value}

        if not payment.lava_id:
            return {"success": False, "status": "no_lava_id"}

        # Check status in Lava.top
        try:
            result = await self._lava_request("GET", f"/api/v3/invoice/{payment.lava_id}")
            lava_status = result.get("status", "").lower()

            logger.debug(
                f"Lava.top status check | payment_id={payment.id}, "
                f"status={lava_status}"
            )

            if lava_status in ("succeeded", "completed", "paid"):
                new_balance = await self._process_successful_payment(payment)
                return {"success": True, "status": "success", "new_balance": new_balance}

            elif lava_status in ("canceled", "failed", "expired"):
                await self.payment_repo.mark_as_failed(payment.id, lava_status=lava_status)
                return {"success": False, "status": lava_status}

            else:
                return {"success": False, "status": lava_status or "pending"}

        except PaymentError:
            return {"success": False, "status": "error", "error": "Lava.top API error"}
        except Exception as e:
            logger.error(f"Lava.top status check failed | error={e}")
            return {"success": False, "status": "error", "error": str(e)}

    async def process_webhook(self, payload: dict) -> Payment | None:
        """
        Process Lava.top webhook notification.

        Args:
            payload: Webhook JSON payload

        Returns:
            Updated Payment or None
        """
        lava_id = payload.get("invoiceId") or payload.get("id")
        status = (payload.get("status") or "").lower()

        if not lava_id:
            logger.warning(f"Lava.top webhook missing invoiceId | payload={payload}")
            return None

        payment = await self.payment_repo.get_by_lava_id(lava_id)
        if not payment:
            logger.warning(f"Lava.top webhook payment not found | lava_id={lava_id}")
            return None

        if payment.status == PaymentStatus.SUCCESS:
            logger.debug(f"Lava.top webhook duplicate | lava_id={lava_id}")
            return payment

        logger.info(
            f"Lava.top webhook | lava_id={lava_id}, "
            f"status={status}, payment_id={payment.id}"
        )

        if status in ("succeeded", "completed", "paid"):
            await self._process_successful_payment(payment)
        elif status in ("canceled", "failed", "expired"):
            await self.payment_repo.mark_as_failed(payment.id, lava_status=status)

        return payment

    async def _process_successful_payment(self, payment: Payment) -> int:
        """Process successful payment - add tokens to user."""
        await self.payment_repo.mark_as_paid(payment.id, lava_status="succeeded")

        new_balance = await self.user_repo.update_balance(payment.user_id, payment.tokens)

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

    async def get_user_payments(self, user_id: int, offset: int = 0, limit: int = 50) -> list[Payment]:
        """Get user payment history."""
        return await self.payment_repo.get_user_payments(user_id, offset, limit)

    async def get_stats(self) -> dict:
        """Get payment statistics."""
        return await self.payment_repo.get_stats()
