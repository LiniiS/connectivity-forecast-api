"""Experimental connection-quality rules for this educational prototype.

These thresholds are NOT scientific standards and are NOT classifications
provided by RIPE Atlas. They are configurable business rules of this project.

The predictive model outputs only:
  - predicted_avg_rtt_ms
  - predicted_packet_loss_pct

Quality labels (GOOD / MODERATE / UNSTABLE) and quality_score are produced
by the backend QualityClassifier using the values below.
"""

from enum import StrEnum


class Quality(StrEnum):
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    UNSTABLE = "UNSTABLE"


# RTT thresholds in milliseconds (predicted_avg_rtt_ms).
MODERATE_RTT_MS = 60.0
UNSTABLE_RTT_MS = 150.0

# Packet-loss thresholds in percent (predicted_packet_loss_pct).
MODERATE_PACKET_LOSS_PCT = 1.0
UNSTABLE_PACKET_LOSS_PCT = 5.0

# Experimental 0-100 score: RTT and loss are scaled against these references.
SCORE_RTT_REF_MS = 200.0
SCORE_LOSS_REF_PCT = 10.0
SCORE_RTT_WEIGHT = 0.70
SCORE_LOSS_WEIGHT = 0.30
