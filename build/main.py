from __future__ import annotations
import streamlit as st
from config.constants import APP_TITLE, TAB_ORDER, PRE_PROCESSING_SECTIONS, FINAL_SECTIONS
from core.bootstrap import bootstrap_state
from ui.styles import apply_styles
from ui.tabs import render_ppc_tab, render_generic_section_tab, render_coating_tab, render_cut_and_sew_tab, render_hydro_tab, render_final_master_tab

def run_app():
    apply_styles()
    if "build1_state" not in st.session_state:
        st.session_state["build1_state"] = bootstrap_state()
    state = st.session_state["build1_state"]
    st.title(APP_TITLE)
    st.caption("Build 1: PPC → Capacity → Coating / CS / Hydro propagation with fast row-level manpower recalculation.")
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
        render_hydro_tab(state)
    with tabs[5]:
        render_generic_section_tab(state, FINAL_SECTIONS, "final")
    with tabs[6]:
        render_final_master_tab(state)
