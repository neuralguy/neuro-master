"""Admin routes."""

from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import AdminUser, SessionDep
from src.api.schemas.admin import (
    AdminPaymentListResponse,
    AdminStatsResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from src.api.schemas.common import MessageResponse
from src.api.schemas.model import AIModelCreateRequest, AIModelResponse, AIModelUpdateRequest
from src.api.schemas.payment import PaymentResponse
from src.modules.ai_models.service import AIModelService
from src.modules.generation.service import GenerationService
from src.modules.payments.repository import PaymentRepository
from src.modules.user.service import UserService
from src.shared.logger import logger

router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin_user: AdminUser,
    session: SessionDep,
) -> AdminStatsResponse:
    """Get admin dashboard statistics."""
    user_service = UserService(session)
    generation_service = GenerationService(session)
    payment_repo = PaymentRepository(session)
    
    user_stats = await user_service.get_stats()
    payment_stats = await payment_repo.get_stats()
    generation_stats = await generation_service.get_stats()
    
    return AdminStatsResponse(
        users=user_stats,
        payments=payment_stats,
        generations=generation_stats,
    )


@router.get("/users", response_model=AdminUserListResponse)
async def get_users(
    admin_user: AdminUser,
    session: SessionDep,
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    is_banned: bool | None = None,
) -> AdminUserListResponse:
    """Get all users."""
    user_service = UserService(session)
    users, total = await user_service.get_all_users(offset, limit, search, is_banned)
    
    from src.modules.generation.repository import GenerationRepository
    gen_repo = GenerationRepository(session)
    
    items = []
    for user in users:
        gen_count = await gen_repo.count_user_generations(user.id)
        items.append(AdminUserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            balance=user.balance,
            is_admin=user.is_admin,
            is_banned=user.is_banned,
            created_at=user.created_at,
            total_generations=gen_count,
        ))
    
    return AdminUserListResponse(items=items, total=total)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    request: AdminUserUpdateRequest,
    admin_user: AdminUser,
    session: SessionDep,
) -> AdminUserResponse:
    """Update user (ban/unban, change balance)."""
    user_service = UserService(session)
    
    try:
        user = await user_service.get_user(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if request.is_banned is not None:
        if request.is_banned:
            await user_service.ban_user(user_id)
        else:
            await user_service.unban_user(user_id)
    
    if request.balance is not None:
        await user_service.set_balance(user_id, request.balance, admin_user.id)
    
    user = await user_service.get_user(user_id)
    
    logger.info(f"Admin updated user | admin_id={admin_user.id}, user_id={user_id}")
    
    from src.modules.generation.repository import GenerationRepository
    gen_repo = GenerationRepository(session)
    gen_count = await gen_repo.count_user_generations(user.id)
    
    return AdminUserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        balance=user.balance,
        is_admin=user.is_admin,
        is_banned=user.is_banned,
        created_at=user.created_at,
        total_generations=gen_count,
    )


@router.get("/payments", response_model=AdminPaymentListResponse)
async def get_all_payments(
    admin_user: AdminUser,
    session: SessionDep,
    offset: int = 0,
    limit: int = 50,
) -> AdminPaymentListResponse:
    """Get all payments."""
    repo = PaymentRepository(session)
    payments = await repo.get_all_payments(offset, limit)
    all_payments = await repo.get_all_payments(0, 10000)
    total = len(all_payments)
    
    return AdminPaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
    )


@router.get("/models", response_model=list[AIModelResponse])
async def get_all_models(
    admin_user: AdminUser,
    session: SessionDep,
) -> list[AIModelResponse]:
    """Get all AI models (including disabled)."""
    service = AIModelService(session)
    models = await service.get_all_models()
    return [AIModelResponse.model_validate(m) for m in models]


@router.post("/models", response_model=AIModelResponse)
async def create_model(
    request: AIModelCreateRequest,
    admin_user: AdminUser,
    session: SessionDep,
) -> AIModelResponse:
    """Create new AI model."""
    service = AIModelService(session)

    try:
        model = await service.create_model(
            code=request.code,
            name=request.name,
            provider_model=request.provider_model,
            generation_type=request.generation_type,
            price_tokens=request.price_tokens,
            description=request.description,
            config=request.config,
            icon=request.icon,
        )
        logger.info(f"Admin created model | admin_id={admin_user.id}, model_code={model.code}")
        return AIModelResponse.model_validate(model)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/models/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: int,
    request: AIModelUpdateRequest,
    admin_user: AdminUser,
    session: SessionDep,
) -> AIModelResponse:
    """Update AI model."""
    service = AIModelService(session)

    try:
        updates = request.model_dump(exclude_none=True)
        model = await service.update_model(model_id, **updates)
        logger.info(f"Admin updated model | admin_id={admin_user.id}, model_id={model_id}")
        return AIModelResponse.model_validate(model)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/models/{model_id}", response_model=MessageResponse)
async def delete_model(
    model_id: int,
    admin_user: AdminUser,
    session: SessionDep,
) -> MessageResponse:
    """Delete AI model."""
    service = AIModelService(session)

    try:
        await service.delete_model(model_id)
        logger.info(f"Admin deleted model | admin_id={admin_user.id}, model_id={model_id}")
        return MessageResponse(message="Модель удалена")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/models/{model_id}/toggle", response_model=MessageResponse)
async def toggle_model(
    model_id: int,
    admin_user: AdminUser,
    session: SessionDep,
) -> MessageResponse:
    """Toggle model enabled/disabled status."""
    service = AIModelService(session)

    try:
        new_status = await service.toggle_model(model_id)
        status_text = "включена" if new_status else "отключена"

        logger.info(f"Admin toggled model | admin_id={admin_user.id}, model_id={model_id}, enabled={new_status}")

        return MessageResponse(message=f"Модель {status_text}")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
