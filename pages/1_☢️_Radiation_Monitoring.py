import streamlit as st
import pandas as pd
from modules.radiation_monitor import make_reading, analyze_readings
from ui_theme import apply_theme
st.set_page_config(page_title="Radiation Monitoring | COSMO CARE", page_icon="☢️", layout="wide")
apply_theme()
with st.sidebar:
    st.markdown("## MISSION NAVIGATION")
    st.page_link("app.py", label="Mission overview", icon="🏠")
    st.page_link("pages/1_☢️_Radiation_Monitoring.py", label="Radiation monitoring", icon="☢️")
    st.page_link("pages/2_🫀_Crew_and_Environment.py", label="Crew & environment", icon="🫀")
    st.page_link("pages/3_🥗_Personalized_Health.py", label="Personalized health", icon="🥗")
    st.page_link("pages/4_📊_Reports_and_Data.py", label="Reports & data", icon="📊")
st.title("Radiation monitoring")
st.caption("Detector input, count-rate history and statistical anomaly review.")
st.warning("CPS is an instrument count rate, not dose rate or absorbed dose. Do not convert CPS to µSv/h without detector-specific calibration.")
if "radiation_history" not in st.session_state: st.session_state.radiation_history = []
with st.container(border=True):
    st.subheader("Record a detector reading")
    with st.form("radiation_input"):
        c1, c2 = st.columns(2)
        with c1:
            detector_id = st.text_input("Detector ID", "RAD-01")
            radiation_type = st.selectbox("Radiation type reported", ["Unclassified", "Neutron", "Gamma", "Proton", "Other"])
        with c2:
            cps = st.number_input("Count rate (counts/second)", min_value=0.0, value=10.0, step=1.0)
            sensor_status = st.selectbox("Detector status", ["operational", "warning", "fault"])
        submitted = st.form_submit_button("Record reading", type="primary")
    if submitted:
        try:
            item = make_reading(detector_id=detector_id, count_rate_cps=cps, radiation_type=radiation_type, sensor_status=sensor_status, source="Manual entry")
            st.session_state.radiation_history.append(item)
            st.success("Reading recorded for this session.")
        except ValueError as exc: st.error(str(exc))
multiplier = st.slider("Anomaly multiplier", 1.1, 10.0, 2.0, 0.1, help="Demo heuristic compared with the median of prior readings; not a radiation safety limit.")
analysis = analyze_readings(st.session_state.radiation_history, anomaly_multiplier=multiplier)
if analysis["count"]:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latest", f'{analysis["latest_cps"]:g} CPS')
    m2.metric("Average", f'{analysis["average_cps"]:.2f} CPS')
    m3.metric("Peak", f'{analysis["peak_cps"]:g} CPS')
    m4.metric("Readings", analysis["count"])
    if analysis["anomaly"]: st.warning("Unusual count-rate increase: " + analysis["message"])
    else: st.info(analysis["message"])
    df = pd.DataFrame(st.session_state.radiation_history)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    st.subheader("Count-rate trend")
    st.line_chart(df.set_index("timestamp")["count_rate_cps"], y_label="Counts per second (CPS)")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Export radiation history (CSV)", df.to_csv(index=False).encode("utf-8"), "cosmo_care_radiation_history.csv", "text/csv")
    if st.session_state.radiation_history[-1]["sensor_status"] != "operational": st.error("The latest detector status is not operational. Treat the measurement stream as potentially unreliable.")
else: st.info("No radiation readings yet. Add a detector reading above to begin.")
st.caption("Anomaly detection is a statistical demonstration feature, not a validated exposure or health-risk assessment.")
