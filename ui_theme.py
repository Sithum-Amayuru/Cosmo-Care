"""Cosmo Care visual theme and reusable UI elements."""
import streamlit as st


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {
            --cosmo-bg: #07111f;
            --cosmo-panel: #101f33;
            --cosmo-panel-2: #142740;
            --cosmo-cyan: #4bd8f2;
            --cosmo-blue: #4d8dff;
            --cosmo-text: #e8f2ff;
            --cosmo-muted: #93a9c3;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: radial-gradient(ellipse at 50% -20%, #163653 0%, #0a1728 42%, #07111f 100%);
            color: var(--cosmo-text);
            font-family: 'DM Sans', sans-serif;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { right: 1rem; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3, [data-testid="stMetricValue"] {
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: -0.035em;
        }
        h1 { color: #f3f8ff !important; }
        h2, h3 { color: #dcecff !important; }
        p, label, [data-testid="stCaptionContainer"] { color: #a9bdd4; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1b2d 0%, #081321 100%);
            border-right: 1px solid rgba(93, 176, 218, .16);
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 { color: #e8f6ff !important; }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(22, 47, 73, .96), rgba(13, 31, 51, .96));
            border: 1px solid rgba(75, 216, 242, .18);
            border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 8px 24px rgba(0,0,0,.14);
        }
        [data-testid="stMetricLabel"] { color: #9eb8d1 !important; }
        [data-testid="stMetricValue"] { color: #f1f8ff !important; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(100, 171, 211, .18) !important;
            border-radius: 16px;
        }
        .stButton > button, .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            border-radius: 10px;
            border: 1px solid rgba(75, 216, 242, .42);
            background: linear-gradient(100deg, #147eaa, #2764bd);
            color: white;
            font-weight: 700;
            transition: transform .15s ease, box-shadow .15s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 22px rgba(31, 159, 210, .22);
            border-color: #70e6ff;
            color: white;
        }
        [data-baseweb="input"] > div, [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div {
            background: #0e2034;
            border-color: #29445f;
            border-radius: 10px;
        }
        [data-testid="stAlert"] { border-radius: 12px; }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid rgba(100, 171, 211, .18);
            border-radius: 12px;
            overflow: hidden;
        }
        hr { border-color: rgba(100, 171, 211, .18); }
        .cosmo-hero {
            position: relative;
            overflow: hidden;
            padding: 30px 34px;
            margin: 4px 0 22px 0;
            border-radius: 22px;
            border: 1px solid rgba(75,216,242,.28);
            background:
                radial-gradient(circle at 85% 20%, rgba(37, 159, 206, .25), transparent 34%),
                linear-gradient(115deg, #102a43 0%, #0c1d31 58%, #102e49 100%);
            box-shadow: 0 18px 55px rgba(0,0,0,.22);
        }
        .cosmo-hero:after {
            content: '✦';
            position: absolute;
            right: 8%;
            top: 3px;
            font-size: 116px;
            line-height: 1;
            color: rgba(113, 225, 255, .10);
        }
        .cosmo-kicker {
            color: #69dff6;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: .22em;
            text-transform: uppercase;
        }
        .cosmo-title {
            margin: 8px 0 4px 0;
            color: #f4f9ff;
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(30px, 4vw, 43px);
            font-weight: 700;
            letter-spacing: -.045em;
        }
        .cosmo-subtitle { color: #a9c2d9; font-size: 14px; }
        .cosmo-status {
            display: inline-block;
            margin-top: 17px;
            padding: 6px 11px;
            border-radius: 999px;
            color: #8af0c0;
            background: rgba(48, 191, 133, .12);
            border: 1px solid rgba(93, 226, 166, .24);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: .08em;
        }
        .cosmo-nav-label {
            color: #6fdcf2;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: .18em;
            margin: 10px 0 8px 2px;
        }
        .cosmo-nav a {
            display: block;
            padding: 9px 12px;
            margin: 4px 0;
            border-radius: 9px;
            text-decoration: none;
            color: #bfd2e6 !important;
            background: rgba(34, 67, 96, .30);
            border: 1px solid rgba(106, 177, 214, .10);
            font-size: 13px;
            font-weight: 600;
        }
        .cosmo-nav a:hover {
            color: #ffffff !important;
            background: rgba(39, 126, 163, .28);
            border-color: rgba(75,216,242,.42);
        }
        @media (max-width: 700px) {
            .cosmo-hero { padding: 24px 20px; }
            .cosmo-hero:after { right: 4%; font-size: 76px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <section class="cosmo-hero">
            <div class="cosmo-kicker">Astronaut health • Mission safety • Intelligent monitoring</div>
            <div class="cosmo-title">COSMO CARE</div>
            <div class="cosmo-subtitle">A unified health and mission-environment monitoring platform for human spaceflight.</div>
            <div class="cosmo-status">● PROTOTYPE MISSION CONSOLE</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_navigation():
    st.markdown(
        """
        <div class="cosmo-nav-label">MISSION NAVIGATION</div>
        <nav class="cosmo-nav">
            <a href="#mission-overview">◈ Mission overview</a>
            <a href="#radiation-monitoring">◎ Radiation monitoring</a>
            <a href="#crew-readings">♡ Crew & environment</a>
            <a href="#alerts">⚑ Alerts & explanations</a>
            <a href="#mission-record">▤ Measurement record</a>
            <a href="#astronaut-health">✚ Astronaut health</a>
        </nav>
        """,
        unsafe_allow_html=True,
    )
