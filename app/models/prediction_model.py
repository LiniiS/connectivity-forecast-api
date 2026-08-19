from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PredictionModel:
    """Catalog entry for a student-group prediction model.

    `algorithm` is informational metadata only. This API never runs the algorithm.
    """

    id: str
    name: str
    description: str
    group_name: str
    algorithm: str
    version: str
    active: bool
    created_at: datetime | None = None
