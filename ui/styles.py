from __future__ import annotations
import streamlit as st
from config.constants import APP_TITLE


def apply_styles():
    st.set_page_config(page_title=APP_TITLE, layout='wide')
    st.markdown(
        """
        <style>
        :root {
            --primary-blue:#2563eb;
            --deep-blue:#1d4ed8;
            --light-blue:#eaf3ff;
            --card-blue:#f7fbff;
            --text:#0f172a;
            --muted:#64748b;
            --line:#d8e7ff;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
            background: linear-gradient(180deg, #f7fbff 0%, #ffffff 22%) !important;
            color:var(--text) !important;
        }
        .block-container { padding-top: 1rem; padding-bottom: 2.25rem; max-width: 96rem; }
        #MainMenu, footer, header { visibility:hidden; }

        .app-title {
            color:var(--primary-blue);
            font-size:1.55rem;
            font-weight:800;
            margin:0 0 0.95rem 0;
            letter-spacing:0.01em;
        }

        h1,h2,h3,h4,h5,h6,
        .stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4,.stMarkdown h5,.stMarkdown h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6,
        [data-testid="stWidgetLabel"],
        .st-emotion-cache-16idsys p,
        .st-emotion-cache-10trblm {
            color:var(--deep-blue) !important;
        }

        p, div, span, label, .stCaptionContainer {
            color:var(--text);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap:0.65rem;
            border-bottom:1px solid var(--line);
            padding-bottom:0.35rem;
            margin-bottom:0.4rem;
        }
        .stTabs [data-baseweb="tab"] {
            background:#ffffff !important;
            border:1px solid #bfd8ff !important;
            border-radius:18px 18px 0 0 !important;
            padding:0.62rem 1.12rem !important;
            color:var(--deep-blue) !important;
            font-weight:700 !important;
            transition:all .2s ease;
            box-shadow:0 8px 22px rgba(37,99,235,0.05);
        }
        .stTabs [aria-selected="true"] {
            background:linear-gradient(180deg, #2f6efc 0%, #255fe4 100%) !important;
            color:#ffffff !important;
            border-color:#2f6efc !important;
            box-shadow: inset 0 -3px 0 #ef4444, 0 12px 28px rgba(37,99,235,0.18);
        }
        .stTabs [aria-selected="true"] * {
            color:#ffffff !important;
        }

        .kpi-row { display:flex; gap:18px; margin:14px 0 22px 0; }
        .kpi-card {
            flex:1;
            background:linear-gradient(120deg, #ffffff 0%, #ffffff 72%, #edf7ff 100%);
            border:1px solid var(--line);
            border-top:4px solid #2f6efc;
            border-radius:22px;
            padding:18px 20px;
            box-shadow:0 18px 35px rgba(37,99,235,0.08);
            min-height:108px;
        }
        .kpi-label {
            color:#5d6f8d !important;
            font-size:0.95rem;
            margin-bottom:8px;
            font-weight:800;
            text-transform:uppercase;
            letter-spacing:0.03em;
        }
        .kpi-value {
            color:#0f172a !important;
            font-size:1.95rem;
            font-weight:800;
            line-height:1.05;
        }
        .kpi-note {
            color:var(--muted) !important;
            font-size:0.95rem;
            margin-top:6px;
        }

        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border-radius:18px !important;
            overflow:hidden !important;
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"],
        div[data-testid="stDataFrame"] *, div[data-testid="stDataEditor"] * {
            color:#111827 !important;
        }
        div[data-testid="stDataFrame"] [role="grid"], div[data-testid="stDataEditor"] [role="grid"],
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"],
        div[data-testid="stDataEditor"] [data-testid="stDataFrameResizable"] {
            background:#ffffff !important;
            border:1px solid #d9e7fb !important;
            border-radius:16px !important;
            box-shadow:0 10px 26px rgba(15,23,42,0.04);
        }
        div[data-testid="stDataFrame"] [role="columnheader"], div[data-testid="stDataEditor"] [role="columnheader"] {
            background:linear-gradient(180deg, #f4f9ff 0%, #eaf3ff 100%) !important;
            color:var(--deep-blue) !important;
            font-weight:800 !important;
            border-bottom:1px solid #d9e7fb !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"], div[data-testid="stDataEditor"] [role="gridcell"],
        div[data-testid="stDataEditor"] input, div[data-testid="stDataEditor"] textarea, div[data-testid="stDataEditor"] select {
            background:#ffffff !important;
            color:#111827 !important;
        }

        .stButton button, .stDownloadButton button {
            border-radius:12px !important;
            border:1px solid #bfd8ff !important;
            background:#ffffff !important;
            color:var(--deep-blue) !important;
            font-weight:700 !important;
            box-shadow:0 8px 22px rgba(37,99,235,0.07);
        }
        .stButton button:hover, .stDownloadButton button:hover {
            background:#eff6ff !important;
            border-color:#60a5fa !important;
        }

        div[data-testid="stExpander"] details {
            background:#ffffff !important;
            border:1px solid var(--line) !important;
            border-radius:16px !important;
            box-shadow:0 10px 24px rgba(37,99,235,0.05);
        }
        div[data-testid="stExpander"] summary {
            color:var(--deep-blue) !important;
            font-weight:800 !important;
        }

        .stMultiSelect [data-baseweb="select"], .stSelectbox [data-baseweb="select"] {
            background:#ffffff !important;
            color:#111827 !important;
            border-radius:12px !important;
            border:1px solid var(--line) !important;
            box-shadow:0 8px 18px rgba(15,23,42,0.04);
        }

        .stAlert, .stInfo, .stSuccess, .stWarning {
            border-radius:14px !important;
        }

        .bottom-actions-spacer { height:0.35rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
