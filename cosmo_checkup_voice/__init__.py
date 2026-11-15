from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND = Path(__file__).parent / "frontend"
_component = components.declare_component("cosmo_checkup_voice", path=str(_FRONTEND))


def cosmo_checkup_voice(questions, run_id, key="cosmo_checkup_voice"):
    """Run a browser-based spoken checkup and return the completed answers."""
    return _component(questions=questions, runId=run_id, key=key, default=None)
