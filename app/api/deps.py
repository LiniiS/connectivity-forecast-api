from functools import lru_cache

from app.config.settings import Settings, settings
from app.repositories.csv_prediction_repository import CsvPredictionRepository
from app.repositories.json_model_repository import JsonModelRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.activity_service import ActivityService
from app.services.forecast_service import ForecastService
from app.services.location_service import LocationService
from app.services.model_service import ModelService
from app.services.quality_classifier import QualityClassifier
from app.services.recommendation_service import RecommendationService


@lru_cache
def get_settings() -> Settings:
    return settings


@lru_cache
def get_model_repository() -> ModelRepository:
    return JsonModelRepository(get_settings().resolved_models_path())


@lru_cache
def get_prediction_repository() -> PredictionRepository:
    model_service = ModelService(get_model_repository())
    return CsvPredictionRepository(
        get_settings().resolved_predictions_path(),
        known_model_ids=model_service.known_ids(),
    )


def get_quality_classifier() -> QualityClassifier:
    return QualityClassifier()


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


def get_model_service() -> ModelService:
    return ModelService(get_model_repository())


def get_location_service() -> LocationService:
    return LocationService(get_prediction_repository())


def get_forecast_service() -> ForecastService:
    return ForecastService(
        repository=get_prediction_repository(),
        location_service=get_location_service(),
        model_service=get_model_service(),
        classifier=get_quality_classifier(),
        recommendations=get_recommendation_service(),
    )


def get_activity_service() -> ActivityService:
    return ActivityService(
        location_service=get_location_service(),
        forecast_service=get_forecast_service(),
        classifier=get_quality_classifier(),
        recommendations=get_recommendation_service(),
    )
