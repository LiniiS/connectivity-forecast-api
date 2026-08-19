from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration. Swap the predictions file without changing routes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "internet-quality-api"
    predictions_file: str = "data/mock_predictions.csv"
    models_file: str = "data/models.json"
    default_model_id: str | None = None
    allowed_origins: str = "*"
    log_level: str = "INFO"
    timeline_default_limit: int = 24
    timeline_max_limit: int = 100

    @field_validator("default_model_id", mode="before")
    @classmethod
    def empty_default_model(cls, value: object) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        return str(value).strip()

    def resolved_predictions_path(self) -> Path:
        return self._resolve(self.predictions_file)

    def resolved_models_path(self) -> Path:
        return self._resolve(self.models_file)

    def _resolve(self, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    def cors_origins(self) -> list[str]:
        origins = [item.strip() for item in self.allowed_origins.split(",") if item.strip()]
        return origins or ["*"]


settings = Settings()
