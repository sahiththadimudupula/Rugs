from __future__ import annotations

import streamlit as st

from calculations.pipeline import run_full_pipeline
from core.workbook_io import load_workbook_tables


def initialize_state() -> None:
    if "initialized" in st.session_state:
        return

    source_state = load_workbook_tables()
    pipeline_output = run_full_pipeline(source_state)

    st.session_state.update(source_state)
    st.session_state.update(pipeline_output)
    st.session_state["initialized"] = True


def rerun_pipeline() -> None:
    source_state = {
        "master_source_df": st.session_state["master_source_df"],
        "packing_source_df": st.session_state["packing_source_df"],
        "capacity_source_df": st.session_state["capacity_source_df"],
        "coating_source_df": st.session_state["coating_source_df"],
        "cs_source_df": st.session_state["cs_source_df"],
        "hydro_source_df": st.session_state["hydro_source_df"],
        "dye_mc_source_df": st.session_state["dye_mc_source_df"],
        "packing_tfo_raw_df": st.session_state["packing_tfo_raw_df"],
        "packing_edit_df": st.session_state.get("packing_edit_df"),
        "coating_edit_df": st.session_state.get("coating_edit_df"),
        "hydro_edit_df": st.session_state.get("hydro_edit_df"),
        "master_df": st.session_state.get("master_df"),
    }
    pipeline_output = run_full_pipeline(source_state)
    st.session_state.update(pipeline_output)
