import runpy

import streamlit as st

st.set_page_config(
    page_title="COSMO CARE | Mission Control",
    page_icon="🛰️",
    layout="wide",
)

from cosmo_camera import cosmo_camera
from cosmo_voice import cosmo_voice

st.session_state.setdefault("cosmo_authenticated", False)
st.session_state.setdefault("cosmo_selected_page", "Mission Overview")
st.session_state.setdefault("cosmo_cam_gen", 0)
st.session_state.setdefault("cosmo_chat_open", False)
st.session_state.setdefault("cosmo_last_prompt_action", None)
st.session_state.setdefault("cosmo_expression_totals", {})
st.session_state.setdefault("cosmo_pending_mood", None)
st.session_state.setdefault("cosmo_chat_history", [])
st.session_state.setdefault("cosmo_mood_checkin_started", False)
st.session_state.setdefault("cosmo_voice_response_text", "")
st.session_state.setdefault("cosmo_voice_response_id", 0)
st.session_state.setdefault("cosmo_last_voice_event_id", None)

st.title("COSMO CARE")
st.caption("Astronaut health and mission-safety monitoring prototype")

# The camera runs in the browser (face detection + expression estimate), so video
# never leaves the user's device. The component lives in a fixed container at the
# top of the sidebar so it stays mounted while the user switches pages in-page.
with st.sidebar:
    st.markdown("## 🛰️ Mission access")
    st.caption("Face-presence demo login")
    camera_slot = st.container()

    with camera_slot:
        # Changing the key (on logout) removes the old component, which releases the camera.
        cam = cosmo_camera(key=f"cosmo-camera-{st.session_state.cosmo_cam_gen}")

    # Share the latest expression totals with the dashboard pages.
    st.session_state.cosmo_expression_totals = cam["totals"]

    # The astronaut chose to talk to the support assistant (handled once per click).
    if (
        cam["promptAction"] == "accepted"
        and st.session_state.cosmo_last_prompt_action != "accepted"
    ):
        st.session_state.cosmo_chat_open = True
        st.session_state.cosmo_pending_mood = cam.get("moodEvent")
        st.session_state.cosmo_mood_checkin_started = False
    st.session_state.cosmo_last_prompt_action = cam["promptAction"]

    if st.session_state.cosmo_authenticated:
        st.success("Demo session active")
        st.caption("Face presence is not required to remain logged in.")
        if cam["status"] == "running":
            st.caption(
                "The live expression estimate is shown on the camera panel. "
                "It is a visual estimate, not a measure of actual emotion."
            )
            seen = {k: v for k, v in cam["totals"].items() if v > 0}
            if seen:
                with st.expander("Expression time (seconds, updates about every 20 s)"):
                    st.write(seen)
        if st.button("Log out", key="cosmo_logout", use_container_width=True):
            st.session_state.cosmo_authenticated = False
            st.session_state.cosmo_selected_page = "Mission Overview"
            st.session_state.cosmo_chat_open = False
            st.session_state.cosmo_chat_history = []
            st.session_state.cosmo_pending_mood = None
            st.session_state.cosmo_mood_checkin_started = False
            st.session_state.cosmo_voice_response_text = ""
            st.session_state.cosmo_voice_response_id = 0
            st.session_state.cosmo_last_voice_event_id = None
            st.session_state.cosmo_cam_gen += 1
            st.rerun()
    elif cam["loggedIn"]:
        st.success("Face check passed. You can now enter Cosmo Care.")
        st.caption("You do not need to keep your face in the camera.")
        if st.button("Enter Cosmo Care", type="primary", use_container_width=True):
            # The button event already causes a rerun; do not force a second one.
            st.session_state.cosmo_authenticated = True
    elif cam["status"] == "running":
        st.info("Keep your face visible for about 3 seconds.")
    else:
        st.info("Tick the consent box, press Start camera and allow camera permission.")

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

    # Manual companion access: astronauts can start a conversation at any time,
    # independently of the camera's uncertain expression estimate.
    if not st.session_state.cosmo_chat_open:
        if st.button("💬 Talk to Cosmo", type="primary", key="cosmo_manual_chat"):
            st.session_state.cosmo_chat_open = True
            st.session_state.cosmo_pending_mood = None
            st.session_state.cosmo_mood_checkin_started = False
            st.rerun()

    if st.session_state.cosmo_chat_open:
        import os

        from modules.astro_agent_companion import get_astro_agent_response

        # Streamlit Cloud secrets are exposed through st.secrets, not automatically
        # as environment variables. Copy the OpenRouter settings into this process.
        try:
            if st.secrets.get("OPENROUTER_API_KEY"):
                os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
            if st.secrets.get("OPENROUTER_MODEL"):
                os.environ["OPENROUTER_MODEL"] = st.secrets["OPENROUTER_MODEL"]
            if st.secrets.get("GROQ_API_KEY"):
                os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
            if st.secrets.get("GROQ_MODEL"):
                os.environ["GROQ_MODEL"] = st.secrets["GROQ_MODEL"]
        except Exception:
            pass

        st.markdown("### 💬 Cosmo Care companion")
        st.caption("A friendly conversation partner — not a mental-health diagnostic tool.")

        st.caption("Voice-first companion with text chat as a fallback.")

        # The browser component handles microphone input and spoken playback.
        # Only replies to voice-originated messages are sent back for speech.
        voice_event = cosmo_voice(
            response_text=st.session_state.cosmo_voice_response_text,
            response_id=st.session_state.cosmo_voice_response_id,
            key="cosmo_voice_interface",
            active=True,
        )

        if (
            isinstance(voice_event, dict)
            and voice_event.get("type") == "transcript"
            and voice_event.get("eventId") != st.session_state.cosmo_last_voice_event_id
        ):
            st.session_state.cosmo_last_voice_event_id = voice_event.get("eventId")
            spoken_message = (voice_event.get("text") or "").strip()
            if spoken_message:
                st.session_state.cosmo_chat_history.append(
                    {"role": "user", "content": spoken_message}
                )
                try:
                    voice_reply = get_astro_agent_response(
                        st.session_state.cosmo_chat_history[:-1],
                        user_message=spoken_message,
                    )
                    st.session_state.cosmo_chat_history.append(
                        {"role": "assistant", "content": voice_reply}
                    )
                    st.session_state.cosmo_voice_response_text = voice_reply
                    st.session_state.cosmo_voice_response_id += 1
                except RuntimeError as exc:
                    st.session_state.cosmo_voice_response_text = (
                        "I'm having trouble connecting right now. Please try again in a moment."
                    )
                    st.session_state.cosmo_voice_response_id += 1
                    st.error(str(exc))
                st.rerun()

        # Start one gentle greeting when the companion is opened, whether by
        # accepting a camera prompt or by using the manual Talk to Cosmo button.
        if (
            not st.session_state.cosmo_mood_checkin_started
            and (
                st.session_state.cosmo_pending_mood is not None
                or not st.session_state.cosmo_chat_history
            )
        ):
            with st.spinner("Your companion is getting ready..."):
                try:
                    opening = get_astro_agent_response(
                        st.session_state.cosmo_chat_history,
                        mood_context=st.session_state.cosmo_pending_mood,
                    )
                    st.session_state.cosmo_chat_history.append(
                        {"role": "assistant", "content": opening}
                    )
                    st.session_state.cosmo_voice_response_text = opening
                    st.session_state.cosmo_voice_response_id += 1
                    st.session_state.cosmo_mood_checkin_started = True
                    st.session_state.cosmo_pending_mood = None
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
                    st.info(
                        "If OpenRouter is rate-limited, add GROQ_API_KEY to Streamlit "
                        "app secrets to enable the backup provider. At least one valid "
                        "provider key is required. Never put API keys in source code."
                    )

        for message in st.session_state.cosmo_chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_message = st.chat_input("Talk to your companion...", key="cosmo_chat_input")
        if user_message:
            st.session_state.cosmo_chat_history.append(
                {"role": "user", "content": user_message}
            )
            try:
                reply = get_astro_agent_response(
                    st.session_state.cosmo_chat_history[:-1],
                    user_message=user_message,
                )
                st.session_state.cosmo_chat_history.append(
                    {"role": "assistant", "content": reply}
                )
            except RuntimeError as exc:
                st.error(str(exc))
            st.rerun()

        left, right = st.columns(2)
        with left:
            if st.button("Close assistant", key="cosmo_close_chat"):
                st.session_state.cosmo_chat_open = False
                st.rerun()
        with right:
            if st.button("New conversation", key="cosmo_new_chat"):
                st.session_state.cosmo_chat_history = []
                st.session_state.cosmo_pending_mood = None
                st.session_state.cosmo_mood_checkin_started = False
                st.session_state.cosmo_voice_response_text = ""
                st.rerun()
        st.divider()

    page_options = {
        "Mission Overview": "home.py",
        "Radiation Monitoring": "views/radiation_monitoring.py",
        "Crew & Environment": "views/crew_environment.py",
        "Personalized Health": "views/personalized_health.py",
        "Reports & Data": "views/reports_and_data.py",
    }
    selected_page = st.sidebar.radio(
        "Mission workspace",
        list(page_options.keys()),
        key="cosmo_selected_page",
    )
    runpy.run_path(page_options[selected_page])
