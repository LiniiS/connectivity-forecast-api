from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.exceptions import DatasetUnavailableError
from app.models.prediction_model import PredictionModel
from app.repositories.model_repository import ModelRepository

logger = logging.getLogger(__name__)


class _CatalogItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    description: str
    group_name: str = Field(alias="groupName")
    algorithm: str
    version: str
    active: bool = True
    created_at: datetime | None = Field(default=None, alias="createdAt")


class JsonModelRepository(ModelRepository):
    """Loads the model catalog from a JSON file."""

    def __init__(self, json_path: Path) -> None:
        self._json_path = json_path
        self._models: dict[str, PredictionModel] | None = None

    def ensure_loaded(self) -> None:
        self._load()

    def list_all(self) -> list[PredictionModel]:
        return list(self._load().values())

    def get_by_id(self, model_id: str) -> PredictionModel | None:
        return self._load().get(model_id)

    def _load(self) -> dict[str, PredictionModel]:
        if self._models is not None:
            return self._models

        if not self._json_path.exists():
            logger.error("Models file not found: %s", self._json_path)
            raise DatasetUnavailableError("The prediction model catalog was not found.")

        try:
            raw = json.loads(self._json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to read model catalog")
            raise DatasetUnavailableError("The prediction model catalog could not be read.") from None

        if not isinstance(raw, list) or not raw:
            raise DatasetUnavailableError("The prediction model catalog is empty.")

        models: dict[str, PredictionModel] = {}
        for index, item in enumerate(raw):
            try:
                parsed = _CatalogItem.model_validate(item)
            except ValidationError as exc:
                logger.warning("Skipping invalid model catalog entry %s: %s", index, exc)
                continue
            if parsed.created_at is not None and parsed.created_at.tzinfo is None:
                created_at = parsed.created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = parsed.created_at
            models[parsed.id] = PredictionModel(
                id=parsed.id,
                name=parsed.name,
                description=parsed.description,
                group_name=parsed.group_name,
                algorithm=parsed.algorithm,
                version=parsed.version,
                active=parsed.active,
                created_at=created_at,
            )

        if not models:
            raise DatasetUnavailableError("The prediction model catalog has no valid entries.")

        self._models = models
        logger.info("Loaded %s prediction models from %s", len(models), self._json_path)
        return models
