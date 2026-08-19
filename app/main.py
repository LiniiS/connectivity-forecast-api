import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.deps import get_model_repository, get_prediction_repository
from app.api.v1.router import api_v1_router
from app.config.settings import settings
from app.core.exceptions import AppError
from app.models.responses import ErrorBody, ErrorResponse
from app.repositories.csv_prediction_repository import CsvPredictionRepository
from app.repositories.json_model_repository import JsonModelRepository

logger = logging.getLogger(__name__)

OPENAPI_DESCRIPTION = """
API educacional de previsão de qualidade de conexão.

Camada de desacoplamento:

`RIPE Atlas → dados históricos → Model A/B/C/D → predictions.csv → esta API → aplicativos mobile`

Esta API **não** consulta o RIPE Atlas e **não** executa nenhum modelo.
Ela lê o catálogo em `data/models.json` e previsões já calculadas em CSV.
O aplicativo escolhe um modelo via `GET /api/v1/models` e envia `model_id` nas consultas.

Classificação de campos no schema:

- **SOURCE** — valor com correspondência a um campo RIPE Atlas (probe ou medição de ping)
- **DERIVED** — calculado a partir de campos RIPE (ex.: packet loss a partir de `sent` e `rcvd`)
- **PREDICTED** — produzido pelo modelo/pipeline, não pelo RIPE Atlas
- **BUSINESS** — regra de negócio desta API (qualidade, score, recomendação)

As categorias GOOD / MODERATE / UNSTABLE são regras experimentais do protótipo.
Não são classificações do RIPE Atlas.
"""


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    models = get_model_repository()
    if isinstance(models, JsonModelRepository):
        models.ensure_loaded()
    repository = get_prediction_repository()
    if isinstance(repository, CsvPredictionRepository):
        repository.ensure_loaded()
    yield


def create_app() -> FastAPI:
    configure_logging()
    application = FastAPI(
        title="Internet Quality API",
        version="0.2.0",
        description=OPENAPI_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        contact={"name": "Internet Quality API — disciplina de Dispositivos Móveis"},
    )
    _configure_cors(application)
    _configure_exception_handlers(application)
    application.include_router(api_v1_router)

    @application.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return application


def _configure_cors(application: FastAPI) -> None:
    origins = settings.cors_origins()
    allow_credentials = origins != ["*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _configure_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        logger.info("Application error %s: %s", exc.code, exc.message)
        return _error_response(exc.status_code, exc.code, exc.message)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = []
        for item in exc.errors():
            location = ".".join(str(part) for part in item.get("loc", []) if part != "body")
            details.append({"field": location, "message": item.get("msg")})
        return _error_response(
            422,
            "VALIDATION_ERROR",
            "Invalid request parameters.",
            details,
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @application.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error")
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
        )


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=payload.model_dump(by_alias=True, exclude_none=True))


app = create_app()
