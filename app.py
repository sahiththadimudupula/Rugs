from __future__ import annotations

import streamlit as st

from config.constants import APP_TITLE
from core.state import initialize_state, rerun_pipeline
from core.workbook_io import export_workbook_bytes, save_workbook_tables, reset_working_workbook
from ui.styles import apply_app_styles
from ui.tabs import (
    render_ppc_tab,
    render_pre_processing_tab,
    render_coating_tab,
    render_cut_and_sew_tab,
    render_dyeing_tab,
    render_packing_tqm_tab,
    render_final_sections_tab,
    render_final_master_sheet,
)


def render_bottom_actions() -> None:
    st.markdown('<div class="bottom-actions"></div>', unsafe_allow_html=True)
    action_col1, action_col2, action_col3 = st.columns([1, 1, 2])

    with action_col1:
        if st.button("Freeze Changes", width="stretch"):
            saved_path = save_workbook_tables(st.session_state)
            st.success(f"Changes saved to: {saved_path}")

    with action_col2:
        if st.button("Reset from Input", width="stretch"):
            reset_working_workbook()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    with action_col3:
        st.download_button(
            "Download Full Excel",
            data=export_workbook_bytes(st.session_state),
            file_name="Rugs_working.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_app_styles()
    st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)

    initialize_state()

    tab_labels = [
        "PPC data",
        "pre procesing",
        "Coating",
        "Cut & Sew",
        "Dyeing",
        "packing&tqm",
        "final section",
        "Final Master Sheet",
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_ppc_tab()
        rerun_pipeline()

    with tabs[1]:
        render_pre_processing_tab()

    with tabs[2]:
        render_coating_tab()
        rerun_pipeline()

    with tabs[3]:
        render_cut_and_sew_tab()

    with tabs[4]:
        render_dyeing_tab()
        rerun_pipeline()

    with tabs[5]:
        render_packing_tqm_tab()

    with tabs[6]:
        render_final_sections_tab()

    with tabs[7]:
        render_final_master_sheet()

    render_bottom_actions()


if __name__ == "__main__":
    main()
