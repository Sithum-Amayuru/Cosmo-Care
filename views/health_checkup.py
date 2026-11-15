"""Daily astronaut health checkup workflow for the Cosmo Care demo."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from ui_theme import apply_theme

apply_theme()
st.title("🩺 Daily Astronaut Health Checkup")
st.caption("A guided wellbeing review combining the latest available observations with the astronaut's own report.")
st.info("Prototype demonstration only. This checkup is not a medical diagnosis, medical clearance, or substitute for mission medical procedures.")

st.session_state.setdefault("crew_readings", [])
st.session_state.setdefault("radiation_history", [])
st.session_state.setdefault("cosmo_checkup_records", [])
st.session_state.setdefault("cosmo_checkup_completed_date", None)

today_key = date.today().isoformat()
crew = st.session_state.get("crew_readings", [])
radiation = st.session_state.get("radiation_history", [])
latest = crew[-1] if crew else None
previous = crew[-2] if len(crew) > 1 else None

st.subheader("1. Latest available health and environment data")
if latest:
    st.caption(f"Latest observation: {latest.get('timestamp', 'Timestamp unavailable')} · Astronaut: {latest.get('astronaut_id', 'Not specified')} · Source: {latest.get('source', 'Not specified')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Heart rate", f"{latest['heart_rate_bpm']:.1f} bpm" if latest.get("heart_rate_bpm") is not None else "Not available")
    c2.metric("Sleep", f"{latest['sleep_hours']:.1f} h" if latest.get("sleep_hours") is not None else "Not available")
    c3.metric("Cabin CO₂", f"{latest['co2_ppm']:.0f} ppm" if latest.get("co2_ppm") is not None else "Not available")
    if previous:
        st.caption("A previous crew observation is available for trend comparison.")
    else:
        st.caption("Only one crew observation is available; personal trends cannot yet be compared.")
else:
    st.warning("No crew health observations are available in this session. The checkup can still collect self-reported wellbeing, but measurement-based observations will be marked as unavailable.")

if radiation:
    last_rad = radiation[-1]
    st.caption(f"Radiation detector record available: {last_rad.get('count_rate_cps', 'Unknown')} CPS ({last_rad.get('timestamp', 'timestamp unavailable')}). CPS is a detector count rate, not a dose measurement.")
else:
    st.caption("No radiation detector record is available in this session.")

st.divider()
st.subheader("2. Wellbeing interview")
st.write("Please answer based on how you feel right now. You can skip any question.")

with st.form("cosmo_daily_health_checkup_form"):
    feeling = st.select_slider("How are you feeling today?", options=["Very unwell", "Unwell", "Okay", "Good", "Very good"], value="Okay")
    energy = st.select_slider("How would you describe your energy level?", options=["Very low", "Low", "Moderate", "High", "Very high"], value="Moderate")
    symptoms = st.multiselect("Have you experienced any of these today?", ["Headache", "Dizziness", "Nausea", "Unusual fatigue", "Shortness of breath", "Pain or discomfort", "Difficulty concentrating", "Sleep disturbance"])
    symptom_details = st.text_area("Would you like to add details? (optional)", placeholder="When did it start? Has it changed? You can leave this blank.")
    submitted = st.form_submit_button("Complete health checkup", type="primary")

if submitted:
    record = {
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "checkup_date": today_key,
        "astronaut_id": (latest or {}).get("astronaut_id", "AST-001"),
        "feeling": feeling,
        "energy": energy,
        "symptoms": symptoms,
        "symptom_details": symptom_details.strip(),
        "latest_crew_observation": dict(latest) if latest else None,
        "latest_radiation_observation": dict(radiation[-1]) if radiation else None,
    }
    st.session_state.cosmo_checkup_records.append(record)
    st.session_state.cosmo_checkup_completed_date = today_key
    st.session_state.cosmo_latest_checkup_report = record
    st.rerun()

report = st.session_state.get("cosmo_latest_checkup_report")
if report:
    st.divider()
    st.subheader("3. Checkup summary")
    st.caption(f"Completed: {report.get('completed_at', 'Time unavailable')}")
    a, b = st.columns(2)
    a.metric("Self-reported wellbeing", report["feeling"])
    b.metric("Self-reported energy", report["energy"])

    if report["symptoms"]:
        st.warning("Symptoms reported: " + ", ".join(report["symptoms"]))
        st.write("These are self-reported symptoms, not a diagnosis. Follow the mission's approved medical reporting process, especially for severe, new, or worsening symptoms.")
    else:
        st.info("No symptoms were selected in this checkup. This does not prove that no health issue is present.")

    observed = report.get("latest_crew_observation")
    if observed:
        st.markdown("**Measurement evidence included**")
        fields = {
            "Heart rate": ("heart_rate_bpm", "bpm"),
            "Sleep": ("sleep_hours", "hours"),
            "Oxygen": ("oxygen_percent", "%"),
            "CO₂": ("co2_ppm", "ppm"),
            "Temperature": ("temperature_c", "°C"),
        }
        rows = []
        for label, (key, unit) in fields.items():
            value = observed.get(key)
            rows.append({"Measurement": label, "Latest value": f"{value} {unit}" if value is not None else "Not available"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning("No physiological/environmental measurement was available for this report.")

    if report.get("latest_radiation_observation"):
        st.caption("A radiation detector count-rate record was present. It is listed as instrument context only and is not interpreted as a personal dose.")

    st.caption("This is a structured demonstration summary. It does not classify the astronaut as medically fit or unfit, and it does not replace clinical review.")

if st.session_state.cosmo_checkup_records:
    with st.expander("Checkup history (this session)"):
        history = [
            {
                "Completed": r.get("completed_at"),
                "Astronaut": r.get("astronaut_id"),
                "Wellbeing": r.get("feeling"),
                "Energy": r.get("energy"),
                "Symptoms": ", ".join(r.get("symptoms", [])) or "None selected",
            }
            for r in reversed(st.session_state.cosmo_checkup_records)
        ]
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)

st.caption("Data availability note: current observations and checkup history are held in Streamlit session state for this prototype and may disappear when the session resets.")
