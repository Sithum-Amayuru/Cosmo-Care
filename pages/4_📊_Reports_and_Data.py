import streamlit as st
import pandas as pd
from ui_theme import apply_theme

st.set_page_config(page_title="Reports & Data | COSMO CARE", page_icon="📊", layout="wide")
apply_theme()
st.title("Reports & data")
st.caption("Review and export records captured during the current application session.")

radiation = st.session_state.get("radiation_history", [])
crew = st.session_state.get("crew_readings", [])
a, b = st.columns(2)
a.metric("Radiation records", len(radiation))
b.metric("Crew / environment records", len(crew))

if radiation:
    st.subheader("Radiation data")
    rdf = pd.DataFrame(radiation)
    st.dataframe(rdf, use_container_width=True, hide_index=True)
    st.download_button("Download radiation CSV", rdf.to_csv(index=False).encode("utf-8"), "cosmo_care_radiation.csv", "text/csv")
else:
    st.info("No radiation data available in this session.")

if crew:
    st.subheader("Crew and environment data")
    cdf = pd.DataFrame(crew)
    st.dataframe(cdf, use_container_width=True, hide_index=True)
    st.download_button("Download crew/environment CSV", cdf.to_csv(index=False).encode("utf-8"), "cosmo_care_crew_environment.csv", "text/csv")
else:
    st.info("No crew/environment data available in this session.")

st.warning("These records are held in Streamlit session state and may disappear when the session resets. This prototype is not a secure medical-record system.")
