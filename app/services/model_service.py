from app.core.exceptions import ModelInactiveError, ModelNotFoundError
from app.models.prediction_model import PredictionModel
from app.models.responses import ModelDetail, ModelListItem, ModelsResponse
from app.repositories.model_repository import ModelRepository


class ModelService:
    """Lists and validates prediction models selected by the mobile app.

    The API never executes a model algorithm. `algorithm` is catalog metadata.
    """

    def __init__(self, repository: ModelRepository) -> None:
        self._repository = repository

    def list_active(self) -> ModelsResponse:
        models = sorted(
            (item for item in self._repository.list_all() if item.active),
            key=lambda item: item.name.lower(),
        )
        items = [self._to_list_item(item) for item in models]
        return ModelsResponse(items=items, total=len(items))

    def get(self, model_id: str) -> ModelDetail:
        model = self._repository.get_by_id(model_id)
        if model is None:
            raise ModelNotFoundError(model_id)
        return self._to_detail(model)

    def require_active(self, model_id: str) -> PredictionModel:
        model = self._repository.get_by_id(model_id)
        if model is None:
            raise ModelNotFoundError(model_id)
        if not model.active:
            raise ModelInactiveError(model_id)
        return model

    def list_active_models(self) -> list[PredictionModel]:
        return sorted(
            (item for item in self._repository.list_all() if item.active),
            key=lambda item: item.name.lower(),
        )

    def known_ids(self) -> set[str]:
        return {item.id for item in self._repository.list_all()}

    @staticmethod
    def _to_list_item(model: PredictionModel) -> ModelListItem:
        return ModelListItem(
            id=model.id,
            name=model.name,
            description=model.description,
            group_name=model.group_name,
            algorithm=model.algorithm,
            version=model.version,
        )

    @staticmethod
    def _to_detail(model: PredictionModel) -> ModelDetail:
        return ModelDetail(
            id=model.id,
            name=model.name,
            description=model.description,
            group_name=model.group_name,
            algorithm=model.algorithm,
            version=model.version,
            active=model.active,
        )
