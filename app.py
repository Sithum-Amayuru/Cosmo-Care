import streamlit as st

st.set_page_config(
    page_title="COSMO CARE | Mission Control",
    page_icon="🛰️",
    layout="wide",
)

# Explicitly register every page. This avoids relying on automatic page discovery.
pages = [
    st.Page("home.py", title="Mission Overview", icon="🏠", default=True),
    st.Page("pages/face_login.py", title="Face Detection Login (Test)", icon="📷"),
    st.Page("pages/radiation_monitoring.py", title="Radiation Monitoring", icon="☢️"),
    st.Page("pages/crew_environment.py", title="Crew & Environment", icon="🫀"),
    st.Page("pages/personalized_health.py", title="Personalized Health", icon="🥗"),
    st.Page("pages/reports_and_data.py", title="Reports & Data", icon="📊"),
]

navigation = st.navigation(pages, position="sidebar", expanded=True)
navigation.run()
