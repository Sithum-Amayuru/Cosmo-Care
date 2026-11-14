import streamlit as st
from streamlit_webrtc import webrtc_streamer

from modules.face_login import FaceDetectionProcessor

st.set_page_config(
    page_title="Face Detection | COSMO CARE",
    page_icon="🛰️",
    layout="wide",
)

st.title("Face Detection Login")
st.caption("Prototype — detects the presence of a face; it does not identify or authenticate an astronaut.")

st.info(
    "Allow camera access when your browser asks. Your webcam stream is processed "
    "for face detection during this test. No face images are intentionally saved."
)

ctx = webrtc_streamer(
    key="cosmo-care-face-login",
    video_processor_factory=FaceDetectionProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

st.markdown("### Detection status")

if ctx.state.playing and ctx.video_processor:
    face_detected, face_count = ctx.video_processor.face_status

    if face_detected:
        st.success(f"Face detected. Faces visible: {face_count}")
        st.session_state["face_demo_ready"] = True
    else:
        st.warning("No face detected yet. Position your face in front of the camera.")
        st.session_state["face_demo_ready"] = False

    st.caption(
        "If the status does not refresh immediately, use the button below to check "
        "the latest camera frame."
    )
    if st.button("Check face status"):
        st.rerun()

elif ctx.state.playing:
    st.info("Starting the camera processor…")
else:
    st.warning("Camera is not running. Select START above and grant browser camera permission.")

if st.session_state.get("face_demo_ready", False):
    st.success("Demo entry condition met.")
    st.write("The next development step will connect this result to the application session.")

st.divider()
st.caption(
    "Security note: this is presence detection only. Anyone whose face is visible may "
    "pass this prototype check. It is not a secure login system."
)
