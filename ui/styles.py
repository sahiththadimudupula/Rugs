from __future__ import annotations
import streamlit as st
from config.constants import APP_TITLE


def apply_styles():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.markdown(
        """
        <style>
        :root {
          --brand:#1d4ed8;
          --brand-2:#2563eb;
          --brand-3:#3b82f6;
          --brand-soft:#eff6ff;
          --brand-soft-2:#dbeafe;
          --text:#0f172a;
          --muted:#475569;
          --border:#dbeafe;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
          background: linear-gradient(180deg,#ffffff 0%, #f8fbff 100%) !important;
          color: var(--text) !important;
        }
        .block-container { padding-top: 0.85rem; padding-bottom: 2rem; }
        #MainMenu, footer, header { visibility:hidden; }
        .app-title {
          color: var(--brand) !important;
          font-size: 1.55rem;
          font-weight: 800;
          letter-spacing: 0.1px;
          margin: 0 0 0.2rem 0;
        }

        .source-badge {
          display:inline-block;
          margin:-0.2rem 0 0.9rem 0;
          padding:0.32rem 0.7rem;
          border-radius:999px;
          background:linear-gradient(180deg,#eff6ff 0%,#dbeafe 100%);
          border:1px solid #bfdbfe;
          color:var(--brand) !important;
          font-size:0.82rem;
          font-weight:700;
          box-shadow:0 6px 16px rgba(37,99,235,0.08);
        }
        h1,h2,h3,h4,h5,h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
          color: var(--brand) !important;
          font-weight: 750 !important;
        }
        p, div, span, label { color: var(--text); }

        .stRadio > div { gap:0.7rem; }
        .stRadio [role="radiogroup"] {
          display:flex; flex-wrap:wrap; gap:0.7rem; padding:0.15rem 0 0.8rem 0; margin-bottom:0.85rem;
          border-bottom: 1px solid var(--brand-soft-2);
        }
        .stRadio label {
          background: linear-gradient(180deg,#ffffff 0%, #f8fbff 100%) !important;
          border:1px solid #bfdbfe !important;
          border-radius:999px !important;
          padding:0.5rem 1rem !important;
          color: var(--brand) !important;
          font-weight:700 !important;
          box-shadow: 0 8px 20px rgba(37,99,235,0.08);
        }
        .stRadio label:has(input:checked) {
          background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%) !important;
          color:#ffffff !important;
          border-color:#2563eb !important;
          box-shadow: 0 14px 28px rgba(37,99,235,0.20), inset 0 -2px 0 rgba(255,255,255,0.22);
        }
        .stRadio label:has(input:checked) * { color:#ffffff !important; }
        .stRadio input { accent-color: var(--brand); }

        .kpi-row { display:flex; gap:14px; margin:12px 0 18px 0; }
        .kpi-card {
          flex:1;
          background: linear-gradient(180deg,#ffffff 0%, #f8fbff 100%);
          border:1px solid var(--brand-soft-2);
          border-radius:18px;
          padding:18px 20px;
          box-shadow: 0 14px 32px rgba(37,99,235,0.08);
          position:relative;
          overflow:hidden;
        }
        .kpi-card::before {
          content:"";
          position:absolute;
          inset:0 0 auto 0;
          height:4px;
          background: linear-gradient(90deg,#1d4ed8,#60a5fa);
        }
        .kpi-card::after {
          content:"";
          position:absolute;
          right:-36px; top:-36px;
          width:120px; height:120px;
          border-radius:999px;
          background: radial-gradient(circle, rgba(59,130,246,0.14), rgba(59,130,246,0.02) 65%, transparent 70%);
        }
        .kpi-label { color: var(--brand) !important; font-size:0.92rem; font-weight:700; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.3px; }
        .kpi-value { color: var(--text) !important; font-size:2rem; font-weight:800; }

        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
          border-radius: 16px !important;
        }
        div[data-testid="stDataFrame"] [role="grid"], div[data-testid="stDataEditor"] [role="grid"],
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"], div[data-testid="stDataEditor"] [data-testid="stDataFrameResizable"] {
          background:#ffffff !important;
          border:1px solid #e5edf9 !important;
          border-radius:16px !important;
          box-shadow: 0 10px 24px rgba(15,23,42,0.04);
        }
        div[data-testid="stDataFrame"] [role="columnheader"], div[data-testid="stDataEditor"] [role="columnheader"] {
          background:#eff6ff !important;
          color:var(--brand) !important;
          font-weight:800 !important;
          border-bottom:1px solid #dbeafe !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"], div[data-testid="stDataEditor"] [role="gridcell"],
        div[data-testid="stDataEditor"] input, div[data-testid="stDataEditor"] textarea, div[data-testid="stDataEditor"] select {
          background:#ffffff !important; color:#111827 !important;
        }
        div[data-testid="stDataFrame"] *, div[data-testid="stDataEditor"] * { color:#111827 !important; }

        .stButton button, .stDownloadButton button {
          border-radius:12px !important;
          border:1px solid #93c5fd !important;
          background: linear-gradient(180deg,#ffffff 0%, #eff6ff 100%) !important;
          color: var(--brand) !important;
          font-weight:700 !important;
          box-shadow: 0 8px 18px rgba(37,99,235,0.08);
        }
        .stButton button:hover, .stDownloadButton button:hover {
          background: linear-gradient(180deg,#eff6ff 0%, #dbeafe 100%) !important;
          border-color:#60a5fa !important;
        }
        div[data-testid="stExpander"] details {
          background:#ffffff !important;
          border:1px solid #dbeafe !important;
          border-radius:14px !important;
          box-shadow: 0 8px 18px rgba(15,23,42,0.04);
        }
        div[data-testid="stExpander"] summary { color: var(--brand) !important; font-weight:700 !important; }
        .stMultiSelect [data-baseweb="select"], .stSelectbox [data-baseweb="select"] {
          background:#ffffff !important; color:#111827 !important; border-radius:12px !important;
          border:1px solid #dbeafe !important;
        }
        .bottom-actions-spacer { height:0.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
