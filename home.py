import streamlit as st
from ui_theme import apply_theme, render_hero

apply_theme()
render_hero()

st.markdown("## Mission overview")
st.caption("A clear snapshot of crew wellbeing and spacecraft monitoring activity.")
st.info(
    "Cosmo Care is a hackathon research prototype. Measurements may be simulated, "
    "and its warning rules are not validated for real mission or medical decisions."
)

# Crew cards use the latest analysis snapshots available in this browser session.
crew_history = st.session_state.get("mission_intel_history", [])
crew_ids = [("Astronaut 1", "AST-001"), ("Astronaut 2", "AST-002")]
st.markdown("### Crew at a glance")
crew_cols = st.columns(2)
for col, (name, crew_id) in zip(crew_cols, crew_ids):
    records = [r for r in crew_history if r.get("astronaut_id") == crew_id]
    latest = records[-1] if records else None
    with col:
        with st.container(border=True):
            st.markdown(f"#### {name}")
            st.caption(crew_id)
            if not latest:
                st.markdown("### ⚪ No recent reading")
                st.write("Run a crew health check to generate a sample status.")
            else:
                status = str(latest.get("prototype_label", "UNKNOWN")).upper()
                if status == "NOMINAL":
                    st.markdown("### 🟢 Normal")
                    st.write("No unusual pattern was flagged in the latest simulated check.")
                elif status == "ADVISORY":
                    st.markdown("### 🟠 Needs attention")
                    st.write("The latest simulated readings triggered a review flag.")
                elif status == "MEDICAL HOLD":
                    st.markdown("### 🔴 High priority")
                    st.write("The experimental algorithm flagged a pattern for qualified review.")
                else:
                    st.markdown("### ⚪ Unable to assess")
                    st.write("The latest result needs technical review.")
                st.caption(f"Last sample: {latest.get('timestamp', 'Time unavailable')}")
            st.button(
                "Open health check",
                key=f"home_health_{crew_id}",
                use_container_width=True,
                on_click=_open_crew_health,
                args=(name,),
            )

st.divider()
st.markdown("### Mission activity")
radiation_count = len(st.session_state.get("radiation_history", []))
crew_records = len(st.session_state.get("crew_readings", []))
intel_count = len(crew_history)
a, b, c = st.columns(3)
a.metric("Radiation readings", radiation_count, help="Detector samples recorded in this session.")
b.metric("Crew observations", crew_records, help="Simulated wearable and cabin observations.")
c.metric("Health analyses", intel_count, help="Crew health snapshots analysed in this session.")

st.markdown("### Choose a workspace")
st.caption("Open a monitoring area to review readings, run a simulation or export session records.")

def _select_workspace(page_name):
    st.session_state.cosmo_selected_page = page_name


def _open_crew_health(name):
    st.session_state.cosmo_selected_page = "Astronaut Health Intelligence"
    st.session_state.intel_astronaut = name

pages = [
    ("🩺 Crew health", "Understand health-pattern results and explore the technical measurements when needed.", "Astronaut Health Intelligence"),
    ("☢️ Radiation monitoring", "Review detector readings, trends and demonstration alerts.", "Radiation Monitoring"),
    ("🌬️ Cabin conditions", "Explore shared oxygen, carbon dioxide, temperature and humidity readings.", "Crew & Environment"),
    ("🥗 Personalized health", "View astronaut profiles and experimental wellbeing suggestions.", "Personalized Health"),
    ("📋 Daily checkup", "Record a daily wellbeing check-in by voice or form.", "Daily Health Checkup"),
    ("📊 Reports & data", "Review and export records from this session.", "Reports & Data"),
]
for start in range(0, len(pages), 2):
    cols = st.columns(2)
    for col, (title, desc, page_name) in zip(cols, pages[start:start + 2]):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {title}")
                st.write(desc)
                st.button(
                    "Open workspace →",
                    key=f"open_{page_name}",
                    use_container_width=True,
                    on_click=_select_workspace,
                    args=(page_name,),
                )

st.divider()
st.caption("COSMO CARE · Astronaut health and mission-safety research prototype")
