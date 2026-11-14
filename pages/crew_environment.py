import streamlit as st
import pandas as pd
from datetime import datetime
from ui_theme import apply_theme
st.set_page_config(page_title="Crew & Environment | COSMO CARE", page_icon="🫀", layout="wide")
apply_theme()
with st.sidebar:
    st.markdown("## MISSION NAVIGATION")
    st.page_link("app.py", label="Mission overview", icon="🏠")
    st.page_link("pages/radiation_monitoring.py", label="Radiation monitoring", icon="☢️")
    st.page_link("pages/crew_environment.py", label="Crew & environment", icon="🫀")
    st.page_link("pages/personalized_health.py", label="Personalized health", icon="🥗")
    st.page_link("pages/reports_and_data.py", label="Reports & data", icon="📊")
st.title("Crew & environment")
st.caption("Enter physiological observations and spacecraft environmental measurements.")
if "crew_readings" not in st.session_state: st.session_state.crew_readings = []
with st.form("crew_environment_form"):
    st.subheader("Crew member")
    astronaut_id = st.text_input("Astronaut ID", "AST-001")
    source = st.selectbox("Data source", ["Simulated demonstration data", "Manually entered readings"])
    left, right = st.columns(2)
    with left:
        st.markdown("#### Physiological observations")
        heart_rate = st.number_input("Heart rate (bpm)", min_value=0.0, value=70.0)
        sleep = st.number_input("Sleep in last 24 hours (hours)", min_value=0.0, max_value=24.0, value=8.0)
        activity = st.slider("Activity level (demo index)", 0, 100, 50)
    with right:
        st.markdown("#### Spacecraft environment")
        oxygen = st.number_input("Oxygen (%)", min_value=0.0, max_value=100.0, value=20.9)
        co2 = st.number_input("Carbon dioxide (ppm)", min_value=0.0, value=1000.0)
        temperature = st.number_input("Temperature (°C)", value=22.0)
        humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=45.0)
        pressure = st.number_input("Pressure (kPa)", min_value=0.0, value=101.0)
    submitted = st.form_submit_button("Save observation", type="primary")
if submitted:
    st.session_state.crew_readings.append({"timestamp": datetime.now().isoformat(timespec="seconds"), "astronaut_id": astronaut_id, "source": source, "heart_rate_bpm": heart_rate, "sleep_hours": sleep, "activity_demo_index": activity, "oxygen_percent": oxygen, "co2_ppm": co2, "temperature_c": temperature, "humidity_percent": humidity, "pressure_kpa": pressure})
    st.success("Observation saved in this session.")
if st.session_state.crew_readings:
    latest = st.session_state.crew_readings[-1]
    st.subheader("Latest recorded observation")
    x1, x2, x3 = st.columns(3)
    x1.metric("Heart rate", f'{latest["heart_rate_bpm"]:.1f} bpm')
    x2.metric("Sleep", f'{latest["sleep_hours"]:.1f} h')
    x3.metric("CO₂", f'{latest["co2_ppm"]:.0f} ppm')
    st.dataframe(pd.DataFrame(st.session_state.crew_readings), use_container_width=True, hide_index=True)
    st.download_button("Export crew & environment records", pd.DataFrame(st.session_state.crew_readings).to_csv(index=False).encode("utf-8"), "cosmo_care_crew_environment.csv", "text/csv")
else: st.info("No crew or environment observations have been recorded in this session.")
st.caption("Demonstration inputs only. This page does not diagnose medical conditions or determine spacecraft environmental safety.")
