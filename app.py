import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modules.radiation_monitor import make_reading, analyze_readings
from modules.astronaut_health import render_astronaut_health
from ui_theme import apply_theme, render_hero, render_navigation

st.set_page_config(page_title="COSMO CARE | Mission Control", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")
apply_theme()

render_hero()
render_navigation()
st.markdown("## Mission overview")
st.caption("Unified astronaut health and mission-environment monitoring console")

st.warning(
    "Prototype only. This app uses manually entered / illustrative demo readings. "
    "It is not a certified spacecraft monitoring system or medical device. "
    "Configure alert limits from approved mission procedures before operational use."
)

with st.sidebar:
    st.header("Demo controls")
    astronaut_id = st.text_input("Astronaut ID", "AST-001")
    source_type = st.selectbox(
        "Reading source",
        ["Simulated demonstration data", "Manually entered readings"]
    )
    st.caption("No real NASA astronaut dataset is included.")

    st.divider()
    st.subheader("Health baseline")
    baseline_hr = st.number_input("Baseline heart rate (bpm)", min_value=1.0, value=70.0)
    baseline_sleep = st.number_input("Typical sleep (hours)", min_value=0.0, max_value=24.0, value=8.0)
    hr_deviation = st.slider(
        "Demo heart-rate deviation alert (%)",
        min_value=5, max_value=60, value=20,
        help="Illustrative prototype setting, not a clinical threshold."
    )
    sleep_min = st.number_input(
        "Demo minimum sleep alert (hours)",
        min_value=0.0, max_value=24.0, value=6.0,
        help="Illustrative prototype setting, not a medical recommendation."
    )

    st.divider()
    st.subheader("Mission-defined environmental limits")
    st.caption("Enter limits supplied by an approved mission procedure. No limits are pre-filled.")
    use_co2 = st.checkbox("Enable CO₂ upper limit")
    co2_limit = st.number_input("CO₂ upper limit (ppm)", min_value=0.0, value=0.0, disabled=not use_co2)
    use_o2 = st.checkbox("Enable O₂ lower limit")
    o2_limit = st.number_input("O₂ lower limit (%)", min_value=0.0, max_value=100.0, value=0.0, disabled=not use_o2)
    use_temp = st.checkbox("Enable temperature range")
    temp_min = st.number_input("Minimum temperature (°C)", value=18.0, disabled=not use_temp)
    temp_max = st.number_input("Maximum temperature (°C)", value=27.0, disabled=not use_temp)
    use_humidity = st.checkbox("Enable humidity range")
    humidity_min = st.number_input("Minimum humidity (%)", min_value=0.0, max_value=100.0, value=30.0, disabled=not use_humidity)
    humidity_max = st.number_input("Maximum humidity (%)", min_value=0.0, max_value=100.0, value=60.0, disabled=not use_humidity)


st.header("◎  Radiation monitoring")
st.caption("Generic detector interface: enter the event count rate reported by the detector. CPS is not a dose measurement.")
if "radiation_history" not in st.session_state:
    st.session_state.radiation_history = []

rad_col1, rad_col2, rad_col3 = st.columns(3)
with rad_col1:
    detector_id = st.text_input("Detector ID", "RAD-01")
    radiation_type = st.selectbox("Radiation type reported by detector", ["Unclassified", "Neutron", "Gamma", "Proton", "Other"])
with rad_col2:
    count_rate_cps = st.number_input("Count rate (counts/second)", min_value=0.0, value=10.0, step=1.0)
    sensor_status = st.selectbox("Detector status", ["operational", "warning", "fault"])
with rad_col3:
    anomaly_multiplier = st.number_input("Anomaly multiplier", min_value=1.1, max_value=10.0, value=2.0, step=0.1,
        help="Flags a latest count rate at least this multiple of the prior-history median. Statistical demo setting, not a safety limit.")
    st.write("")
    if st.button("Record detector reading", type="primary", use_container_width=True):
        try:
            new_reading = make_reading(
                detector_id=detector_id,
                count_rate_cps=count_rate_cps,
                radiation_type=radiation_type,
                sensor_status=sensor_status,
                source=source_type,
            )
            st.session_state.radiation_history.append(new_reading)
            st.success("Radiation reading recorded.")
        except ValueError as exc:
            st.error(str(exc))

radiation_analysis = analyze_readings(
    st.session_state.radiation_history,
    anomaly_multiplier=anomaly_multiplier,
)
radiation_latest = radiation_analysis["latest_cps"] if radiation_analysis["latest_cps"] is not None else 0.0

st.subheader("Radiation count-rate history")
if st.session_state.radiation_history:
    radiation_df = pd.DataFrame(st.session_state.radiation_history)
    radiation_df["timestamp"] = pd.to_datetime(radiation_df["timestamp"], utc=True)
    st.line_chart(radiation_df.set_index("timestamp")["count_rate_cps"], y_label="Counts per second (CPS)")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Latest", f"{radiation_analysis['latest_cps']:g} CPS")
    r2.metric("Average", f"{radiation_analysis['average_cps']:.2f} CPS")
    r3.metric("Peak", f"{radiation_analysis['peak_cps']:g} CPS")
    r4.metric("Recorded readings", radiation_analysis["count"])
    if radiation_analysis["anomaly"]:
        st.warning("Unusual count-rate increase detected. " + radiation_analysis["message"])
    else:
        st.info(radiation_analysis["message"])
    if radiation_df["sensor_status"].iloc[-1] != "operational":
        st.error("Latest detector status is not operational. Treat the measurement stream as potentially unreliable.")
    st.download_button(
        "Download radiation history as CSV",
        data=radiation_df.to_csv(index=False).encode("utf-8"),
        file_name="cosmo_care_radiation_history.csv",
        mime="text/csv",
    )
else:
    st.info("No detector readings recorded yet. Enter a reading above and select Record detector reading.")

st.warning("CPS is an instrument count rate, not dose rate or absorbed dose. Do not convert CPS to µSv/h without detector-specific calibration.")

st.header("♡  Crew & environment readings")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Astronaut health")
    heart_rate = st.number_input("Heart rate (bpm)", min_value=0.0, value=88.0)
    sleep_hours = st.number_input("Sleep in last 24 hours (hours)", min_value=0.0, max_value=24.0, value=5.5)
    activity = st.slider("Activity level (demo index)", 0, 100, 55)
with col2:
    st.subheader("Spacecraft environment")
    oxygen = st.number_input("Oxygen (%)", min_value=0.0, max_value=100.0, value=20.9)
    co2 = st.number_input("Carbon dioxide (ppm)", min_value=0.0, value=1000.0)
    temperature = st.number_input("Temperature (°C)", value=22.0)
    humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=45.0)
    pressure = st.number_input("Pressure (kPa)", min_value=0.0, value=101.0)
