from app.services.quality_classifier import QualityClassifier
from app.config.quality_rules import Quality

classifier = QualityClassifier()


def test_good_when_rtt_and_loss_are_low() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=22.4, predicted_packet_loss_pct=0.1)
    assert result.quality is Quality.GOOD
    assert result.quality_score > 80


def test_moderate_when_rtt_crosses_threshold() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=71.4, predicted_packet_loss_pct=0.2)
    assert result.quality is Quality.MODERATE


def test_moderate_when_loss_crosses_threshold() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=20.0, predicted_packet_loss_pct=1.5)
    assert result.quality is Quality.MODERATE


def test_unstable_when_rtt_is_high() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=185.2, predicted_packet_loss_pct=0.4)
    assert result.quality is Quality.UNSTABLE


def test_unstable_when_loss_is_high() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=40.0, predicted_packet_loss_pct=8.1)
    assert result.quality is Quality.UNSTABLE


def test_worse_metric_wins() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=20.0, predicted_packet_loss_pct=5.0)
    assert result.quality is Quality.UNSTABLE


def test_quality_score_is_bounded() -> None:
    result = classifier.classify(predicted_avg_rtt_ms=400.0, predicted_packet_loss_pct=40.0)
    assert 0 <= result.quality_score <= 100
