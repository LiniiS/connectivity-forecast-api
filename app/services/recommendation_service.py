from app.config.activity_rules import (
    ACTIVITY_MESSAGES,
    MINIMUM_QUALITY_BY_ACTIVITY,
    QUALITY_RANK,
    RECOMMENDATION_BY_QUALITY,
    ActivityType,
    RecommendationCode,
)
from app.config.quality_rules import Quality
from app.models.responses import Recommendation


class RecommendationService:
    """Turns a quality classification into a stable recommendation code.

    Recommendations are backend business rules. They are not model outputs
    and they are not RIPE Atlas fields.
    """

    def for_quality(self, quality: Quality) -> Recommendation:
        code, message = RECOMMENDATION_BY_QUALITY[quality]
        return Recommendation(code=code, message=message)

    def for_activity(self, activity: ActivityType, quality: Quality) -> tuple[bool, Recommendation]:
        minimum = MINIMUM_QUALITY_BY_ACTIVITY[activity]
        suitable = QUALITY_RANK[quality] >= QUALITY_RANK[minimum]
        code = self._activity_code(suitable, quality)
        message = ACTIVITY_MESSAGES[(activity, quality)]
        return suitable, Recommendation(code=code, message=message)

    @staticmethod
    def _activity_code(suitable: bool, quality: Quality) -> RecommendationCode:
        if suitable and quality is Quality.GOOD:
            return RecommendationCode.NORMAL_USE
        if quality is Quality.UNSTABLE:
            return RecommendationCode.PREPARE_OFFLINE
        return RecommendationCode.REDUCE_NETWORK_USAGE
