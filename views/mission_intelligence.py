"""Astronaut Health Intelligence — integrated mission prototype workspace."""
from datetime import datetime, timezone
from statistics import median
import random

import pandas as pd
import streamlit as st

from ui_theme import apply_theme
from modules.mission_backend import (
    AstronautVitals,
    BioAstronauticsLogic,
)

apply_theme()
st.title("🛰️ Astronaut Health Intelligence")
st.caption(
    "An integrated mission-console demonstration combining crew physiology, "
    "biosignal visualisation, cabin conditions, radiation trends and mission logistics."
)
st.warning(
    "RESEARCH SIMULATION ONLY — every generated measurement is synthetic. "
    "The teammate's algorithms and thresholds are unvalidated. Outputs are not diagnoses, "
    "medical clearance, treatment instructions, real radiation dose assessments or spacecraft alerts."
)

# All demo data stays in this Streamlit session. No API/LLM calls are made here.
CREW = {"Astronaut 1": "AST-001", "Astronaut 2": "AST-002"}
st.session_state.setdefault("mission_intel_history", [])
st.session_state.setdefault("mission_intel_radiation", [])
st.session_state.setdefault("mission_intel_environment", [])
st.session_state.setdefault("mission_intel_last_result", None)

left, right = st.columns([1, 1])
with left:
    astronaut_name = st.selectbox("Crew member", list(CREW), key="intel_astronaut")
    astronaut_id = CREW[astronaut_name]
with right:
    flight_day = st.number_input("Mission day", min_value=1, max_value=2000, value=24, step=1)

st.divider()
st.subheader("1 · Crew health check")
st.caption("Choose a sample situation to see how the monitoring system explains crew readings.")
scenario = st.selectbox(
    "Simulation scenario",
    [
        "Nominal baseline",
        "Higher heart rate and lower heart-rate variability",
        "Possible low blood-volume pattern",
        "Higher cabin CO2 and headache pattern",
        "Muscle discomfort",
        "Custom readings",
    ],
    key="intel_health_scenario",
)

defaults = {
    "Nominal baseline": (68.0, 118.0, 76.0, 44.0, 2.6, 0, False, False, "None", "None", 0),
    "Elevated heart rate / low HRV": (106.0, 118.0, 88.0, 20.0, 2.6, 4, False, False, "Calves/Hamstrings", "Acute Cramp/Spasm", 7),
    "Possible low-volume pattern": (101.0, 108.0, 82.0, 34.0, 2.6, 0, True, False, "None", "None", 0),
    "Elevated CO₂ + headache pattern": (78.0, 142.0, 86.0, 42.0, 4.3, 0, False, True, "None", "None", 0),
    "Muscle cramp / discomfort": (72.0, 118.0, 76.0, 42.0, 2.6, 0, False, False, "Left Leg", "Acute Cramp/Spasm", 5),
}
base = defaults.get(scenario, defaults["Nominal baseline"])
if scenario == "Custom readings":
    a, b, c = st.columns(3)
    with a:
        hr = st.number_input("Heart rate (bpm)", 20.0, 250.0, 68.0, key="intel_hr")
        sbp = st.number_input("Systolic BP (mmHg)", 50.0, 300.0, 118.0, key="intel_sbp")
        dbp = st.number_input("Diastolic BP (mmHg)", 30.0, 200.0, 76.0, key="intel_dbp")
    with b:
        hrv = st.number_input("HRV RMSSD (ms)", 0.0, 300.0, 44.0, key="intel_hrv")
        co2 = st.number_input("CO₂ partial pressure (mmHg)", 0.0, 30.0, 2.6, key="intel_co2")
        ectopic = st.number_input("Ectopic beats/min (demo)", 0, 100, 0, key="intel_ectopic")
    with c:
        dizzy = st.checkbox("Dizziness reported", key="intel_dizzy")
        headache = st.checkbox("Headache reported", key="intel_headache")
        region = st.selectbox("Body region", ["None", "Neck/Trapezius", "Lumbar Spine", "Left Leg", "Right Leg", "Other"], key="intel_region")
        symptom = st.selectbox("Symptom category", ["None", "Acute Cramp/Spasm", "Generalized Weakness", "Deep Dull Ache", "Post-ARED DOMS"], key="intel_symptom")
        pain = st.slider("Pain score (0–10)", 0, 10, 0, key="intel_pain")
else:
    hr, sbp, dbp, hrv, co2, ectopic, dizzy, headache, region, symptom, pain = base
    st.info(f"Scenario preset: HR {hr:g} bpm · BP {sbp:g}/{dbp:g} mmHg · HRV {hrv:g} ms")

