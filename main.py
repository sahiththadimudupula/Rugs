from __future__ import annotations
import streamlit as st
from config.constants import APP_TITLE, TAB_ORDER, PRE_PROCESSING_SECTIONS, FINAL_SECTIONS
from core.bootstrap import bootstrap_state
from ui.styles import apply_styles
from ui.tabs import render_ppc_tab, render_generic_section_tab, render_coating_tab, render_cut_and_sew_tab, render_dyeing_tab, render_packintqm_tab, render_final_master_tab


def run_app():
    apply_styles()
    if "build4_state" not in st.session_state:
        st.session_state["build4_state"] = bootstrap_state()
    state = st.session_state["build4_state"]
    source_label = 'Working File' if state.get('using_working_file') else 'Input File'
    st.markdown(f'<h3 class="app-title">{APP_TITLE}</h3><div class="source-badge">Source: {source_label}</div>', unsafe_allow_html=True)
    active_tab = st.radio("Navigation", TAB_ORDER, horizontal=True, key="active_nav_tab", label_visibility="collapsed")
    if active_tab == TAB_ORDER[0]:
        render_ppc_tab(state)
    elif active_tab == TAB_ORDER[1]:
        render_generic_section_tab(state, PRE_PROCESSING_SECTIONS, "pre")
    elif active_tab == TAB_ORDER[2]:
        render_coating_tab(state)
    elif active_tab == TAB_ORDER[3]:
        render_cut_and_sew_tab(state)
    elif active_tab == TAB_ORDER[4]:
        render_dyeing_tab(state)
    elif active_tab == TAB_ORDER[5]:
        render_packintqm_tab(state)
    elif active_tab == TAB_ORDER[6]:
        render_generic_section_tab(state, FINAL_SECTIONS, "final")
    else:
        render_final_master_tab(state)
