from __future__ import annotations

import streamlit as st


def apply_app_styles() -> None:
    st.markdown(
        '''
        <style>
        #MainMenu, header, footer {visibility: hidden;}
        .stApp {
            background: #ffffff;
            color: #111111;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 4rem;
            max-width: 108rem;
        }
        .app-title {
            color: #1f5fe0;
            font-size: 1.9rem;
            font-weight: 800;
            margin-bottom: 0.8rem;
        }
        h3 {
            color: #163b8c;
            font-weight: 750;
            margin-top: 0.7rem;
        }
        .metric-card {
            background: linear-gradient(90deg, #ffffff 0%, #ffffff 70%, #eef6ff 100%);
            border: 1px solid #d8e4fb;
            border-top: 4px solid #2d7ef7;
            border-radius: 18px;
            padding: 1rem 1.2rem;
            min-height: 120px;
            box-shadow: 0 6px 14px rgba(19, 76, 168, 0.06);
            margin-bottom: 1rem;
        }
        .metric-label {
            color: #4a607f;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            color: #081f4d;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.4rem;
        }
        .metric-note {
            color: #5c708f;
            font-size: 0.95rem;
        }
        .section-card {
            background: #ffffff;
            border: 1px solid #dde8fb;
            border-radius: 16px;
            padding: 0.9rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 10px rgba(19, 76, 168, 0.04);
        }
        .section-title {
            color: #1f5fe0;
            font-size: 1.08rem;
            font-weight: 800;
            margin-bottom: 0.6rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.55rem;
            border-bottom: 1px solid #d8e4fb;
            padding-bottom: 0.4rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid #b8cff8;
            border-radius: 999px;
            color: #1f5fe0;
            padding: 0.75rem 1.25rem;
            font-weight: 700;
        }
        .stTabs [aria-selected="true"] {
            background: #eef5ff;
            border-color: #2d7ef7;
            box-shadow: inset 0 -2px 0 #2d7ef7;
        }
        .stMultiSelect label, .stDataFrame label, .stSelectbox label {
            color: #163b8c !important;
            font-weight: 700 !important;
        }
        [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #111111 !important;
            border: 1px solid #d8e4fb !important;
        }
        [data-testid="stDataEditor"], .stDataFrame {
            background: #ffffff !important;
            border-radius: 12px;
        }
        [data-testid="stDataEditor"] input, [data-testid="stDataEditor"] textarea {
            color: #111111 !important;
        }
        .stButton > button, .stDownloadButton > button {
            background: #ffffff;
            color: #163b8c;
            border: 1px solid #b8cff8;
            border-radius: 12px;
            font-weight: 700;
            min-height: 2.8rem;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: #2d7ef7;
            color: #0f4fc7;
        }
        .bottom-actions {
            padding-top: 1rem;
            border-top: 1px solid #e3ebfb;
            margin-top: 1.2rem;
        }
        </style>
        ''',
        unsafe_allow_html=True,
    )
