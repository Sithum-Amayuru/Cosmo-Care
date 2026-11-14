from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND = Path(__file__).parent / "frontend"
_component = components.declare_component("cosmo_camera", path=str(_FRONTEND))

DEFAULT = {
    "status": "idle",
    "loggedIn": False,
    "faceDetected": False,
    "expression": None,
    "totals": {},
    "prompt": None,
    "promptAction": None,
    "error": "",
}


def cosmo_camera(
    key="cosmo_camera",
    login_seconds=3,
    prompt_seconds=10,
    prompt_labels=("sadness", "anger", "fear"),
    model_url="./emotion-ferplus-8.onnx",
    active=True,
):
    """Browser-side face detection + FER+ expression estimation.

    Returns a dict (see DEFAULT). Video never leaves the user's device.
    Set active=False to switch the camera off (e.g. on logout).
    """
    return _component(
        loginSeconds=login_seconds,
        promptSeconds=prompt_seconds,
        promptLabels=list(prompt_labels),
        modelUrl=model_url,
        active=active,
        key=key,
        default=DEFAULT,
    )
