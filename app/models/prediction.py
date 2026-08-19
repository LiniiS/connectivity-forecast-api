from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PredictionRecord:
    """Internal representation of one row from the predictions file.

    Field origin is documented in README.md (RIPE Atlas field mapping).
    This object is not a RIPE Atlas measurement.
    """

    prediction_id: str
    model_id: str
    probe_id: int
    measurement_id: int
    country_code: str
    asn_v4: int | None
    asn_v6: int | None
    latitude: float
    longitude: float
    prediction_generated_at: datetime
    prediction_for: datetime
    predicted_avg_rtt_ms: float
    predicted_packet_loss_pct: float
    model_confidence: float | None
    model_version: str


@dataclass(frozen=True)
class ProbeLocation:
    probe_id: int
    country_code: str
    asn_v4: int | None
    asn_v6: int | None
    latitude: float
    longitude: float
