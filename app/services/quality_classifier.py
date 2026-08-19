from dataclasses import dataclass

from app.config.quality_rules import (
    MODERATE_PACKET_LOSS_PCT,
    MODERATE_RTT_MS,
    SCORE_LOSS_REF_PCT,
    SCORE_LOSS_WEIGHT,
    SCORE_RTT_REF_MS,
    SCORE_RTT_WEIGHT,
    UNSTABLE_PACKET_LOSS_PCT,
    UNSTABLE_RTT_MS,
    Quality,
)


@dataclass(frozen=True)
class QualityAssessment:
    quality: Quality
    quality_score: int


class QualityClassifier:
    """Maps predicted RTT and packet loss to experimental quality labels.

    The predictive model does not emit GOOD/MODERATE/UNSTABLE.
    RIPE Atlas does not emit these categories either.
    """

    def classify(
        self,
        predicted_avg_rtt_ms: float,
        predicted_packet_loss_pct: float,
    ) -> QualityAssessment:
        quality = self._category(predicted_avg_rtt_ms, predicted_packet_loss_pct)
        score = self._score(predicted_avg_rtt_ms, predicted_packet_loss_pct)
        return QualityAssessment(quality=quality, quality_score=score)

    def _category(self, rtt_ms: float, loss_pct: float) -> Quality:
        rtt_level = self._level(
            rtt_ms,
            moderate_threshold=MODERATE_RTT_MS,
            unstable_threshold=UNSTABLE_RTT_MS,
        )
        loss_level = self._level(
            loss_pct,
            moderate_threshold=MODERATE_PACKET_LOSS_PCT,
            unstable_threshold=UNSTABLE_PACKET_LOSS_PCT,
        )
        return min(rtt_level, loss_level, key=self._rank)

    @staticmethod
    def _level(value: float, moderate_threshold: float, unstable_threshold: float) -> Quality:
        if value >= unstable_threshold:
            return Quality.UNSTABLE
        if value >= moderate_threshold:
            return Quality.MODERATE
        return Quality.GOOD

    @staticmethod
    def _rank(quality: Quality) -> int:
        return {Quality.UNSTABLE: 0, Quality.MODERATE: 1, Quality.GOOD: 2}[quality]

    @staticmethod
    def _score(rtt_ms: float, loss_pct: float) -> int:
        rtt_component = max(0.0, 1.0 - (rtt_ms / SCORE_RTT_REF_MS)) * (SCORE_RTT_WEIGHT * 100)
        loss_component = max(0.0, 1.0 - (loss_pct / SCORE_LOSS_REF_PCT)) * (SCORE_LOSS_WEIGHT * 100)
        return int(round(min(100.0, max(0.0, rtt_component + loss_component))))
