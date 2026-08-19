from __future__ import annotations

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.core.exceptions import DatasetUnavailableError
from app.models.prediction import PredictionRecord, ProbeLocation
from app.repositories.prediction_repository import PredictionRepository

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = (
    "prediction_id",
    "model_id",
    "model_version",
    "probe_id",
    "measurement_id",
    "country_code",
    "asn_v4",
    "asn_v6",
    "latitude",
    "longitude",
    "prediction_generated_at",
    "prediction_for",
    "predicted_avg_rtt_ms",
    "predicted_packet_loss_pct",
    "model_confidence",
)

FORBIDDEN_COLUMNS = {
    "src_addr",
    "from",
    "address_v4",
    "address_v6",
    "prefix_v4",
    "prefix_v6",
}


class CsvPredictionRepository(PredictionRepository):
    """Loads a read-only predictions CSV into memory.

    Point PREDICTIONS_FILE to data/predictions.csv when real group outputs exist.
    Rows whose model_id is not in the catalog are skipped and logged.
    """

    def __init__(
        self,
        csv_path: Path,
        known_model_ids: set[str] | None = None,
    ) -> None:
        self._csv_path = csv_path
        self._known_model_ids = known_model_ids
        self._records: list[PredictionRecord] | None = None
        self._by_model: dict[str, list[PredictionRecord]] | None = None
        self._by_model_probe: dict[tuple[str, int], list[PredictionRecord]] | None = None
        self._locations: dict[int, ProbeLocation] | None = None
        self._locations_by_model: dict[str, dict[int, ProbeLocation]] | None = None

    def ensure_loaded(self) -> None:
        self._load()

    def list_all(self) -> list[PredictionRecord]:
        return list(self._load())

    def get_predictions_by_model(self, model_id: str) -> list[PredictionRecord]:
        self._load()
        assert self._by_model is not None
        return list(self._by_model.get(model_id, []))

    def get_timeline(self, model_id: str, probe_id: int) -> list[PredictionRecord]:
        self._load()
        assert self._by_model_probe is not None
        return list(self._by_model_probe.get((model_id, probe_id), []))

    def get_prediction(
        self,
        model_id: str,
        probe_id: int,
        prediction_time: datetime,
    ) -> PredictionRecord | None:
        target = _as_utc(prediction_time)
        for record in self.get_timeline(model_id, probe_id):
            if record.prediction_for == target:
                return record
        return None

    def get_predictions_for_comparison(
        self,
        probe_id: int,
        prediction_time: datetime,
    ) -> list[PredictionRecord]:
        target = _as_utc(prediction_time)
        self._load()
        assert self._by_model is not None
        matches: list[PredictionRecord] = []
        for model_id in self._by_model:
            record = self.get_prediction(model_id, probe_id, target)
            if record is not None:
                matches.append(record)
        return matches

    def list_prediction_times(self, probe_id: int, model_id: str) -> list[datetime]:
        return [record.prediction_for for record in self.get_timeline(model_id, probe_id)]

    def list_probe_locations(self, model_id: str | None = None) -> list[ProbeLocation]:
        self._load()
        if model_id is None:
            assert self._locations is not None
            return list(self._locations.values())
        assert self._locations_by_model is not None
        return list(self._locations_by_model.get(model_id, {}).values())

    def get_probe_location(self, probe_id: int) -> ProbeLocation | None:
        self._load()
        assert self._locations is not None
        return self._locations.get(probe_id)

    def _load(self) -> list[PredictionRecord]:
        if self._records is not None:
            return self._records

        if not self._csv_path.exists():
            logger.error("Predictions file not found: %s", self._csv_path)
            raise DatasetUnavailableError("The prediction dataset file was not found.")

        try:
            with self._csv_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    raise DatasetUnavailableError("The prediction dataset has no header row.")
                columns = [name.strip() for name in reader.fieldnames]
                self._validate_header(columns)
                records: list[PredictionRecord] = []
                skipped_unknown = 0
                for row_number, raw_row in enumerate(reader, start=2):
                    try:
                        record = self._parse_row(raw_row)
                    except ValueError as exc:
                        logger.warning(
                            "Skipping invalid prediction row %s in %s: %s",
                            row_number,
                            self._csv_path.name,
                            exc,
                        )
                        continue
                    if self._known_model_ids is not None and record.model_id not in self._known_model_ids:
                        skipped_unknown += 1
                        logger.warning(
                            "Skipping prediction %s: model_id %s is not registered in the model catalog.",
                            record.prediction_id,
                            record.model_id,
                        )
                        continue
                    records.append(record)
        except DatasetUnavailableError:
            raise
        except OSError:
            logger.exception("Failed to read predictions file")
            raise DatasetUnavailableError("The prediction dataset could not be read.") from None

        if skipped_unknown:
            logger.warning(
                "Ignored %s prediction rows with unregistered model_id values.",
                skipped_unknown,
            )

        if not records:
            raise DatasetUnavailableError("The prediction dataset is empty.")

        by_model: dict[str, list[PredictionRecord]] = {}
        by_model_probe: dict[tuple[str, int], list[PredictionRecord]] = {}
        locations: dict[int, ProbeLocation] = {}
        locations_by_model: dict[str, dict[int, ProbeLocation]] = {}
        for record in records:
            by_model.setdefault(record.model_id, []).append(record)
            by_model_probe.setdefault((record.model_id, record.probe_id), []).append(record)
            location = ProbeLocation(
                probe_id=record.probe_id,
                country_code=record.country_code,
                asn_v4=record.asn_v4,
                asn_v6=record.asn_v6,
                latitude=record.latitude,
                longitude=record.longitude,
            )
            locations[record.probe_id] = location
            locations_by_model.setdefault(record.model_id, {})[record.probe_id] = location

        for probe_records in by_model_probe.values():
            probe_records.sort(key=lambda item: item.prediction_for)

        self._records = records
        self._by_model = by_model
        self._by_model_probe = by_model_probe
        self._locations = locations
        self._locations_by_model = locations_by_model
        logger.info(
            "Loaded %s predictions for %s models and %s probes from %s",
            len(records),
            len(by_model),
            len(locations),
            self._csv_path,
        )
        return records

    def _validate_header(self, columns: list[str]) -> None:
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise DatasetUnavailableError(
                f"The prediction dataset is missing required columns: {', '.join(missing)}."
            )
        leaked = [name for name in columns if name in FORBIDDEN_COLUMNS]
        if leaked:
            raise DatasetUnavailableError(
                "The prediction dataset contains probe address fields that must not be exposed."
            )

    def _parse_row(self, row: dict[str, str]) -> PredictionRecord:
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        if not -90 <= latitude <= 90:
            raise ValueError("latitude out of range")
        if not -180 <= longitude <= 180:
            raise ValueError("longitude out of range")

        predicted_avg = float(row["predicted_avg_rtt_ms"])
        predicted_loss = float(row["predicted_packet_loss_pct"])
        if predicted_avg < 0 or predicted_loss < 0:
            raise ValueError("predicted metrics must be non-negative")

        return PredictionRecord(
            prediction_id=_required(row, "prediction_id"),
            model_id=_required(row, "model_id"),
            probe_id=int(row["probe_id"]),
            measurement_id=int(row["measurement_id"]),
            country_code=_required(row, "country_code").upper(),
            asn_v4=_optional_int(row.get("asn_v4")),
            asn_v6=_optional_int(row.get("asn_v6")),
            latitude=latitude,
            longitude=longitude,
            prediction_generated_at=_parse_datetime(row["prediction_generated_at"]),
            prediction_for=_parse_datetime(row["prediction_for"]),
            predicted_avg_rtt_ms=predicted_avg,
            predicted_packet_loss_pct=predicted_loss,
            model_confidence=_optional_float(row.get("model_confidence")),
            model_version=_required(row, "model_version"),
        )


def _required(row: dict[str, str], column: str) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"missing {column}")
    return value


def _optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise ValueError("model_confidence must be between 0 and 1")
    return parsed


def _parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    return _as_utc(parsed)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
