from fastapi import APIRouter, Depends, Path

from app.api.deps import get_model_service
from app.models.responses import ModelDetail, ModelsResponse
from app.services.model_service import ModelService

router = APIRouter()


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List active prediction models",
    description=(
        "Returns catalog entries with `active=true`, ordered by name. "
        "The mobile app should call this first, let the user pick a model, "
        "and send that `id` as `model_id` on forecast endpoints. "
        "No model is treated as default or scientifically superior. "
        "`algorithm` is metadata only; this API never executes a model."
    ),
)
def list_models(
    model_service: ModelService = Depends(get_model_service),
) -> ModelsResponse:
    return model_service.list_active()


@router.get(
    "/models/{model_id}",
    response_model=ModelDetail,
    summary="Get a prediction model",
    description="Returns one catalog entry, including inactive models.",
    responses={
        404: {
            "description": "Unknown model id.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "MODEL_NOT_FOUND",
                            "message": "The requested prediction model was not found.",
                        }
                    }
                }
            },
        }
    },
)
def get_model(
    model_id: str = Path(..., min_length=1, description="Unique identifier of the prediction model."),
    model_service: ModelService = Depends(get_model_service),
) -> ModelDetail:
    return model_service.get(model_id)
