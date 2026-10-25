"""EDP visual identity for the Streamlit demonstration."""

from html import escape

import streamlit as st


EDP_NAVY = "#212E3E"
EDP_GREEN = "#28FF52"
EDP_SLATE_GREY = "#7C9599"
EDP_ICE_BLUE = "#0CD3F8"
EDP_WHITE = "#FFFFFF"


def apply_edp_theme() -> None:
    """Apply the three-color EDP demo palette to Streamlit components."""

    st.markdown(
        f"""
        <style>
        :root {{
            --edp-navy: {EDP_NAVY};
            --edp-green: {EDP_GREEN};
            --edp-slate-grey: {EDP_SLATE_GREY};
            --edp-ice-blue: {EDP_ICE_BLUE};
            --edp-white: {EDP_WHITE};
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {{
            background: var(--edp-navy);
            color: var(--edp-white);
        }}

        [data-testid="stHeader"] {{
            background: rgba(33, 46, 62, 0.96);
            border-bottom: 1px solid rgba(124, 149, 153, 0.28);
        }}

        [data-testid="stSidebar"] {{
            background: var(--edp-navy);
            border-right: 1px solid rgba(124, 149, 153, 0.35);
        }}

        .block-container {{
            padding-top: 3rem;
            padding-bottom: 4rem;
        }}

        h1 {{
            color: var(--edp-white) !important;
            letter-spacing: -0.025em;
        }}

        h2, h3,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: var(--edp-white) !important;
        }}

        p, label, span,
        [data-testid="stCaptionContainer"],
        [data-testid="stMarkdownContainer"] {{
            color: var(--edp-white);
        }}

        a {{
            color: var(--edp-ice-blue) !important;
        }}

        hr {{
            border-color: rgba(124, 149, 153, 0.30) !important;
        }}

        [data-testid="stMetric"] {{
            min-height: 142px;
            padding: 1.15rem 1.25rem;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-top: 3px solid var(--edp-green);
            border-radius: 10px;
        }}

        [data-testid="stMetricLabel"] p {{
            color: rgba(255, 255, 255, 0.78) !important;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--edp-green) !important;
        }}

        [data-testid="stAlert"] {{
            color: var(--edp-white);
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-left: 4px solid var(--edp-ice-blue);
        }}

        .edp-status-badge {{
            margin-top: 0.9rem;
            margin-bottom: 0.75rem;
            padding: 0.85rem 1rem;
            color: var(--edp-white);
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-left: 4px solid var(--edp-slate-grey);
            border-radius: 4px;
            font-weight: 700;
            letter-spacing: 0.015em;
        }}

        .stButton > button,
        .stLinkButton > a {{
            color: var(--edp-navy) !important;
            background: var(--edp-green) !important;
            border: 1px solid var(--edp-green) !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
        }}

        .stButton > button:hover,
        .stLinkButton > a:hover {{
            color: var(--edp-white) !important;
            background: transparent !important;
        }}

        [data-baseweb="select"] > div,
        [data-baseweb="button-group"] {{
            color: var(--edp-white);
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(124, 149, 153, 0.42);
        }}

        [data-baseweb="button-group"] button[aria-pressed="true"] {{
            color: var(--edp-navy) !important;
            background: var(--edp-green) !important;
        }}

        [data-testid="stCode"] {{
            border: 1px solid rgba(124, 149, 153, 0.30);
        }}

        [data-testid="stExpander"] {{
            border-color: rgba(124, 149, 153, 0.32);
        }}

        ::selection {{
            color: var(--edp-navy);
            background: var(--edp-green);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text: str) -> None:
    """Render a safe status label using only the EDP palette."""

    st.markdown(
        f'<div class="edp-status-badge">{escape(text)}</div>',
        unsafe_allow_html=True,
    )
