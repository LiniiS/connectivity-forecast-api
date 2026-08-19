from pathlib import Path

import pytest

from app.core.exceptions import DatasetUnavailableError
from app.repositories.csv_prediction_repository import CsvPredictionRepository

MOCK_CSV = Path(__file__).resolve().parents[1] / "data" / "mock_predictions.csv"
HEADER = (
    "prediction_id,model_id,model_version,probe_id,measurement_id,country_code,asn_v4,asn_v6,"
    "latitude,longitude,prediction_generated_at,prediction_for,"
    "predicted_avg_rtt_ms,predicted_packet_loss_pct,model_confidence\n"
)


def test_mock_dataset_loads_expected_shape() -> None:
    repository = CsvPredictionRepository(MOCK_CSV)
    records = repository.list_all()
    probes = repository.list_probe_locations()

    assert len(records) == 960
    assert len(probes) == 10
    assert {record.model_id for record in records} == {"model-a", "model-b", "model-c", "model-d"}
    assert {probe.country_code for probe in probes} == {"BR"}
    assert all(record.predicted_avg_rtt_ms >= 0 for record in records)
    assert all(record.predicted_packet_loss_pct >= 0 for record in records)
    assert all(record.prediction_for.tzinfo is not None for record in records)
    assert any(record.model_confidence is None for record in records)

    times_a = repository.list_prediction_times(900001, "model-a")
    times_b = repository.list_prediction_times(900001, "model-b")
    assert times_a == times_b
    assert len(times_a) == 24


def test_missing_file_raises_dataset_unavailable(tmp_path: Path) -> None:
    repository = CsvPredictionRepository(tmp_path / "missing.csv")
    with pytest.raises(DatasetUnavailableError) as exc:
        repository.list_all()
    assert exc.value.status_code == 500


def test_empty_file_raises_dataset_unavailable(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text(HEADER, encoding="utf-8")
    repository = CsvPredictionRepository(csv_path)
    with pytest.raises(DatasetUnavailableError):
        repository.list_all()


def test_unregistered_model_id_is_skipped(tmp_path: Path) -> None:
    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text(
        HEADER
        + "1,model-a,1.0,900001,1001,BR,28573,,-23.55,-46.63,"
        "2026-08-18T18:00:00Z,2026-08-20T19:00:00Z,71.4,1.5,0.82\n"
        "2,model-x,1.0,900001,1001,BR,28573,,-23.55,-46.63,"
        "2026-08-18T18:00:00Z,2026-08-20T19:00:00Z,90.0,3.0,0.50\n",
        encoding="utf-8",
    )
    repository = CsvPredictionRepository(csv_path, known_model_ids={"model-a"})
    records = repository.list_all()
    assert len(records) == 1
    assert records[0].model_id == "model-a"
