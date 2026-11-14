import streamlit as st
from ui_theme import apply_theme, render_hero

apply_theme()
render_hero()
st.markdown("## Mission overview")
st.caption("Your central workspace for astronaut health and mission-environment monitoring.")
st.info("Prototype console · Values depend on data entered during this session. This is not a certified spacecraft monitoring system or medical device.")
radiation_count = len(st.session_state.get("radiation_history", []))
crew_records = len(st.session_state.get("crew_readings", []))
try:
    from astro_agent import agent
    health_profiles = len(agent.load_profiles())
except Exception:
    health_profiles = 0
a, b, c = st.columns(3)
a.metric("Radiation readings", radiation_count)
b.metric("Crew / environment records", crew_records)
c.metric("Demo astronaut profiles", health_profiles)
st.markdown("### Explore Cosmo Care")
st.markdown("Choose a workspace below to open its tools.")
pages = [
    ("☢️ Radiation monitoring", "Record detector CPS readings, inspect trends and review count-rate anomalies.", "Radiation Monitoring"),
    ("🫀 Crew & environment", "Enter crew physiological and spacecraft environmental readings.", "Crew & Environment"),
    ("🥗 Personalized health", "Manage astronaut profiles, explore tailored exercise and diet suggestions, and record examinations.", "Personalized Health"),
    ("📊 Reports & data", "Review session records and export data for your demonstration.", "Reports & Data"),
]
cols = st.columns(2)
for i, (title, desc, page_name) in enumerate(pages):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"#### {title}")
            st.write(desc)
            if st.button("Open workspace →", key=f"open_{i}", use_container_width=True):
                st.session_state.cosmo_selected_page = page_name
                st.rerun()
st.divider()
st.caption("COSMO CARE · Astronaut health and mission safety prototype")
