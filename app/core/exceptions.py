class AppError(Exception):
    """Domain error mapped to a stable HTTP error payload."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ProbeNotFoundError(AppError):
    def __init__(self, probe_id: int) -> None:
        super().__init__(
            code="PROBE_NOT_FOUND",
            message="No prediction data was found for the requested probe.",
            status_code=404,
        )
        self.probe_id = probe_id


class NoProbeInRangeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="NO_PROBE_IN_RANGE",
            message="No probe with prediction data was found within the requested radius.",
            status_code=404,
        )


class DatasetUnavailableError(AppError):
    def __init__(self, message: str = "The prediction dataset is unavailable.") -> None:
        super().__init__(
            code="DATASET_UNAVAILABLE",
            message=message,
            status_code=500,
        )


class ModelNotFoundError(AppError):
    def __init__(self, model_id: str | None = None) -> None:
        super().__init__(
            code="MODEL_NOT_FOUND",
            message="The requested prediction model was not found.",
            status_code=404,
        )
        self.model_id = model_id


class ModelInactiveError(AppError):
    def __init__(self, model_id: str | None = None) -> None:
        super().__init__(
            code="MODEL_INACTIVE",
            message="The requested prediction model is not active.",
            status_code=404,
        )
        self.model_id = model_id


class NoCommonPredictionError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="NO_COMMON_PREDICTION",
            message="No shared prediction instant was found across active models for this probe.",
            status_code=404,
        )


class InvalidTimeRangeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_TIME_RANGE",
            message="The 'from' timestamp must be earlier than or equal to the 'to' timestamp.",
            status_code=400,
        )