if st.button("Analyse crew snapshot", type="primary", key="intel_analyse"):
    if dbp >= sbp:
        st.error("Check blood pressure: systolic should be greater than diastolic.")
    else:
        vitals = AstronautVitals(
            astronaut_id=astronaut_id, flight_day=int(flight_day), hr=float(hr),
            sbp=float(sbp), dbp=float(dbp), hrv=float(hrv), co2=float(co2),
            ectopic=int(ectopic), dizzy=bool(dizzy), headache=bool(headache),
            region=region, symptom=symptom, pain=int(pain),
        )
        result = BioAstronauticsLogic.evaluate_triage(vitals)
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "astronaut": astronaut_name, "astronaut_id": astronaut_id,
            "scenario": scenario, "heart_rate_bpm": hr, "systolic_mmhg": sbp,
            "diastolic_mmhg": dbp, "hrv_rmssd": hrv, "co2_mmhg": co2,
            "ectopic_beats_min": ectopic, "prototype_label": result["status_level"],
        }
        st.session_state.mission_intel_history.append(snapshot)
        st.session_state.mission_intel_history = st.session_state.mission_intel_history[-100:]
        st.session_state.mission_intel_last_result = {
            "snapshot": snapshot, "result": result,
            "vitals": vitals,
        }

last = st.session_state.mission_intel_last_result
if last and last["snapshot"]["astronaut_id"] == astronaut_id:
    result = last["result"]
    vitals = last["vitals"]

    # Translate research-engine terminology into plain language for the default view.
    diagnosis = str(result.get("diagnosis", ""))
    friendly_titles = {
        "Microgravity Hypovolemia & Reduced Stroke Volume": "Possible low blood-volume pattern",
        "Systemic Electrolyte Depletion & Myocardial Irritability": "Possible electrolyte-related heart rhythm concern",
        "Cephalad Venous Congestion & Hypercapnic Vasodilation": "Possible CO2-related circulation concern",
        "Localized Neuromuscular Hyper-Excitability": "Possible muscle or nerve irritation pattern",
        "Autonomic Overdrive": "Possible stress-response pattern",
        "Mechanical Overload": "Possible muscle overexertion pattern",
    }
    friendly_title = next(
        (title for technical, title in friendly_titles.items() if technical.lower() in diagnosis.lower()),
        "A pattern needs review" if result.get("status_level") != "NOMINAL" else "No unusual pattern detected",
    )
    status = str(result.get("status_level", "UNKNOWN")).upper()
    if status == "NOMINAL":
        status_label, status_icon = "Normal", "🟢"
        status_message = "The simulated readings did not trigger this prototype's warning rules."
        status_kind = "success"
    elif status == "MEDICAL HOLD":
        status_label, status_icon = "High priority", "🔴"
        status_message = "The prototype detected a pattern that requires prompt review by qualified mission medical personnel."
        status_kind = "error"
    elif status == "ADVISORY":
        status_label, status_icon = "Needs attention", "🟠"
        status_message = "Some simulated readings differ from the prototype's expected pattern. Review the measurements and verification steps."
        status_kind = "warning"
    else:
        status_label, status_icon = "Unable to assess", "⚪"
        status_message = "The engine returned an unrecognised status. Review the technical output."
        status_kind = "info"

    st.markdown("#### Crew health result")
    with st.container(border=True):
        st.markdown(f"### {status_icon} {status_label}")
        st.markdown(f"## {friendly_title}")
        st.write(status_message)
        if status_kind == "success":
            st.success("No prototype warning was triggered.")
        elif status_kind == "error":
            st.error("Priority review suggested by the experimental algorithm.")
        elif status_kind == "warning":
            st.warning("Review the readings; this is not a confirmed medical condition.")
        else:
            st.info("The result needs technical review.")
        st.markdown("**What the system noticed**")
        st.write(result.get("explanation", "No explanation was returned."))
        st.markdown("**Suggested next step**")
        st.write(result.get("verification", "Review the measurements with the qualified mission team."))
        st.caption("Research simulation only. This status is not a diagnosis, medical clearance or emergency instruction.")

    st.markdown("#### Key measurements")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Heart rate", f"{vitals.hr:g} bpm", help="Number of heartbeats per minute.")
    m2.metric("Blood pressure", f"{vitals.sbp:g}/{vitals.dbp:g} mmHg", help="Systolic / diastolic blood pressure.")
    m3.metric("Heart rate variability", f"{vitals.hrv:g} ms", help="A measure of variation in time between heartbeats.")
    m4.metric("Pulse pressure", f"{result['hemodynamics']['pulse_pressure']:g} mmHg", help="Difference between systolic and diastolic pressure.")
    st.caption(f"Mission phase used by the research model: {result['phase_name']}")

    show_engineering = st.toggle("Show engineering details", value=False, key="intel_show_engineering")
    if show_engineering:
        st.markdown("**Original engine output**")
        st.write(result["status_level"] + " · " + result["diagnosis"])
        st.write("Standardised deviations (Z-scores)")
        st.json(result["z_scores"])
        st.write("Derived hemodynamic calculations")
        st.json(result["hemodynamics"])
        st.caption("The teammate engine's medication, treatment and exercise recommendations are not presented as advice. Any real concern requires independent assessment by qualified medical personnel.")

    # Illustrative waveform generated from teammate's mathematical waveform model.
    wave_rows = []
    for i in range(240):
        t = i * 0.05
        wave = BioAstronauticsLogic.sample_bio_waveforms(t, vitals)
        wave_rows.append({"time_s": t, "ECG-like signal (mV)": wave["ecg_mv"], "PPG-like signal (a.u.)": wave["ppg_amp"]})
    wave_df = pd.DataFrame(wave_rows).set_index("time_s")
    st.markdown("#### Synthetic biosignal visualisation")
    st.line_chart(wave_df[["ECG-like signal (mV)"]], height=190)
    st.line_chart(wave_df[["PPG-like signal (a.u.)"]], height=190)
    st.caption("Mathematical demonstration waveforms only — not captured ECG/PPG and not suitable for diagnosis.")

