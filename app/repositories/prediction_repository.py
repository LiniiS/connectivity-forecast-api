from abc import ABC, abstractmethod
from datetime import datetime

from app.models.prediction import PredictionRecord, ProbeLocation


class PredictionRepository(ABC):
    """Read-only access to prediction records, always scoped by model when required.

    Routes must not depend on CSV, files, or a future database.
    """

    @abstractmethod
    def list_all(self) -> list[PredictionRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_predictions_by_model(self, model_id: str) -> list[PredictionRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_timeline(self, model_id: str, probe_id: int) -> list[PredictionRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_prediction(
        self,
        model_id: str,
        probe_id: int,
        prediction_time: datetime,
    ) -> PredictionRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_predictions_for_comparison(
        self,
        probe_id: int,
        prediction_time: datetime,
    ) -> list[PredictionRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_prediction_times(self, probe_id: int, model_id: str) -> list[datetime]:
        raise NotImplementedError

    @abstractmethod
    def list_probe_locations(self, model_id: str | None = None) -> list[ProbeLocation]:
        raise NotImplementedError

    @abstractmethod
    def get_probe_location(self, probe_id: int) -> ProbeLocation | None:
        raise NotImplementedError
