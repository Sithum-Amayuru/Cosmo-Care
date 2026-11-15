from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND = Path(__file__).parent / "frontend"
_component = components.declare_component("cosmo_voice", path=str(_FRONTEND))


def cosmo_voice(response_text="", response_id=0, key="cosmo_voice", active=True):
    """Browser voice interface: speech recognition plus spoken AI responses."""
    return _component(
        responseText=response_text,
        responseId=response_id,
        active=active,
        key=key,
        default=None,
    )