crew_history = [
    r for r in st.session_state.mission_intel_history
    if r["astronaut_id"] == astronaut_id
]
if crew_history:
    st.markdown("#### Recent crew trend")
    trend = pd.DataFrame(crew_history).set_index("timestamp")
    st.line_chart(trend[["heart_rate_bpm", "hrv_rmssd"]], height=220)
    st.dataframe(pd.DataFrame(crew_history).tail(10), use_container_width=True, hide_index=True)

st.divider()
st.subheader("2 · Spacecraft cabin conditions")
st.caption("These readings describe the shared cabin environment, not an individual astronaut.")
env_scenario = st.selectbox(
    "Cabin scenario",
    ["Nominal cabin", "Elevated CO₂", "Low oxygen", "Temperature excursion"],
    key="intel_env_scenario",
)
if st.button("Generate cabin reading", key="intel_generate_env"):
    env = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "oxygen_percent": round(random.uniform(20.6, 21.2), 2),
        "co2_ppm": round(random.uniform(900, 1500), 0),
        "temperature_c": round(random.uniform(21.2, 23.0), 1),
        "humidity_percent": round(random.uniform(42, 48), 1),
        "pressure_kpa": round(random.uniform(100.8, 101.5), 2),
        "scenario": env_scenario,
    }
    if env_scenario == "Elevated CO₂":
        env["co2_ppm"] = round(random.uniform(4000, 6500), 0)
    elif env_scenario == "Low oxygen":
        env["oxygen_percent"] = round(random.uniform(18.1, 19.2), 2)
    elif env_scenario == "Temperature excursion":
        env["temperature_c"] = round(random.choice([random.uniform(15, 17), random.uniform(29, 32)]), 1)
    st.session_state.mission_intel_environment.append(env)
    st.session_state.mission_intel_environment = st.session_state.mission_intel_environment[-100:]

if st.session_state.mission_intel_environment:
    env = st.session_state.mission_intel_environment[-1]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Oxygen", f"{env['oxygen_percent']:.2f}%")
    c2.metric("Cabin CO₂", f"{env['co2_ppm']:.0f} ppm")
    c3.metric("Temperature", f"{env['temperature_c']:.1f} °C")
    c4.metric("Humidity", f"{env['humidity_percent']:.1f}%")
    c5.metric("Pressure", f"{env['pressure_kpa']:.2f} kPa")
    if env["oxygen_percent"] < 19.5 or env["co2_ppm"] >= 3800:
        st.warning("Prototype cabin-condition flag: verify this synthetic reading and consult approved mission procedures.")
    elif env["temperature_c"] < 18 or env["temperature_c"] > 28:
        st.warning("Prototype temperature excursion flag: verify the synthetic reading.")
    else:
        st.success("No prototype cabin-condition flag for this generated sample.")
    st.caption("These demonstration triggers are not validated spacecraft environmental limits.")

