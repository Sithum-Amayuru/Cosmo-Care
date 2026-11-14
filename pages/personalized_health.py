import streamlit as st
from ui_theme import apply_theme
from modules.astronaut_health import render_astronaut_health
st.set_page_config(page_title="Personalized Health | COSMO CARE", page_icon="🥗", layout="wide")
apply_theme()
with st.sidebar:
    st.markdown("## MISSION NAVIGATION")
    st.page_link("app.py", label="Mission overview", icon="🏠")
    st.page_link("pages/radiation_monitoring.py", label="Radiation monitoring", icon="☢️")
    st.page_link("pages/crew_environment.py", label="Crew & environment", icon="🫀")
    st.page_link("pages/personalized_health.py", label="Personalized health", icon="🥗")
    st.page_link("pages/reports_and_data.py", label="Reports & data", icon="📊")
st.title("Personalized astronaut health")
st.caption("Crew profiles, mission-aware exercise and nutrition suggestions, and medical examination records.")
st.warning("Demonstration content only. Exercise and diet suggestions and examination reference ranges are not validated astronaut medical guidance.")
render_astronaut_health()
