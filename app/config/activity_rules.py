"""Experimental activity-suitability rules for this educational prototype.

These rules are NOT universal Internet engineering requirements.
They combine the backend quality classification with a requested activity
type so the mobile app can offer a planning hint.

The predictive model does not produce activity recommendations.
"""

from enum import StrEnum

from app.config.quality_rules import Quality


class ActivityType(StrEnum):
    VIDEO_CALL = "VIDEO_CALL"
    AUDIO_CALL = "AUDIO_CALL"
    STREAMING = "STREAMING"
    FILE_UPLOAD = "FILE_UPLOAD"
    WEB_BROWSING = "WEB_BROWSING"
    MESSAGING = "MESSAGING"


class RecommendationCode(StrEnum):
    NORMAL_USE = "NORMAL_USE"
    REDUCE_NETWORK_USAGE = "REDUCE_NETWORK_USAGE"
    PREPARE_OFFLINE = "PREPARE_OFFLINE"


# Minimum quality required for the activity to be considered suitable.
MINIMUM_QUALITY_BY_ACTIVITY: dict[ActivityType, Quality] = {
    ActivityType.VIDEO_CALL: Quality.GOOD,
    ActivityType.STREAMING: Quality.GOOD,
    ActivityType.AUDIO_CALL: Quality.MODERATE,
    ActivityType.FILE_UPLOAD: Quality.MODERATE,
    ActivityType.WEB_BROWSING: Quality.MODERATE,
    ActivityType.MESSAGING: Quality.UNSTABLE,
}

QUALITY_RANK: dict[Quality, int] = {
    Quality.UNSTABLE: 0,
    Quality.MODERATE: 1,
    Quality.GOOD: 2,
}

RECOMMENDATION_BY_QUALITY: dict[Quality, tuple[RecommendationCode, str]] = {
    Quality.GOOD: (
        RecommendationCode.NORMAL_USE,
        "A conexão prevista está adequada para atividades online neste período.",
    ),
    Quality.MODERATE: (
        RecommendationCode.REDUCE_NETWORK_USAGE,
        "A conexão pode apresentar alguma instabilidade neste período.",
    ),
    Quality.UNSTABLE: (
        RecommendationCode.PREPARE_OFFLINE,
        "Considere preparar recursos offline para este período.",
    ),
}

ACTIVITY_MESSAGES: dict[tuple[ActivityType, Quality], str] = {
    (ActivityType.VIDEO_CALL, Quality.GOOD): (
        "A conexão prevista está adequada para uma chamada de vídeo neste período."
    ),
    (ActivityType.VIDEO_CALL, Quality.MODERATE): (
        "Uma chamada de vídeo pode sofrer oscilações neste período."
    ),
    (ActivityType.VIDEO_CALL, Quality.UNSTABLE): (
        "Há risco de instabilidade para uma chamada de vídeo neste período."
    ),
    (ActivityType.AUDIO_CALL, Quality.GOOD): (
        "A conexão prevista está adequada para uma chamada de áudio neste período."
    ),
    (ActivityType.AUDIO_CALL, Quality.MODERATE): (
        "Uma chamada de áudio pode apresentar alguma instabilidade neste período."
    ),
    (ActivityType.AUDIO_CALL, Quality.UNSTABLE): (
        "Há risco de instabilidade para uma chamada de áudio neste período."
    ),
    (ActivityType.STREAMING, Quality.GOOD): (
        "A conexão prevista está adequada para streaming neste período."
    ),
    (ActivityType.STREAMING, Quality.MODERATE): (
        "O streaming pode apresentar buffering neste período."
    ),
    (ActivityType.STREAMING, Quality.UNSTABLE): (
        "Há risco de interrupções no streaming neste período."
    ),
    (ActivityType.FILE_UPLOAD, Quality.GOOD): (
        "A conexão prevista está adequada para envio de arquivos neste período."
    ),
    (ActivityType.FILE_UPLOAD, Quality.MODERATE): (
        "O envio de arquivos pode ser mais lento neste período."
    ),
    (ActivityType.FILE_UPLOAD, Quality.UNSTABLE): (
        "Há risco de falha ou lentidão no envio de arquivos neste período."
    ),
    (ActivityType.WEB_BROWSING, Quality.GOOD): (
        "A conexão prevista está adequada para navegação neste período."
    ),
    (ActivityType.WEB_BROWSING, Quality.MODERATE): (
        "A navegação pode ficar mais lenta neste período."
    ),
    (ActivityType.WEB_BROWSING, Quality.UNSTABLE): (
        "A navegação pode ficar instável neste período."
    ),
    (ActivityType.MESSAGING, Quality.GOOD): (
        "A conexão prevista está adequada para mensagens neste período."
    ),
    (ActivityType.MESSAGING, Quality.MODERATE): (
        "Mensagens devem funcionar, com possível atraso neste período."
    ),
    (ActivityType.MESSAGING, Quality.UNSTABLE): (
        "Mensagens podem atrasar; considere não depender só da rede neste período."
    ),
}