st.divider()
st.subheader("3 · Radiation monitoring")
st.caption("The detector counts events each second. This count rate is not the same as a radiation dose.")
rad_scenario = st.selectbox(
    "Detector scenario", ["Routine background", "Count-rate spike", "Detector fault"],
    key="intel_rad_scenario",
)
if st.button("Generate radiation reading", key="intel_generate_rad"):
    if rad_scenario == "Routine background":
        cps, status = round(random.uniform(8, 14), 2), "operational"
    elif rad_scenario == "Count-rate spike":
        cps, status = round(random.uniform(48, 85), 2), "warning"
    else:
        cps, status = round(random.uniform(0, 2), 2), "fault"
    st.session_state.mission_intel_radiation.append({
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "detector_id": "RAD-01", "count_rate_cps": cps,
        "sensor_status": status, "scenario": rad_scenario,
    })
    st.session_state.mission_intel_radiation = st.session_state.mission_intel_radiation[-100:]

rad_history = st.session_state.mission_intel_radiation
if rad_history:
    values = [float(r["count_rate_cps"]) for r in rad_history]
    baseline = median(values[:-1]) if len(values) >= 4 else None
    latest_rad = rad_history[-1]
    factor = values[-1] / baseline if baseline and baseline > 0 else None
    anomaly = (factor is not None and factor >= 2.0) or values[-1] >= 40
    r1, r2, r3 = st.columns(3)
    r1.metric("Latest count rate", f"{values[-1]:.2f} CPS")
    r2.metric("Session peak", f"{max(values):.2f} CPS")
    r3.metric("Compared with prior median", f"{factor:.2f}×" if factor else "Building baseline")
    if latest_rad["sensor_status"] != "operational":
        st.error("Detector status flag: latest sensor is not marked operational.")
    elif anomaly:
        st.warning("Prototype count-rate anomaly flag. Verify detector, shielding and mission-control data.")
    else:
        st.info("No count-rate anomaly flag in this synthetic sample.")
    rdf = pd.DataFrame(rad_history).set_index("timestamp")
    st.line_chart(rdf[["count_rate_cps"]], height=180)
    st.caption("The teammate's anomaly multiplier is a demonstration heuristic, not a radiation safety threshold. No dose is inferred from CPS.")

st.divider()
st.subheader("4 · Supply delivery planning")
st.caption("Estimate how long a supply shipment and its communication would take. This is a planning simulation, not a real transmission.")
distance_km = st.number_input(
    "Spacecraft distance from Earth (km)",
    min_value=0.0, max_value=1_000_000_000.0, value=384400.0,
    step=10000.0, format="%.1f", key="intel_distance",
)
# Calculate using the teammate engine's documented constants/formula.
light_hours = distance_km / 299792.458 / 3600.0
cargo_days = distance_km / 20.0 / 86400.0
buffer_days = cargo_days * 0.25
prep_days = 14.0
total_days = (2 * light_hours / 24.0) + prep_days + cargo_days + buffer_days
s1, s2, s3 = st.columns(3)
s1.metric("One-way signal delay", f"{light_hours:.2f} hours")
s2.metric("Cargo transit estimate", f"{cargo_days:.2f} days")
s3.metric("Total planning lead time", f"{total_days:.2f} days")
st.caption("Assumptions: cargo speed 20 km/s, Earth preparation 14 days, 25% transit buffer. Actual missions require mission-specific logistics models.")

st.divider()
st.subheader("5 · Session data export")
all_health = st.session_state.mission_intel_history
if all_health:
    hdf = pd.DataFrame(all_health)
    st.download_button("Export crew intelligence history (CSV)", hdf.to_csv(index=False).encode("utf-8"), "cosmo_care_health_intelligence.csv", "text/csv")
if st.session_state.mission_intel_environment:
    edf = pd.DataFrame(st.session_state.mission_intel_environment)
    st.download_button("Export cabin history (CSV)", edf.to_csv(index=False).encode("utf-8"), "cosmo_care_cabin_history.csv", "text/csv")
if rad_history:
    rpdf = pd.DataFrame(rad_history)
    st.download_button("Export radiation history (CSV)", rpdf.to_csv(index=False).encode("utf-8"), "cosmo_care_radiation_history.csv", "text/csv")

if st.button("Clear this intelligence session", key="intel_clear"):
    for key in ("mission_intel_history", "mission_intel_radiation", "mission_intel_environment"):
        st.session_state[key] = []
    st.session_state.mission_intel_last_result = None
    st.rerun()

st.caption(
    "All data on this page is synthetic and stored only in the current Streamlit session. "
    "The interface makes no real sensor connection, no actual emergency transmission, and no clinical decision."
)
