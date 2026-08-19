from abc import ABC, abstractmethod

from app.models.prediction_model import PredictionModel


class ModelRepository(ABC):
    """Read-only access to the prediction-model catalog.

    Routes must not read models.json. A new group is added by inserting a
    catalog entry and prediction rows — not by creating new routes.
    """

    @abstractmethod
    def list_all(self) -> list[PredictionModel]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, model_id: str) -> PredictionModel | None:
        raise NotImplementedError
