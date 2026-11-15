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

with st.sidebar:
    st.markdown("## 🛰️ Mission access")
    st.caption("Face-presence demo login")
    camera_slot = st.container()

    with camera_slot:
        cam = cosmo_camera(key=f"cosmo-camera-{st.session_state.cosmo_cam_gen}")

    st.session_state.cosmo_expression_totals = cam["totals"]

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
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"]:has(#floating-cosmo-anchor) {
        position: fixed !important;
        bottom: 24px !important;
        right: 28px !important;
        width: auto !important;
        z-index: 99999 !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 12px !important;
        background: transparent !important;
    }

    div[data-testid="stHorizontalBlock"]:has(#floating-cosmo-anchor) > div {
        width: auto !important;
        flex: 0 0 auto !important;
    }

    div[data-testid="stHorizontalBlock"]:has(#floating-cosmo-anchor) div[data-testid="stPopover"] > div > button {
        height: 54px !important;
        border-radius: 30px !important;
        background: linear-gradient(95deg, #00d2ff 0%, #6366f1 55%, #9b5de5 100%) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255, 255, 255, 0.85) !important;
        padding: 0 24px !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        transition: none !important;
        animation: none !important;
    }

    div[data-testid="stHorizontalBlock"]:has(#floating-cosmo-anchor) div[data-testid="stPopover"] > div > button svg {
        display: none !important;
    }

    div[data-testid="stPopoverBody"] {
        width: 390px !important;
        max-width: 92vw !important;
        border-radius: 16px !important;
        padding: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.success("Welcome to the Cosmo Care mission console.")

    import os

    from modules.astro_agent_companion import get_astro_agent_response

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

    if not st.session_state.cosmo_chat_open:
        if st.button("💬 Talk to Cosmo", type="primary", key="cosmo_manual_chat"):
            st.session_state.cosmo_chat_open = True
            st.session_state.cosmo_pending_mood = None
            st.session_state.cosmo_mood_checkin_started = False
            st.rerun()

    if st.session_state.cosmo_chat_open:
        st.markdown("### 💬 Cosmo Care companion")
        st.caption("A friendly conversation partner — not a mental-health diagnostic tool.")
        st.caption("Voice-first companion with text chat as a fallback.")

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

    (chat_col,) = st.columns([1])
    with chat_col:
        st.markdown('<div id="floating-cosmo-anchor"></div>', unsafe_allow_html=True)
        with st.popover("💬 Mental Health AI"):
            st.markdown("### 💬 Cosmo Care companion")
            st.caption("A friendly conversation partner — not a mental-health diagnostic tool.")

            chat_container = st.container(height=280)
            with chat_container:
                for message in st.session_state.cosmo_chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            with st.form("cosmo_popup_chat_form", clear_on_submit=True):
                c_in, c_btn = st.columns([4, 1])
                with c_in:
                    user_message = st.text_input(
                        "Talk to your companion...",
                        placeholder="Talk to your companion...",
                        label_visibility="collapsed",
                    )
                with c_btn:
                    submitted = st.form_submit_button("➤")

                if submitted and user_message.strip():
                    clean_msg = user_message.strip()
                    st.session_state.cosmo_chat_history.append(
                        {"role": "user", "content": clean_msg}
                    )
                    try:
                        reply = get_astro_agent_response(
                            st.session_state.cosmo_chat_history[:-1],
                            user_message=clean_msg,
                        )
                        st.session_state.cosmo_chat_history.append(
                            {"role": "assistant", "content": reply}
                        )
                    except RuntimeError as exc:
                        st.error(str(exc))
                    st.rerun()