st.divider()
st.header("◈  Live monitoring overview")

m1, m2, m3 = st.columns(3)
m1.metric("Heart rate", f"{heart_rate:.1f} bpm", f"{heart_rate - baseline_hr:+.1f} vs baseline")
m2.metric("Sleep", f"{sleep_hours:.1f} h", f"{sleep_hours - baseline_sleep:+.1f} vs typical")
m3.metric("CO₂", f"{co2:.0f} ppm")

alerts = []
observations = []

# Health: personalized comparison; this is a configurable demo heuristic, not diagnosis.
if baseline_hr > 0:
    hr_change_pct = abs(heart_rate - baseline_hr) / baseline_hr * 100
    if hr_change_pct >= hr_deviation:
        alerts.append(("Health", "Review heart-rate deviation", f"Current heart rate differs from the entered personal baseline by {hr_change_pct:.1f}%."))
    else:
        observations.append("Heart rate is within the configured demo deviation from the entered baseline.")

if sleep_hours < sleep_min:
    alerts.append(("Health", "Review sleep duration", f"Sleep is below the configured demo alert setting of {sleep_min:.1f} hours."))

# Environmental checks are inactive until mission-approved limits are entered.
if use_co2 and co2 > co2_limit:
    alerts.append(("Environment", "CO₂ above configured limit", f"CO₂ reading ({co2:.0f} ppm) exceeds the entered mission limit ({co2_limit:.0f} ppm). Follow approved environmental procedures."))
