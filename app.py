import runpy
import streamlit as st
from streamlit_webrtc import webrtc_streamer
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="COSMO CARE | Mission Control",
    page_icon="🛰️",
    layout="wide",
)

from modules.face_login import FaceDetectionProcessor

st.session_state.setdefault("cosmo_authenticated", False)
st.session_state.setdefault("cosmo_camera_requested", False)
st.session_state.setdefault("cosmo_selected_page", "Mission Overview")

st.title("COSMO CARE")
st.caption("Astronaut health and mission-safety monitoring prototype")

# Keep the WebRTC component mounted on this single Streamlit page.
# st.navigation() changes the active page hash and can terminate WebRTC workers
# when the user enters a multipage route. We use in-page routing below instead.
with st.sidebar:
    st.markdown("## 🛰️ Mission access")
    st.caption("Face-presence demo login")

    # Logout is independent of WebRTC connection state, so it remains available
    # even if the camera temporarily disconnects.
    if st.session_state.cosmo_authenticated:
        st.success("Demo session active")
        if st.button("Log out", key="cosmo_logout", use_container_width=True):
            st.session_state.cosmo_authenticated = False
            st.session_state.cosmo_camera_requested = False
            st.session_state.cosmo_selected_page = "Mission Overview"
            st.rerun()

    if not st.session_state.cosmo_camera_requested:
        st.info("Start the camera to check for a visible face.")
        if st.button("Start camera", type="primary", use_container_width=True):
            st.session_state.cosmo_camera_requested = True
            st.rerun()
        camera_ctx = None
    else:
        camera_ctx = webrtc_streamer(
            key="cosmo-care-session-camera",
            video_processor_factory=FaceDetectionProcessor,
            media_stream_constraints={"video": True, "audio": False},
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            },
            async_processing=True,
            # Keep the stream active across Streamlit script reruns, including login.
            desired_playing_state=True,
        )

        if camera_ctx.state.playing:
            st_autorefresh(interval=1000, key="cosmo-camera-status-refresh")
            processor = camera_ctx.video_processor
            if processor:
                processor.set_expression_enabled(st.session_state.cosmo_authenticated)
                (
                    face_detected,
                    face_count,
                    login_ready,
                    detection_seconds,
                    expression_label,
                    expression_confidence,
                    expression_status,
                ) = processor.face_status
            else:
                face_detected, face_count = False, 0
                login_ready, detection_seconds = False, 0.0
                expression_label, expression_confidence = "Unavailable", 0.0
                expression_status = "Camera processor is starting."

            if st.session_state.cosmo_authenticated:
                st.success("Demo session active")
                st.caption("Face presence is not required to remain logged in.")
                st.markdown("### 🙂 Live expression estimate")
                if face_detected:
                    if expression_status == "ready":
                        st.metric("Visible expression", expression_label)
                        st.caption(
                            f"Model score: {expression_confidence:.0%}. "
                            "This is a visual estimate, not a measure of actual emotion."
                        )
                    elif expression_status == "loading":
                        st.info("Loading the expression model…")
                    elif expression_status.startswith("error:"):
                        st.warning(
                            "Expression model unavailable. Face detection and login "
                            "can still work. " + expression_status.removeprefix("error:")
                        )
                    else:
                        st.info("Waiting for a face to estimate its visible expression.")
                else:
                    st.info("No face currently visible. Expression estimates are paused.")

            elif login_ready:
                st.success("Face check passed. You can now enter Cosmo Care.")
                st.caption("You do not need to keep your face in the camera.")
                if st.button("Enter Cosmo Care", type="primary", use_container_width=True):
                    # The button event already causes a rerun; do not force a second one.
                    st.session_state.cosmo_authenticated = True
            elif face_detected:
                st.info(
                    f"Keep your face visible briefly: "
                    f"{min(detection_seconds, 3.0):.1f} / 3.0 seconds"
                )
            else:
                st.warning("No face currently detected. Look towards the camera.")
        else:
            # Do not force rapid Streamlit reruns during SDP/ICE negotiation:
            # repeated reruns can interrupt the WebRTC offer/answer handshake.
            # streamlit-webrtc emits component updates as signalling/playing changes.
            if camera_ctx.state.signalling:
                st.info("Establishing the camera connection… Please allow a few seconds.")
            else:
                st.warning(
                    "The camera stream is not active yet. Check browser camera permission "
                    "and the START control in the camera panel. If it still cannot connect, "
                    "the current network may require TURN relay settings."
                )

    st.divider()
    st.caption(
        "Prototype only: this detects face presence, not identity. "
        "Expression labels are visual model estimates, not psychological assessments. "
        "Camera access requires browser permission."
    )

if not st.session_state.cosmo_authenticated:
    st.markdown("## Mission access required")
    st.write(
        "Start the camera from the sidebar and allow browser camera permission. "
        "Keep any face visible for approximately 3 seconds. Once the check passes, "
        "you can enter even if the face is no longer detected."
    )
    st.info(
        "This is not secure authentication: anyone with a visible face can enter. "
        "Astronaut identity recognition and anti-spoofing are future requirements."
    )
else:
    st.success("Welcome to the Cosmo Care mission console.")
    page_options = {
        "Mission Overview": "home.py",
        "Radiation Monitoring": "pages/radiation_monitoring.py",
        "Crew & Environment": "pages/crew_environment.py",
        "Personalized Health": "pages/personalized_health.py",
        "Reports & Data": "pages/reports_and_data.py",
    }
    selected_page = st.sidebar.radio(
        "Mission workspace",
        list(page_options.keys()),
        key="cosmo_selected_page",
    )
    runpy.run_path(page_options[selected_page])
