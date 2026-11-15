"""Radiation count-rate processing for Cosmo Care.

This module processes generic detector event counts (CPS). CPS is not dose rate
and must not be converted to dose without detector-specific calibration.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import random
from statistics import median
from typing import Any, Iterable


def validate_reading(reading: dict[str, Any]) -> tuple[bool, str]:
    """Validate one detector count-rate record."""
    required = ("timestamp", "detector_id", "count_rate_cps")
    missing = [key for key in required if key not in reading]
    if missing:
        return False, f"Missing required field(s): {', '.join(missing)}"

    try:
        value = float(reading["count_rate_cps"])
    except (TypeError, ValueError):
        return False, "count_rate_cps must be a numeric value."

    if value < 0:
        return False, "count_rate_cps cannot be negative."

    try:
        datetime.fromisoformat(str(reading["timestamp"]).replace("Z", "+00:00"))
    except ValueError:
        return False, "timestamp must be a valid ISO-8601 date/time."

    if not str(reading["detector_id"]).strip():
        return False, "detector_id cannot be empty."

    return True, "Valid reading."


def make_reading(
    detector_id: str,
    count_rate_cps: float,
    radiation_type: str = "Unclassified",
    sensor_status: str = "operational",
    timestamp: str | None = None,
    source: str = "simulated",
) -> dict[str, Any]:
    """Create a consistently structured detector reading."""
    reading = {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "detector_id": detector_id.strip(),
        "radiation_type": radiation_type,
        "count_rate_cps": float(count_rate_cps),
        "sensor_status": sensor_status,
        "source": source,
    }
    valid, message = validate_reading(reading)
    if not valid:
        raise ValueError(message)
    return reading


def analyze_readings(
    readings: Iterable[dict[str, Any]],
    anomaly_multiplier: float = 2.0,
    minimum_history: int = 3,
) -> dict[str, Any]:
    """Summarise CPS history and flag increases against prior median.

    The latest reading is compared with the median of preceding readings only.
    This is a simple demo heuristic, not a radiation safety threshold.
    """
    rows = list(readings)
    if anomaly_multiplier <= 1:
        raise ValueError("anomaly_multiplier must be greater than 1.")

    if not rows:
        return {
            "count": 0, "latest_cps": None, "average_cps": None,
            "peak_cps": None, "baseline_cps": None,
            "increase_factor": None, "anomaly": False,
            "message": "No radiation measurements have been recorded.",
        }

    for row in rows:
        valid, message = validate_reading(row)
        if not valid:
            raise ValueError(message)

    values = [float(row["count_rate_cps"]) for row in rows]
    latest = values[-1]
    prior = values[:-1]
    baseline = median(prior) if len(prior) >= minimum_history else None
    factor = (latest / baseline) if baseline and baseline > 0 else None
    anomaly = factor is not None and factor >= anomaly_multiplier

    if baseline is None:
        message = (
            f"Latest reading is {latest:g} CPS. More historical readings are "
            f"needed before a baseline comparison can be made."
        )
    elif anomaly:
        message = (
            f"Count rate is {factor:.2f} times the prior median "
            f"({baseline:g} CPS). Investigate the change and verify detector status."
        )
    else:
        message = (
            f"Latest count rate is {latest:g} CPS; prior-history median is "
            f"{baseline:g} CPS. No configured statistical increase rule was triggered."
        )

    return {
        "count": len(values),
        "latest_cps": latest,
        "average_cps": sum(values) / len(values),
        "peak_cps": max(values),
        "baseline_cps": baseline,
        "increase_factor": factor,
        "anomaly": anomaly,
        "message": message,
    }



def make_simulated_reading(
    previous_readings: Iterable[dict[str, Any]],
    scenario: str = "Normal orbital conditions",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Generate one clearly-labelled synthetic radiation telemetry sample.

    CPS values are illustrative detector-specific counts. Dose-rate values are
    separately simulated; no CPS-to-dose conversion is performed.
    """
    profiles = {
        "Normal orbital conditions": {
            "cps": (8.0, 18.0), "dose": (2.0, 8.0), "radiation": "Mixed background"
        },
        "South Atlantic Anomaly pass": {
            "cps": (35.0, 95.0), "dose": (20.0, 96.0), "radiation": "Proton-rich region"
        },
        "Solar particle event": {
            "cps": (100.0, 280.0), "dose": (80.0, 250.0), "radiation": "Solar energetic particles"
        },
    }
    if scenario not in profiles:
        raise ValueError("Unknown simulation scenario.")

    profile = profiles[scenario]
    cps = random.uniform(*profile["cps"])
    dose_rate = random.uniform(*profile["dose"])

    # Add modest continuity so adjacent samples look like a changing sensor stream.
    previous = list(previous_readings)
    if previous and previous[-1].get("source") == "Simulated sensor":
        prior_cps = float(previous[-1]["count_rate_cps"])
        prior_dose = previous[-1].get("dose_rate_usv_h")
        if prior_dose is not None:
            cps = max(0.1, 0.65 * prior_cps + 0.35 * cps)
            dose_rate = max(0.1, 0.65 * float(prior_dose) + 0.35 * dose_rate)

    interval_minutes = 1.0
    dose_increment_msv = dose_rate * interval_minutes / 60.0 / 1000.0
    previous_cumulative = 0.0
    for row in reversed(previous):
        if row.get("cumulative_session_dose_msv") is not None:
            previous_cumulative = float(row["cumulative_session_dose_msv"])
            break

    status = "operational"
    if random.random() < 0.015:
        status = "warning"

    reading = make_reading(
        detector_id="SIM-RAD-01",
        count_rate_cps=round(cps, 2),
        radiation_type=profile["radiation"],
        sensor_status=status,
        timestamp=timestamp,
        source="Simulated sensor",
    )
    reading.update({
        "scenario": scenario,
        "dose_rate_usv_h": round(dose_rate, 2),
        "dose_increment_msv": round(dose_increment_msv, 6),
        "cumulative_session_dose_msv": round(
            previous_cumulative + dose_increment_msv, 6
        ),
        "sample_interval_minutes": interval_minutes,
    })
    return reading
