"""Safe access layer for the imported mission backend prototype.

No fictional crew, synthetic telemetry, or sample inventory is inserted unless
an explicit demo-seeding option is requested by a developer.
"""
from functools import lru_cache
from pathlib import Path
import os

from .logic import (
    AstronautVitals,
    BioAstronauticsLogic,
    DatabaseManager,
    DeepSpaceSupplyEngine,
    RadiationMonitorLogic,
)


def get_database_path() -> str:
    """Return an explicitly configured path, or a local project database path."""
    configured = os.environ.get("COSMO_CARE_DB_PATH")
    if configured:
        return configured
    return str(Path(__file__).resolve().parent / "cosmo_care.db")


@lru_cache(maxsize=1)
def get_database() -> DatabaseManager:
    """Create the shared database manager without seeding fictional demo data."""
    return DatabaseManager(db_name=get_database_path(), seed_demo_data=False)


def get_prototype_triage(vitals: AstronautVitals) -> dict:
    """Run the retained experimental engine but suppress unvalidated treatment steps."""
    result = BioAstronauticsLogic.evaluate_triage(vitals)
    return {
        "astronaut_id": result.get("astronaut_id"),
        "phase_name": result.get("phase_name"),
        "status_level": result.get("status_level"),
        "diagnosis": result.get("diagnosis"),
        "explanation": result.get("explanation"),
        "z_scores": result.get("z_scores"),
        "hemodynamics": result.get("hemodynamics"),
        "verification": result.get("verification"),
        "prototype_only": True,
        "safety_notice": (
            "Experimental simulation only. This output is not a medical diagnosis, "
            "medical clearance, or treatment recommendation. Do not act on it; "
            "use the mission's approved medical procedures and qualified clinicians."
        ),
    }


__all__ = [
    "AstronautVitals",
    "BioAstronauticsLogic",
    "DatabaseManager",
    "DeepSpaceSupplyEngine",
    "RadiationMonitorLogic",
    "get_database",
    "get_database_path",
    "get_prototype_triage",
]
