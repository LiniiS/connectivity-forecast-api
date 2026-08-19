from fastapi import APIRouter, Depends

from app.api.deps import get_activity_service
from app.models.responses import ActivityCheckRequest, ActivityCheckResponse
from app.services.activity_service import ActivityService

router = APIRouter()


@router.post(
    "/activity/check",
    response_model=ActivityCheckResponse,
    summary="Check whether an activity looks suitable",
    description=(
        "Combines the nearest probe forecast at the requested instant with an "
        "experimental activity rule for the selected `modelId`. "
        "Suitability is a BUSINESS decision of this prototype. "
        "The same QualityClassifier and RecommendationService are used for every model. "
        "The matched probe is only a geographic reference."
    ),
)
def check_activity(
    payload: ActivityCheckRequest,
    activity_service: ActivityService = Depends(get_activity_service),
) -> ActivityCheckResponse:
    return activity_service.check(payload)
