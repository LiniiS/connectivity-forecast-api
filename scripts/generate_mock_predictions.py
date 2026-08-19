"""Generate fictional mock predictions for multiple catalog models.

IDs, coordinates, ASNs and measurements are MOCKED.
They do not identify real RIPE Atlas probes.
The API does not execute these algorithms; rows are precomputed output.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "mock_predictions.csv"

COLUMNS = [
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
]

PROBES = [
    {"probe_id": 900001, "measurement_id": 100001, "lat": -23.5505, "lon": -46.6333, "asn_v4": 28573, "asn_v6": None, "base_rtt": 28.0, "base_loss": 0.2},
    {"probe_id": 900002, "measurement_id": 100002, "lat": -22.9068, "lon": -43.1729, "asn_v4": 7738, "asn_v6": 7738, "base_rtt": 32.0, "base_loss": 0.3},
    {"probe_id": 900003, "measurement_id": 100003, "lat": -19.9167, "lon": -43.9345, "asn_v4": 16735, "asn_v6": None, "base_rtt": 36.0, "base_loss": 0.4},
    {"probe_id": 900004, "measurement_id": 100004, "lat": -15.7975, "lon": -47.8919, "asn_v4": 28573, "asn_v6": 28573, "base_rtt": 34.0, "base_loss": 0.3},
    {"probe_id": 900005, "measurement_id": 100005, "lat": -12.9714, "lon": -38.5014, "asn_v4": 18881, "asn_v6": None, "base_rtt": 48.0, "base_loss": 0.6},
    {"probe_id": 900006, "measurement_id": 100006, "lat": -8.0476, "lon": -34.8770, "asn_v4": 18881, "asn_v6": 18881, "base_rtt": 52.0, "base_loss": 0.7},
    {"probe_id": 900007, "measurement_id": 100007, "lat": -3.7172, "lon": -38.5434, "asn_v4": 10429, "asn_v6": None, "base_rtt": 55.0, "base_loss": 0.8},
    {"probe_id": 900008, "measurement_id": 100008, "lat": -25.4284, "lon": -49.2733, "asn_v4": 28573, "asn_v6": None, "base_rtt": 30.0, "base_loss": 0.2},
    {"probe_id": 900009, "measurement_id": 100009, "lat": -30.0346, "lon": -51.2177, "asn_v4": 10429, "asn_v6": 10429, "base_rtt": 38.0, "base_loss": 0.5},
    {"probe_id": 900010, "measurement_id": 100010, "lat": -3.1190, "lon": -60.0217, "asn_v4": 7738, "asn_v6": None, "base_rtt": 78.0, "base_loss": 1.2},
]

# Same probe_id + prediction_for for every model; only predicted values differ.
MODELS = [
    {"id": "model-a", "version": "1.0", "rtt_factor": 1.00, "loss_factor": 1.00, "rtt_bias": 0.0, "loss_bias": 0.0},
    {"id": "model-b", "version": "1.0", "rtt_factor": 1.08, "loss_factor": 1.20, "rtt_bias": 6.5, "loss_bias": 0.5},
    {"id": "model-c", "version": "1.0", "rtt_factor": 0.88, "loss_factor": 0.70, "rtt_bias": -6.0, "loss_bias": -0.2},
    {"id": "model-d", "version": "1.0", "rtt_factor": 1.04, "loss_factor": 1.35, "rtt_bias": 14.0, "loss_bias": 0.9},
]


def baseline_metrics(probe: dict, hour: int) -> tuple[float, float, float | None]:
    peak = 0.5 * (1 + math.sin((hour - 13) / 24 * 2 * math.pi))
    rtt = probe["base_rtt"] + peak * 55 + (hour % 5) * 1.3
    loss = probe["base_loss"] + peak * 4.8 + (hour % 7) * 0.05

    if probe["probe_id"] == 900010 and hour in {18, 19, 20, 21}:
        rtt = 170.0 + (hour - 18) * 8.4
        loss = 6.5 + (hour - 18) * 0.8

    if probe["probe_id"] == 900001 and hour in {2, 3, 4}:
        rtt = 22.0 + hour * 0.4
        loss = 0.1

    if hour in {3, 15} or (probe["probe_id"] == 900007 and hour == 11):
        confidence = None
    else:
        confidence = round(max(0.55, min(0.96, 0.93 - peak * 0.18)), 2)

    return rtt, loss, confidence


def apply_model(model: dict, rtt: float, loss: float) -> tuple[float, float]:
    adjusted_rtt = max(1.0, rtt * model["rtt_factor"] + model["rtt_bias"])
    adjusted_loss = max(0.0, loss * model["loss_factor"] + model["loss_bias"])
    return round(adjusted_rtt, 1), round(adjusted_loss, 1)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    generated_at = "2026-08-18T12:00:00Z"
    for probe in PROBES:
        for hour in range(24):
            base_rtt, base_loss, confidence = baseline_metrics(probe, hour)
            prediction_for = f"2026-08-20T{hour:02d}:00:00Z"
            for model in MODELS:
                rtt, loss = apply_model(model, base_rtt, base_loss)
                rows.append(
                    {
                        "prediction_id": f"mock-{model['id']}-{probe['probe_id']}-{hour:02d}",
                        "model_id": model["id"],
                        "model_version": model["version"],
                        "probe_id": probe["probe_id"],
                        "measurement_id": probe["measurement_id"],
                        "country_code": "BR",
                        "asn_v4": probe["asn_v4"] if probe["asn_v4"] is not None else "",
                        "asn_v6": probe["asn_v6"] if probe["asn_v6"] is not None else "",
                        "latitude": probe["lat"],
                        "longitude": probe["lon"],
                        "prediction_generated_at": generated_at,
                        "prediction_for": prediction_for,
                        "predicted_avg_rtt_ms": rtt,
                        "predicted_packet_loss_pct": loss,
                        "model_confidence": "" if confidence is None else confidence,
                    }
                )

    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