if use_o2 and oxygen < o2_limit:
    alerts.append(("Environment", "O₂ below configured limit", f"O₂ reading ({oxygen:.2f}%) is below the entered mission limit ({o2_limit:.2f}%). Follow approved environmental procedures."))
if use_temp and not (temp_min <= temperature <= temp_max):
    alerts.append(("Environment", "Temperature outside configured range", f"Temperature ({temperature:.1f} °C) is outside the entered range ({temp_min:.1f}–{temp_max:.1f} °C)."))
if use_humidity and not (humidity_min <= humidity <= humidity_max):
    alerts.append(("Environment", "Humidity outside configured range", f"Humidity ({humidity:.1f}%) is outside the entered range ({humidity_min:.1f}–{humidity_max:.1f}%)."))
if radiation_analysis["anomaly"]:
    alerts.append(("Radiation", "Unusual count-rate increase", radiation_analysis["message"]))
if st.session_state.radiation_history and st.session_state.radiation_history[-1]["sensor_status"] != "operational":
    alerts.append(("Radiation", "Detector status requires attention", "The latest detector status is not operational. Verify the instrument and do not assume the reading stream is complete or reliable."))

if not any([use_co2, use_o2, use_temp, use_humidity]):
    observations.append("Environmental thresholds are not configured. Readings are displayed but not classified as safe or unsafe.")
if not st.session_state.radiation_history:
    observations.append("No radiation detector readings have been recorded yet.")

st.subheader("⚑  Alerts and explanations")
if alerts:
    for category, title, explanation in alerts:
        st.error(f"**{category}: {title}**\n\n{explanation}")
else:
    st.success("No configured alert rules were triggered by the current inputs.")
for item in observations:
    st.info(item)

st.caption("Alerts are rule-triggered observations, not diagnoses or autonomous instructions. The system does not infer causation between simultaneous readings.")

st.divider()
st.header("▤  Current measurement record")
record = {
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "astronaut_id": astronaut_id,
    "source": source_type,
    "heart_rate_bpm": heart_rate,
    "sleep_hours": sleep_hours,
    "activity_demo_index": activity,
    "oxygen_percent": oxygen,
    "co2_ppm": co2,
    "temperature_c": temperature,
    "humidity_percent": humidity,
    "pressure_kpa": pressure,
    "radiation_latest_count_rate_cps": radiation_latest if radiation_analysis["count"] else None,
    "radiation_recorded_readings": radiation_analysis["count"],
    "alert_count": len(alerts),
}
st.dataframe(pd.DataFrame([record]), use_container_width=True)

st.download_button(
    "Download current readings as CSV",
    data=pd.DataFrame([record]).to_csv(index=False).encode("utf-8"),
    file_name=f"{astronaut_id}_cosmo_care_reading.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Reference basis")
st.markdown(
    "- NASA HRP Hazards: space radiation, isolation/confinement, gravity fields and hostile/closed environments.\n"
    "- NASA HRP Risks: health consequences that motivate monitoring.\n"
    "- NASA HRP Ongoing Research: examples of ongoing human-spaceflight research and monitoring approaches.\n"
    "- Canadian Space Agency CANS article: specialized autonomous neutron-radiation measurement.\n"
    "- Canadian Space Agency space-science article: long-duration mission risks and the value of onboard capability when communication with Earth is delayed."
)
st.caption("The five references provide rationale and context; they do not supply this prototype with live astronaut measurements or operational alarm thresholds.")


st.divider()
st.header("✚  Astronaut health & personalisation")
render_astronaut_health()
