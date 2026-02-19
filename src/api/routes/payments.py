"""Payment routes."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import CurrentUser, SessionDep
from src.api.schemas.payment import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentCheckResponse,
    PaymentListResponse,
    PaymentPackageItem,
    PaymentPackagesResponse,
    PaymentResponse,
)
from src.core.exceptions import PaymentError
from src.modules.payments.service import PaymentService
from src.shared.constants import PAYMENT_PACKAGES_USD, PAYMENT_PACKAGES_RUB, PAYMENT_CURRENCY
from src.shared.enums import PaymentStatus

router = APIRouter()

@router.get("/packages", response_model=PaymentPackagesResponse)
async def get_payment_packages(currency: str = "USD") -> PaymentPackagesResponse:
    """Get available payment packages (public endpoint)."""
    packages = PAYMENT_PACKAGES_RUB if currency.upper() == "RUB" else PAYMENT_PACKAGES_USD
    return PaymentPackagesResponse(
        packages=[PaymentPackageItem(**pkg) for pkg in packages],
        currency=currency.upper(),
    )

@router.post("", response_model=PaymentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PaymentCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> PaymentCreateResponse:
    """Create new payment by package ID."""
    currency = request.currency.upper() if request.currency else "USD"
    packages = PAYMENT_PACKAGES_RUB if currency == "RUB" else PAYMENT_PACKAGES_USD

    package = next(
        (pkg for pkg in packages if pkg["id"] == request.package_id),
        None,
    )
    if not package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный пакет: {request.package_id}",
        )

    service = PaymentService(session)

    try:
        payment, confirmation_url = await service.create_payment(
            user_id=current_user.id,
            amount=package["amount"],
            tokens=package["tokens"],
            package_name=package["name"],
            currency=currency,
        )

        return PaymentCreateResponse(
            payment_id=payment.id,
            amount=payment.amount,
            tokens=payment.tokens,
            package_name=package["name"],
            confirmation_url=confirmation_url,
        )

    except PaymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )

@router.post("/{payment_id}/check", response_model=PaymentCheckResponse)
async def check_payment(
    payment_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> PaymentCheckResponse:
    """Check payment status."""
    service = PaymentService(session)

    payment = await service.get_payment(payment_id)

    if not payment or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Платёж не найден",
        )

    result = await service.check_payment_status(payment)

    if result["success"]:
        return PaymentCheckResponse(
            payment_id=payment_id,
            status=PaymentStatus.SUCCESS,
            success=True,
            new_balance=result["new_balance"],
            message="Оплата прошла успешно!",
        )
    else:
        status_messages = {
            "pending": "Ожидание оплаты",
            "waiting_for_capture": "Ожидание оплаты",
            "canceled": "Платёж отменён",
            "error": "Ошибка проверки платежа",
        }

        return PaymentCheckResponse(
            payment_id=payment_id,
            status=PaymentStatus.PENDING if result["status"] == "pending" else PaymentStatus.FAILED,
            success=False,
            message=status_messages.get(result["status"], f"Статус: {result['status']}"),
        )

@router.get("", response_model=PaymentListResponse)
async def get_payments(
    current_user: CurrentUser,
    session: SessionDep,
    offset: int = 0,
    limit: int = 50,
) -> PaymentListResponse:
    """Get user payment history."""
    service = PaymentService(session)
    payments = await service.get_user_payments(current_user.id, offset, limit)

    from src.modules.payments.repository import PaymentRepository
    repo = PaymentRepository(session)
    all_payments = await repo.get_user_payments(current_user.id, 0, 1000)
    total = len(all_payments)

    return PaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
    )
