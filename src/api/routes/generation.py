"""Generation routes."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import CurrentUser, SessionDep
from src.api.schemas.generation import (
    GenerationCreateRequest,
    GenerationListResponse,
    GenerationResponse,
    GenerationStatusResponse,
)
from src.config import settings
from src.core.exceptions import InsufficientBalanceError, NotFoundError, ValidationError
from src.modules.generation.service import GenerationService
from src.shared.enums import GenerationType

router = APIRouter()


def _build_generation_response(generation, base_url: str) -> GenerationResponse:
    """Build generation response with file URLs."""
    result_file_url = None
    if generation.result_file_path:
        file_name = generation.result_file_path.split("/")[-1]
        result_file_url = f"{base_url}/static/generations/{file_name}"
    
    return GenerationResponse(
        id=generation.id,
        generation_type=generation.generation_type,
        status=generation.status,
        prompt=generation.prompt,
        tokens_spent=generation.tokens_spent,
        result_url=generation.result_url,
        result_file_url=result_file_url,
        error_message=generation.error_message,
        created_at=generation.created_at,
        completed_at=generation.completed_at,
        model_code=generation.model.code if generation.model else None,
        model_name=generation.model.name if generation.model else None,
    )


@router.post("", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    request: GenerationCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> GenerationResponse:
    """Create new generation task."""
    service = GenerationService(session)
    
    try:
        generation = await service.create_generation(
            user_id=current_user.id,
            model_code=request.model_code,
            prompt=request.prompt,
            image_url=request.image_url,
            video_url=request.video_url,  # NEW
            aspect_ratio=request.aspect_ratio,
            duration=request.duration,
            extra_params=request.extra_params,
        )
        
        return _build_generation_response(generation, settings.WEBAPP_URL)
        
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.message,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> GenerationResponse:
    """Get generation by ID."""
    service = GenerationService(session)
    
    try:
        generation = await service.get_generation(generation_id)
        
        if generation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation not found",
            )
        
        return _build_generation_response(generation, settings.WEBAPP_URL)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get("/{generation_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    generation_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> GenerationStatusResponse:
    """Get generation status (for polling)."""
    service = GenerationService(session)
    
    try:
        generation = await service.get_generation(generation_id)
        
        if generation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation not found",
            )
        
        result_file_url = None
        if generation.result_file_path:
            file_name = generation.result_file_path.split("/")[-1]
            result_file_url = f"{settings.WEBAPP_URL}/static/generations/{file_name}"
        
        return GenerationStatusResponse(
            id=generation.id,
            status=generation.status,
            result_url=generation.result_url,
            result_file_url=result_file_url,
            error_message=generation.error_message,
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found",
        )


@router.get("", response_model=GenerationListResponse)
async def get_generations(
    current_user: CurrentUser,
    session: SessionDep,
    offset: int = 0,
    limit: int = 50,
    generation_type: GenerationType | None = None,
) -> GenerationListResponse:
    """Get user's generations."""
    service = GenerationService(session)
    
    generations = await service.get_user_generations(
        current_user.id, offset, limit, generation_type
    )
    
    from src.modules.generation.repository import GenerationRepository
    repo = GenerationRepository(session)
    total = await repo.count_user_generations(current_user.id, generation_type)
    
    return GenerationListResponse(
        items=[
            _build_generation_response(g, settings.WEBAPP_URL)
            for g in generations
        ],
        total=total,
    )

