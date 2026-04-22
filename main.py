from __future__ import annotations
import streamlit as st
from config.constants import APP_TITLE, TAB_ORDER, PRE_PROCESSING_SECTIONS, FINAL_SECTIONS, PACKING_TQM_SECTIONS
from core.bootstrap import bootstrap_state
from ui.styles import apply_styles
from ui.tabs import render_ppc_tab, render_generic_section_tab, render_coating_tab, render_cut_and_sew_tab, render_dyeing_tab, render_packintqm_tab, render_final_master_tab


def run_app():
    apply_styles()
    if "build4_state" not in st.session_state:
        st.session_state["build4_state"] = bootstrap_state()
    state = st.session_state["build4_state"]
    st.markdown(f'<h3 class="app-title">{APP_TITLE}</h3>', unsafe_allow_html=True)
    tabs = st.tabs(TAB_ORDER)
    with tabs[0]:
        render_ppc_tab(state)
    with tabs[1]:
        render_generic_section_tab(state, PRE_PROCESSING_SECTIONS, "pre")
    with tabs[2]:
        render_coating_tab(state)
    with tabs[3]:
        render_cut_and_sew_tab(state)
    with tabs[4]:
        render_dyeing_tab(state)
    with tabs[5]:
        render_packintqm_tab(state)
    with tabs[6]:
        render_generic_section_tab(state, FINAL_SECTIONS, "final")
    with tabs[7]:
        render_final_master_tab(state)
