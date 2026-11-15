import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

from modules.radiation_monitor import (
    make_reading,
    make_simulated_reading,
    analyze_readings,
)
from ui_theme import apply_theme

apply_theme()
st.title("Radiation monitoring")
st.caption("Simulated detector telemetry, count-rate history and illustrative exposure assessment.")

st.warning(
    "SIMULATION MODE: all generated values are synthetic and are not real astronaut "
    "measurements. CPS is detector count rate, not dose. The simulated dose-rate "
    "channel is generated independently; no CPS-to-dose conversion is performed."
)

if "radiation_history" not in st.session_state:
    st.session_state.radiation_history = []

st.subheader("Simulated sensor input")
st.caption(
    "Choose a mission scenario and generate a stream of sample readings. "
    "The simulator produces detector CPS and a separate illustrative dose-rate channel."
)
scenario = st.selectbox(
    "Radiation environment",
    [
        "Normal orbital conditions",
        "South Atlantic Anomaly pass",
        "Solar particle event",
    ],
    help="These are demonstration scenarios, not predictions of actual space weather."
)
sim_col1, sim_col2, sim_col3 = st.columns([1, 1, 1])
with sim_col1:
    if st.button("Generate next reading", type="primary", use_container_width=True):
        st.session_state.radiation_history.append(
            make_simulated_reading(st.session_state.radiation_history, scenario)
        )
        st.rerun()
with sim_col2:
    if st.button("Simulate 10-minute stream", use_container_width=True):
        now = datetime.now(timezone.utc)
        for index in range(10):
            stamp = (now - timedelta(minutes=9 - index)).isoformat(timespec="seconds")
            st.session_state.radiation_history.append(
                make_simulated_reading(
                    st.session_state.radiation_history, scenario, timestamp=stamp
                )
            )
        st.rerun()
with sim_col3:
    if st.button("Clear history", use_container_width=True):
        st.session_state.radiation_history = []
        st.rerun()

with st.expander("Manual detector input (for future hardware testing)"):
    with st.form("radiation_input"):
        c1, c2 = st.columns(2)
        with c1:
            detector_id = st.text_input("Detector ID", "RAD-01")
            radiation_type = st.selectbox(
                "Radiation type reported",
                ["Unclassified", "Neutron", "Gamma", "Proton", "Other"],
            )
        with c2:
            cps = st.number_input(
                "Count rate (counts/second)", min_value=0.0, value=10.0, step=1.0
            )
            sensor_status = st.selectbox(
                "Detector status", ["operational", "warning", "fault"]
            )
        submitted = st.form_submit_button("Record manual reading")
    if submitted:
        try:
            item = make_reading(
                detector_id=detector_id,
                count_rate_cps=cps,
                radiation_type=radiation_type,
                sensor_status=sensor_status,
                source="Manual entry",
            )
            st.session_state.radiation_history.append(item)
            st.success("Manual count-rate reading recorded.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

multiplier = st.slider(
    "Anomaly multiplier",
    1.1,
    10.0,
    2.0,
    0.1,
    help="Demo heuristic compared with the median of prior readings; not a radiation safety limit.",
)
analysis = analyze_readings(
    st.session_state.radiation_history, anomaly_multiplier=multiplier
)

if analysis["count"]:
    history = st.session_state.radiation_history
    latest = history[-1]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latest count rate", f'{analysis["latest_cps"]:g} CPS')
    m2.metric("Average count rate", f'{analysis["average_cps"]:.2f} CPS')
    m3.metric("Peak count rate", f'{analysis["peak_cps"]:g} CPS')
    m4.metric("Readings", analysis["count'])

    if analysis["anomaly"]:
        st.warning("Unusual count-rate increase: " + analysis["message"])
    else:
        st.info(analysis["message"])

    dose_rows = [
        row for row in history
        if row.get("dose_rate_usv_h") is not None
        and row.get("sensor_status") == "operational"
    ]
    if dose_rows:
        latest_dose = float(dose_rows[-1]["dose_rate_usv_h"])
        cumulative = float(dose_rows[-1].get("cumulative_session_dose_msv") or 0.0)
        daily_projection = latest_dose * 24.0 / 1000.0

        st.subheader("Simulated exposure assessment")
        d1, d2, d3 = st.columns(3)
        d1.metric("Latest simulated dose rate", f"{latest_dose:.2f} µSv/h")
        d2.metric("Projected 24-hour dose*", f"{daily_projection:.3f} mSv")
        d3.metric("Accumulated in this demo session", f"{cumulative:.6f} mSv")

        st.caption(
            "*A simple projection assuming the latest rate remains constant for 24 hours. "
            "It is not a forecast or a clinical risk calculation."
        )

        # These are explicitly prototype alert bands, not NASA medical thresholds.
        if latest_dose >= 100:
            st.error("HIGH SIMULATED EXPOSURE — prototype alert")
            st.markdown(
                "- Follow the mission's approved radiation-event and shelter procedure.
"
                "- Move to the designated shielded area if instructed by mission control.
"
                "- Suspend non-essential EVA or exposed activities under mission procedures.
"
                "- Notify the radiation officer / flight surgeon and verify the reading."
            )
        elif latest_dose >= 25:
            st.warning("ELEVATED SIMULATED EXPOSURE — prototype alert")
            st.markdown(
                "- Check the radiation trend and confirm detector status.
"
                "- Review current space-weather and mission-control advisories.
"
                "- Limit avoidable time in less-shielded locations while awaiting guidance."
            )
        else:
            st.success("ROUTINE SIMULATED RANGE — prototype assessment")
            st.markdown(
                "- Continue routine monitoring and follow the mission radiation-protection plan.
"
                "- Keep cumulative exposure records and check detector health."
            )

        st.caption(
            "The 25 and 100 µSv/h bands are demonstration triggers chosen for this prototype, "
            "not validated astronaut health thresholds. They must be replaced by mission-approved "
            "limits before any operational use."
        )

        st.info(
            f"NASA's published spaceflight standard sets a career effective-dose limit of "
            f"600 mSv. The value above is only the dose accumulated during this simulated "
            f"app session; it is NOT the astronaut's career dose and must not be compared "
            f"as a real compliance result."
        )
        st.markdown(
            "Reference: [NASA-STD-3001 radiation protection requirements]"
            "(https://www.nasa.gov/reference/4-0-human-performance/)."
        )

    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    st.subheader("Count-rate trend")
    st.line_chart(
        df.set_index("timestamp")["count_rate_cps"],
        y_label="Counts per second (CPS)",
    )

    if "dose_rate_usv_h" in df.columns and df["dose_rate_usv_h"].notna().any():
        st.subheader("Simulated dose-rate trend")
        dose_df = df.dropna(subset=["dose_rate_usv_h"]).set_index("timestamp")
        st.line_chart(dose_df["dose_rate_usv_h"], y_label="Dose rate (µSv/h)")

    st.subheader("Telemetry history")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Export radiation history (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        "cosmo_care_radiation_history.csv",
        "text/csv",
    )

    if latest["sensor_status"] != "operational":
        st.error(
            "The latest detector status is not operational. Treat the measurement "
            "stream as potentially unreliable; do not use it for exposure decisions."
        )
else:
    st.info("No radiation readings yet. Generate simulated sensor inputs to begin.")

st.caption(
    "This is a hackathon simulation, not a radiation dosimeter or medical decision-support "
    "system. Real deployment requires calibrated, radiation-type-aware dosimetry, validated "
    "mission thresholds, crew-specific dose records and review by qualified radiation/medical staff."
)
