"""AI Models routes."""

from fastapi import APIRouter

from src.api.dependencies import CurrentUser, SessionDep
from src.api.schemas.model import AIModelResponse, AIModelsGroupedResponse
from src.modules.ai_models.service import AIModelService
from src.shared.enums import GenerationType

router = APIRouter()


@router.get("", response_model=list[AIModelResponse])
async def get_models(
    current_user: CurrentUser,
    session: SessionDep,
    generation_type: GenerationType | None = None,
) -> list[AIModelResponse]:
    """Get available AI models."""
    service = AIModelService(session)
    models = await service.get_available_models(generation_type)
    return [AIModelResponse.model_validate(m) for m in models]


@router.get("/grouped", response_model=AIModelsGroupedResponse)
async def get_models_grouped(
    current_user: CurrentUser,
    session: SessionDep,
) -> AIModelsGroupedResponse:
    """Get AI models grouped by type."""
    service = AIModelService(session)
    grouped = await service.get_models_grouped()
    
    return AIModelsGroupedResponse(
        image=[AIModelResponse.model_validate(m) for m in grouped["image"]],
        video=[AIModelResponse.model_validate(m) for m in grouped["video"]],
        faceswap=[AIModelResponse.model_validate(m) for m in grouped["faceswap"]],
    )


@router.get("/{model_code}", response_model=AIModelResponse)
async def get_model(
    model_code: str,
    current_user: CurrentUser,
    session: SessionDep,
) -> AIModelResponse:
    """Get specific AI model by code."""
    service = AIModelService(session)
    model = await service.get_model_by_code(model_code)
    return AIModelResponse.model_validate(model)
