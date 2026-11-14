import streamlit as st
from streamlit_webrtc import webrtc_streamer
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="COSMO CARE | Mission Control",
    page_icon="🛰️",
    layout="wide",
)

from modules.face_login import FaceDetectionProcessor

# Session flags are deliberately limited to this browser session.
st.session_state.setdefault("cosmo_authenticated", False)
st.session_state.setdefault("cosmo_camera_requested", False)

st.title("COSMO CARE")
st.caption("Astronaut health and mission-safety monitoring prototype")

# Keep the webcam component in the same location on every page so that the
# browser camera stream remains active while the user navigates the app.
with st.sidebar:
    st.markdown("## 🛰️ Mission access")
    st.caption("Face-presence demo login")

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
        )

        if camera_ctx.state.playing:
            # Refresh the Python UI to read the latest thread-safe detector state.
            st_autorefresh(interval=1000, key="cosmo-camera-status-refresh")

            processor = camera_ctx.video_processor
            if processor:
                # Expression inference is enabled only after the demo login succeeds.
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
                            "This is an estimate, not a measure of actual emotion."
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

                if st.button("Log out", use_container_width=True):
                    st.session_state.cosmo_authenticated = False
                    st.session_state.cosmo_camera_requested = False
                    st.rerun()
            elif login_ready:
                st.success("Face check passed. You can now enter Cosmo Care.")
                st.caption("You do not need to keep your face in the camera.")
                if st.button("Enter Cosmo Care", type="primary", use_container_width=True):
                    st.session_state.cosmo_authenticated = True
                    st.rerun()
            elif face_detected:
                st.info(
                    f"Keep your face visible briefly: "
                    f"{min(detection_seconds, 3.0):.1f} / 3.0 seconds"
                )
            else:
                st.warning("No face currently detected. Look towards the camera.")

        else:
            st.warning(
                "Camera is not streaming. Check browser permission and press START "
                "in the camera panel."
            )
            if st.button("Cancel camera", use_container_width=True):
                st.session_state.cosmo_camera_requested = False
                st.rerun()

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
    pages = [
        st.Page("home.py", title="Mission Overview", icon="🏠", default=True),
        st.Page("pages/radiation_monitoring.py", title="Radiation Monitoring", icon="☢️"),
        st.Page("pages/crew_environment.py", title="Crew & Environment", icon="🫀"),
        st.Page("pages/personalized_health.py", title="Personalized Health", icon="🥗"),
        st.Page("pages/reports_and_data.py", title="Reports & Data", icon="📊"),
    ]
    navigation = st.navigation(pages, position="sidebar", expanded=True)
    navigation.run()
