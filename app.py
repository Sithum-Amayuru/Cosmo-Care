import base64
from pathlib import Path
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
st.session_state.setdefault("cosmo_current_page", "Mission Overview")
st.session_state.setdefault("cosmo_page_history", [])
st.session_state.setdefault("cosmo_skip_history_update", False)
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
    fallback_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="100%" height="100%">
        <defs>
            <radialGradient id="spaceBg" cx="50%" cy="45%" r="75%">
                <stop offset="0%" stop-color="#071636"/>
                <stop offset="55%" stop-color="#030918"/>
                <stop offset="100%" stop-color="#010308"/>
            </radialGradient>
            <radialGradient id="earthGlow" cx="50%" cy="100%" r="55%">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.85"/>
                <stop offset="35%" stop-color="#0284c7" stop-opacity="0.45"/>
                <stop offset="70%" stop-color="#030918" stop-opacity="0"/>
            </radialGradient>
            <linearGradient id="cyanBlue" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#0284c7"/>
                <stop offset="100%" stop-color="#38bdf8"/>
            </linearGradient>
        </defs>
        <rect width="1920" height="1080" fill="url(#spaceBg)"/>
        <circle cx="250" cy="180" r="1.8" fill="#ffffff" opacity="0.7"/>
        <circle cx="520" cy="120" r="1.4" fill="#38bdf8" opacity="0.8"/>
        <circle cx="1420" cy="160" r="2.0" fill="#ffffff" opacity="0.75"/>
        <circle cx="1680" cy="280" r="1.5" fill="#38bdf8" opacity="0.7"/>
        <circle cx="380" cy="520" r="1.5" fill="#ffffff" opacity="0.6"/>
        <circle cx="1550" cy="540" r="1.8" fill="#ffffff" opacity="0.65"/>
        <ellipse cx="960" cy="1120" rx="980" ry="380" fill="url(#earthGlow)"/>
        <ellipse cx="960" cy="1160" rx="880" ry="290" fill="#041028" stroke="#38bdf8" stroke-width="5"/>
        <g transform="translate(960, 340)">
            <path d="M-190,65 C-250,10 -150,-110 20,-135 C170,-155 240,-40 120,55" fill="none" stroke="url(#cyanBlue)" stroke-width="18" stroke-linecap="round"/>
            <circle cx="0" cy="-35" r="82" fill="#071c3d" stroke="#ffffff" stroke-width="12"/>
            <path d="M-45,-65 C-10,-95 55,-80 65,-25 C70,15 35,35 -15,25 C-55,15 -65,-35 -45,-65 Z" fill="#0c2d5e" stroke="#38bdf8" stroke-width="6"/>
            <circle cx="-48" cy="-22" r="22" fill="#ffffff"/>
            <path d="M135,-125 L145,-98 L172,-88 L145,-78 L135,-51 L125,-78 L98,-88 L125,-98 Z" fill="#ffffff"/>
            <polyline points="-105,68 -45,68 -32,42 -15,92 4,15 24,102 40,68 105,68" fill="none" stroke="#38bdf8" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>
        </g>
        <text x="905" y="575" fill="#ffffff" font-size="92" font-weight="800" font-family="Segoe UI, Arial, sans-serif" text-anchor="end" letter-spacing="6">COSMO</text>
        <text x="945" y="575" fill="#22d3ee" font-size="92" font-weight="800" font-family="Segoe UI, Arial, sans-serif" text-anchor="start" letter-spacing="6">CARE</text>
        <text x="960" y="645" fill="#cbd5e1" font-size="28" font-weight="500" font-family="Segoe UI, Arial, sans-serif" text-anchor="middle" letter-spacing="14">HEALTHCARE BEYOND EARTH</text>
    </svg>
    """
    b64_svg = base64.b64encode(fallback_svg.strip().encode("utf-8")).decode()
    bg_url = f"data:image/svg+xml;base64,{b64_svg}"

    for candidate in (
        Path(__file__).parent / "cosmo_login_bg.jpg",
        Path(__file__).parent / "cosmo_login_bg.png",
        Path(__file__).parent / "image_6b0485.jpg",
        Path(__file__).parent / "image_6b0485.png",
        Path(__file__).parent / "galaxy_bg.jpg",
        Path(__file__).parent / "assets" / "cosmo_login_bg.jpg",
        Path(__file__).parent / "assets" / "image_6b0485.jpg",
        Path(__file__).parent / "assets" / "galaxy_bg.jpg",
    ):
        if candidate.exists():
            mime = "image/png" if candidate.suffix.lower() == ".png" else "image/jpeg"
            b64_img = base64.b64encode(candidate.read_bytes()).decode()
            bg_url = f"data:{mime};base64,{b64_img}"
            break

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(3, 8, 20, 0.45), rgba(3, 8, 20, 0.55)),
                        url("{bg_url}") no-repeat center center fixed !important;
            background-size: cover !important;
        }}
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

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
        "Astronaut Health Intelligence": "views/mission_intelligence.py",
        "Daily Health Checkup": "views/health_checkup.py",
        "Radiation Monitoring": "views/radiation_monitoring.py",
        "Crew & Environment": "views/crew_environment.py",
        "Personalized Health": "views/personalized_health.py",
        "Reports & Data": "views/reports_and_data.py",
    }
    def _cosmo_go_back():
        history = st.session_state.get("cosmo_page_history", [])
        if history:
            st.session_state.cosmo_selected_page = history.pop()
        st.session_state.cosmo_skip_history_update = True

    def _cosmo_go_home():
        st.session_state.cosmo_selected_page = "Mission Overview"
        st.session_state.cosmo_page_history = []
        st.session_state.cosmo_skip_history_update = True

    selected_page = st.session_state.get("cosmo_selected_page", "Mission Overview")
    if selected_page not in page_options:
        selected_page = "Mission Overview"
        st.session_state.cosmo_selected_page = selected_page

    # Keep a simple navigation history for the global Back button.
    if selected_page != st.session_state.cosmo_current_page:
        if not st.session_state.cosmo_skip_history_update:
            st.session_state.cosmo_page_history.append(
                st.session_state.cosmo_current_page
            )
        st.session_state.cosmo_current_page = selected_page
    st.session_state.cosmo_skip_history_update = False

    nav_back, nav_home, nav_reset, nav_space = st.columns([1, 1, 1.2, 4.8])
    with nav_back:
        st.button(
            "← Back",
            key="cosmo_global_back",
            disabled=not st.session_state.cosmo_page_history,
            on_click=_cosmo_go_back,
            use_container_width=True,
        )
    with nav_home:
        st.button(
            "⌂ Home",
            key="cosmo_global_home",
            on_click=_cosmo_go_home,
            use_container_width=True,
        )
    with nav_reset:
        if st.button("↻ Reset", key="cosmo_global_reset", use_container_width=True):
            st.session_state.cosmo_reset_requested = True

    if st.session_state.get("cosmo_reset_requested", False):
        st.warning(
            "Reset will log you out and permanently clear saved prototype health, "
            "checkup, chat, astronaut-profile and monitoring records from the app database. "
            "This cannot be undone."
        )
        confirm_col, cancel_col, _ = st.columns([1.2, 1, 5])
        with confirm_col:
            if st.button("Confirm reset", type="primary", key="cosmo_confirm_reset"):
                try:
                    from modules.mission_backend import clear_health_records

                    clear_health_records()
                    next_camera_generation = st.session_state.get("cosmo_cam_gen", 0) + 1
                    st.session_state.clear()
                    st.session_state.cosmo_authenticated = False
                    st.session_state.cosmo_cam_gen = next_camera_generation
                    st.rerun()
                except Exception as exc:
                    st.error(f"Reset could not be completed: {exc}")
        with cancel_col:
            if st.button("Cancel", key="cosmo_cancel_reset"):
                st.session_state.cosmo_reset_requested = False
                st.rerun()

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
