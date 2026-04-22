from __future__ import annotations
import streamlit as st
from config.constants import APP_TITLE

def apply_styles():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.markdown(
        """
        <style>
        .stApp { background: #ffffff; color: #111827; }
        .block-container { padding-top: 1rem; padding-bottom: 1.5rem; }
        h1, h2, h3, h4 { color: #1d4ed8; }
        div[data-testid="stDataEditor"] * { color: #111827 !important; }
        div[data-testid="stDataFrame"] * { color: #111827 !important; }
        .kpi-row { display:flex; gap:12px; margin:8px 0 16px 0; }
        .kpi-card { flex:1; background:#fff; border:1px solid #dbeafe; border-radius:14px; padding:14px 16px; box-shadow:0 1px 3px rgba(15,23,42,.06); }
        .kpi-label { color:#475569; font-size:.88rem; margin-bottom:6px; }
        .kpi-value { color:#0f172a; font-weight:700; font-size:1.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
