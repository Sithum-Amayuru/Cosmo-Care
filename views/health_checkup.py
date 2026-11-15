"""Daily astronaut health checkup with voice and manual interview modes."""
from __future__ import annotations

from datetime import date, datetime
import uuid

import pandas as pd
import streamlit as st

from ui_theme import apply_theme
from cosmo_checkup_voice import cosmo_checkup_voice

apply_theme()
st.title("🩺 Daily Astronaut Health Checkup")
st.caption("A short daily wellbeing interview with voice and fill-in options.")
st.info(
    "Prototype demonstration only. This checkup records self-reported information "
    "and available observations. It is not a medical diagnosis or medical clearance."
)

st.session_state.setdefault("crew_readings", [])
st.session_state.setdefault("radiation_history", [])
st.session_state.setdefault("cosmo_checkup_records", [])
st.session_state.setdefault("cosmo_checkup_completed_date", None)
st.session_state.setdefault("cosmo_checkup_voice_run_id", str(uuid.uuid4()))

today_key = date.today().isoformat()
crew = st.session_state.get("crew_readings", [])
radiation = st.session_state.get("radiation_history", [])
latest = crew[-1] if crew else None
previous = crew[-2] if len(crew) > 1 else None

st.subheader("1. Latest available health and environment data")
if latest:
    st.caption(
        f"Latest observation: {latest.get('timestamp', 'Timestamp unavailable')} · "
        f"Astronaut: {latest.get('astronaut_id', 'Not specified')} · "
        f"Source: {latest.get('source', 'Not specified')}"
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Heart rate", f"{latest['heart_rate_bpm']:.1f} bpm" if latest.get("heart_rate_bpm") is not None else "Not available")
    c2.metric("Sleep", f"{latest['sleep_hours']:.1f} h" if latest.get("sleep_hours") is not None else "Not available")
    c3.metric("Cabin CO₂", f"{latest['co2_ppm']:.0f} ppm" if latest.get("co2_ppm") is not None else "Not available")
    st.caption(
        "A previous crew observation is available for trend comparison."
        if previous else
        "Only one crew observation is available; personal trends cannot yet be compared."
    )
else:
    st.warning("No crew health observations are available in this session. You can still complete the self-reported checkup.")

if radiation:
    last_rad = radiation[-1]
    st.caption(
        f"Radiation detector record available: {last_rad.get('count_rate_cps', 'Unknown')} CPS "
        f"({last_rad.get('timestamp', 'timestamp unavailable')}). "
        "CPS is a detector count rate, not a dose measurement."
    )
else:
    st.caption("No radiation detector record is available in this session.")

voice_questions = [
    "How are you feeling overall today? Please describe it in a few words.",
    "How is your energy level today? Do you feel energetic, normal, or unusually tired?",
    "How did you sleep during your last sleep period? You can mention the number of hours and sleep quality.",
    "Have you experienced any symptoms today, such as headache, dizziness, nausea, unusual fatigue, or sleep disturbance? Please describe them, or say none.",
    "Are you experiencing any pain or physical discomfort? If yes, where is it and how severe is it from zero to ten?",
    "Are you experiencing any new or severe symptoms such as chest pain, difficulty breathing, or fainting? Please say yes, no, or not sure.",
    "How would you describe your stress level or mood today?",
    "Is there anything else about your health or wellbeing that you would like the mission medical team to know?",
]

st.divider()
st.subheader("2. Complete your daily checkup")
mode = st.radio(
    "Choose your preferred method",
    ["Voice-guided checkup", "Fill in the questions"],
    horizontal=True,
    label_visibility="collapsed",
)

if mode == "Voice-guided checkup":
    st.write(
        "Press **Start checkup** in the voice panel. Cosmo Care will read each question "
        "aloud and listen for your answer. You can repeat or skip a question."
    )
    voice_result = cosmo_checkup_voice(
        questions=voice_questions,
        run_id=st.session_state.cosmo_checkup_voice_run_id,
        key="cosmo_daily_checkup_voice",
    )
    if (
        isinstance(voice_result, dict)
        and voice_result.get("type") == "voice_checkup_complete"
        and voice_result.get("runId") == st.session_state.cosmo_checkup_voice_run_id
        and voice_result.get("completed")
        and st.session_state.get("cosmo_saved_voice_run_id") != voice_result.get("runId")
    ):
        record = {
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "checkup_date": today_key,
            "astronaut_id": (latest or {}).get("astronaut_id", "AST-001"),
            "method": "Voice-guided",
            "answers": voice_result.get("answers", []),
            "latest_crew_observation": dict(latest) if latest else None,
            "latest_radiation_observation": dict(radiation[-1]) if radiation else None,
        }
        st.session_state.cosmo_checkup_records.append(record)
        st.session_state.cosmo_checkup_completed_date = today_key
        st.session_state.cosmo_latest_checkup_report = record
        st.session_state.cosmo_saved_voice_run_id = voice_result.get("runId")
        st.success("Voice checkup saved to your report.")
        st.rerun()
else:
    with st.form("cosmo_daily_health_checkup_form"):
        st.markdown("**1. How are you feeling overall today?**")
        feeling = st.select_slider(
            "Overall wellbeing",
            options=["Very unwell", "Unwell", "Okay", "Good", "Very good"],
            value="Okay",
        )
        st.markdown("**2. How is your energy level today?**")
        energy = st.select_slider(
            "Energy level",
            options=["Very low", "Low", "Moderate", "High", "Very high"],
            value="Moderate",
        )
        st.markdown("**3. How did you sleep during your last sleep period?**")
        sleep_quality = st.selectbox(
            "Sleep quality",
            ["Very poor", "Poor", "Fair", "Good", "Very good"],
            index=2,
        )
        sleep_hours = st.number_input(
            "Approximate hours slept (optional)",
            min_value=0.0, max_value=24.0, value=8.0, step=0.5,
        )
        st.markdown("**4. Have you experienced any symptoms today?**")
        symptoms = st.multiselect(
            "Select all that apply",
            [
                "Headache", "Dizziness", "Nausea", "Unusual fatigue",
                "Shortness of breath", "Pain or discomfort",
                "Difficulty concentrating", "Sleep disturbance", "Other",
            ],
        )
        st.markdown("**5. Are you experiencing pain or physical discomfort?**")
        pain_level = st.slider("Pain level (0 = none, 10 = worst)", 0, 10, 0)
        pain_location = st.text_input("Where is the pain? (optional)")
        st.markdown("**6. Are you experiencing any new or severe symptoms?**")
        urgent_symptoms = st.radio(
            "For example: chest pain, difficulty breathing, or fainting",
            ["No", "Yes", "Not sure"],
            horizontal=True,
        )
        st.markdown("**7. How would you describe your stress level or mood today?**")
        stress = st.select_slider(
            "Stress level",
            options=["Very low", "Low", "Moderate", "High", "Very high"],
            value="Moderate",
        )
        st.markdown("**8. Anything else the mission medical team should know?**")
        details = st.text_area(
            "Additional notes (optional)",
            placeholder="Add any other details you want included in the report.",
        )
        submitted = st.form_submit_button("Complete health checkup", type="primary")

    if submitted:
        answers = [
            {"question": voice_questions[0], "answer": feeling},
            {"question": voice_questions[1], "answer": energy},
            {"question": voice_questions[2], "answer": f"{sleep_quality}; approximately {sleep_hours:g} hours"},
            {"question": voice_questions[3], "answer": ", ".join(symptoms) if symptoms else "No symptoms selected"},
            {"question": voice_questions[4], "answer": f"Pain level {pain_level}/10; location: {pain_location or 'Not specified'}"},
            {"question": voice_questions[5], "answer": urgent_symptoms},
            {"question": voice_questions[6], "answer": stress},
            {"question": voice_questions[7], "answer": details.strip() or "No additional notes"},
        ]
        record = {
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "checkup_date": today_key,
            "astronaut_id": (latest or {}).get("astronaut_id", "AST-001"),
            "method": "Fill-in form",
            "answers": answers,
            "feeling": feeling,
            "energy": energy,
            "sleep_quality": sleep_quality,
            "sleep_hours_reported": sleep_hours,
            "symptoms": symptoms,
            "pain_level": pain_level,
            "pain_location": pain_location.strip(),
            "urgent_symptoms": urgent_symptoms,
            "stress": stress,
            "additional_notes": details.strip(),
            "latest_crew_observation": dict(latest) if latest else None,
            "latest_radiation_observation": dict(radiation[-1]) if radiation else None,
        }
        st.session_state.cosmo_checkup_records.append(record)
        st.session_state.cosmo_checkup_completed_date = today_key
        st.session_state.cosmo_latest_checkup_report = record
        st.success("Your checkup has been saved.")
        st.rerun()

report = st.session_state.get("cosmo_latest_checkup_report")
if report:
    st.divider()
    st.subheader("3. Checkup report")
    st.caption(f"Completed: {report.get('completed_at', 'Time unavailable')} · Method: {report.get('method', 'Not specified')}")
    st.write(f"**Astronaut:** {report.get('astronaut_id', 'Not specified')}")
    report_answers = report.get("answers", [])
    if report_answers:
        st.markdown("**Interview responses**")
        for item in report_answers:
            with st.container(border=True):
                st.markdown(f"**{item.get('question', 'Question')}**")
                st.write(item.get("answer") or "No answer recorded")

    observed = report.get("latest_crew_observation")
    if observed:
        st.markdown("**Latest available measurement evidence**")
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
            rows.append({
                "Measurement": label,
                "Latest value": f"{value} {unit}" if value is not None else "Not available",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning("No physiological/environmental measurement was available for this report.")

    if report.get("latest_radiation_observation"):
        st.caption(
            "A radiation detector count-rate record was present as instrument context only. "
            "It is not interpreted as a personal radiation dose."
        )
    if report.get("urgent_symptoms") in ("Yes", "Not sure") or any(
        any(term in str(item.get("answer", "")).lower() for term in ("chest pain", "difficulty breathing", "fainting"))
        for item in report_answers
    ):
        st.warning(
            "A new or severe symptom was reported or may have been mentioned. "
            "Contact the mission's qualified medical team and follow approved emergency procedures. "
            "This app does not triage emergencies."
        )
    st.caption(
        "This report records answers and available observations only. It does not determine "
        "whether an astronaut is medically fit or unfit, and it does not replace clinical review."
    )

if st.session_state.cosmo_checkup_records:
    with st.expander("Checkup history (this session)"):
        history = [
            {
                "Completed": r.get("completed_at"),
                "Astronaut": r.get("astronaut_id"),
                "Method": r.get("method"),
                "Responses recorded": len(r.get("answers", [])),
            }
            for r in reversed(st.session_state.cosmo_checkup_records)
        ]
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)

st.caption(
    "Voice answers are transcribed by the browser's speech-recognition service; "
    "the app receives text transcripts, not raw microphone recordings. Checkup records "
    "are held in Streamlit session state for this prototype and may disappear when the session resets."
)
