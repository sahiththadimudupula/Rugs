from __future__ import annotations
import streamlit as st
import pandas as pd
from config.constants import *
from config.settings import DOWNLOAD_FILE_NAME
from engines.pipeline import recalc_all
from services.master_rows import apply_master_edit
from services.summaries import build_summary, add_total_row
from core.persistence import save_snapshot, workbook_bytes, reset_working_file

def render_cards(summary: dict[str, float], label_one="Scientific Manpower", label_two="Final Manpower"):
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-label">Visible Sections</div><div class="kpi-value">{int(summary['visible_section_count'])}</div></div>
      <div class="kpi-card"><div class="kpi-label">{label_one}</div><div class="kpi-value">{summary['scientific_total']:,.2f}</div></div>
      <div class="kpi-card"><div class="kpi-label">{label_two}</div><div class="kpi-value">{summary['final_total']:,.2f}</div></div>
    </div>
    """, unsafe_allow_html=True)

def section_df(state: dict, sections: list[str]) -> pd.DataFrame:
    return state["master_df"][state["master_df"]["Section"].isin(sections)].copy()

def sync_ppc_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state["snapshots"]["ppc_df"]
    changed = False
    for i, row in edited_df.iterrows():
        if row["row_type"] != "input":
            continue
        old = float(old_df.at[i, "Asking_Rate_Per_Day"])
        new = float(row["Asking_Rate_Per_Day"])
        if old != new:
            state["ppc_df"].at[i, "Asking_Rate_Per_Day"] = new
            changed = True
    if changed:
        recalc_all(state)
        state["snapshots"]["ppc_df"] = state["ppc_df"].copy(deep=True)

def sync_coating_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state["snapshots"]["coating_df"]
    changed = False
    for i, row in edited_df.iterrows():
        if row["row_type"] != "input":
            continue
        old = float(old_df.at[i, "Value"])
        new = float(row["Value"])
        if old != new:
            state["coating_df"].at[i, "Value"] = new
            changed = True
    if changed:
        recalc_all(state)
        state["snapshots"]["coating_df"] = state["coating_df"].copy(deep=True)

def sync_hydro_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state["snapshots"]["hydro_df"].drop(columns=["row_order"])
    changed = False
    editable = {"Efficiency", "additional Req", "M/s Capacity Proposed", "No. Of Batch"}
    for col in editable:
        old = float(old_df.at[0, col]); new = float(edited_df.at[0, col])
        if old != new:
            state["hydro_df"].at[0, col] = new
            changed = True
    if changed:
        recalc_all(state)
        state["snapshots"]["hydro_df"] = state["hydro_df"].copy(deep=True)

def sync_master_edits(state: dict, original_df: pd.DataFrame, edited_df: pd.DataFrame):
    compare_cols = list(edited_df.columns)
    for row_id in edited_df.index.tolist():
        old_row = original_df[original_df["row_id"] == row_id].iloc[0]
        new_row = edited_df.loc[row_id]
        for col in compare_cols:
            if str(old_row[col]) != str(new_row[col]):
                apply_master_edit(state, row_id, col, new_row[col])

def render_master_editor(state: dict, df: pd.DataFrame, key: str):
    display_df = df.drop(columns=["row_order"]).set_index("row_id")
    edited_df = st.data_editor(
        display_df,
        key=key,
        width="stretch",
        height=min(800, 44 * (len(display_df) + 3)),
        hide_index=True,
        disabled=[c for c in display_df.columns if c not in EDITABLE_MASTER_COLUMNS],
        column_config={"Operator_Type": st.column_config.SelectboxColumn("Operator_Type", options=OPERATOR_TYPE_OPTIONS)},
    )
    sync_master_edits(state, df.copy(), edited_df)

def render_ppc_tab(state: dict):
    temp = state["ppc_df"][["Main_Group", "Asking_Rate_Per_Day"]].copy()
    temp["Section"] = temp["Main_Group"]
    temp["BE_Scientific_Manpower"] = temp["Asking_Rate_Per_Day"]
    temp["BE_Final_Manpower"] = temp["Asking_Rate_Per_Day"]
    temp["Machine_Count"] = temp["Asking_Rate_Per_Day"]
    render_cards(build_summary(temp[["Section", "Machine_Count", "BE_Scientific_Manpower", "BE_Final_Manpower"]]), "Total Asking Rate", "Displayed Total")
    st.caption("Edit only base PPC rows. Calculated rows will refresh automatically.")
    edited_df = st.data_editor(state["ppc_df"], key="ppc_editor", width="stretch", height=620, hide_index=True, disabled=["Main_Group", "Sub_Group", "Category", "Subcategory", "row_type", "row_order"])
    sync_ppc_changes(state, edited_df)
    st.dataframe(add_total_row(state["ppc_df"].drop(columns=["row_order"])), width="stretch", hide_index=True)

def render_generic_section_tab(state: dict, sections: list[str], tab_key: str):
    df = section_df(state, sections)
    render_cards(build_summary(df))
    if df.empty:
        st.info("No rows found.")
        return
    compact = df[["Section", "Dept_Machine_Name", "Designation", "Machine_Count", "BE_Final_Manpower"]]
    st.dataframe(add_total_row(compact), width="stretch", hide_index=True)
    for section_name in df["Section"].drop_duplicates().tolist():
        part = df[df["Section"] == section_name].copy()
        with st.expander(section_name, expanded=False):
            render_master_editor(state, part, f"{tab_key}_{section_name}")

def render_coating_tab(state: dict):
    df = section_df(state, [COATING_SECTION])
    render_cards(build_summary(df))
    st.subheader("Coating Helper")
    helper_edit = st.data_editor(state["coating_df"], key="coating_helper_editor", width="stretch", height=420, hide_index=True, disabled=["Parameter", "Material", "row_type", "row_order"])
    sync_coating_changes(state, helper_edit)
    st.dataframe(add_total_row(state["coating_df"].drop(columns=["row_order"])), width="stretch", hide_index=True)
    st.subheader("Coating Manpower")
    render_master_editor(state, df, "coating_master_editor")
    st.dataframe(add_total_row(df[["Section", "Sr_No", "Dept_Machine_Name", "Designation", "Machine_Count", "BE_Scientific_Manpower", "BE_Final_Manpower"]]), width="stretch", hide_index=True)

def render_cut_and_sew_tab(state: dict):
    df = section_df(state, [CUT_AND_SEW_SECTION])
    render_cards(build_summary(df))
    st.subheader("Capacity")
    st.dataframe(add_total_row(state["capacity_df"].drop(columns=["row_order"])), width="stretch", hide_index=True)
    st.subheader("CS")
    st.dataframe(add_total_row(state["cs_df"].drop(columns=["row_order"])), width="stretch", hide_index=True)
    st.subheader("Cut & Sew Manpower")
    render_master_editor(state, df, "cut_sew_master_editor")

def render_hydro_tab(state: dict):
    dyeing_df = section_df(state, [DYEING_SECTION])
    linked = dyeing_df[dyeing_df["Sr_No"] == 10].copy()
    render_cards(build_summary(dyeing_df))
    st.subheader("Hydro Helper")
    helper_edit = st.data_editor(state["hydro_df"].drop(columns=["row_order"]), key="hydro_editor", width="stretch", height=180, hide_index=True)
    sync_hydro_changes(state, helper_edit)
    st.dataframe(add_total_row(state["hydro_df"].drop(columns=["row_order"])), width="stretch", hide_index=True)
    st.subheader("Linked Dyeing Row")
    if linked.empty:
        st.info("Linked Hydro row not found.")
    else:
        render_master_editor(state, linked, "hydro_master_editor")

def render_final_master_tab(state: dict):
    render_cards(build_summary(state["master_df"]))
    render_master_editor(state, state["master_df"].copy(), "final_master_editor")
    st.dataframe(add_total_row(state["master_df"].drop(columns=["row_order", "row_id"])), width="stretch", hide_index=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Freeze Changes", width="stretch"):
            save_snapshot(state)
            st.success("Working file updated.")
    with c2:
        st.download_button("Download Full Excel", data=workbook_bytes(state), file_name=DOWNLOAD_FILE_NAME, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    with c3:
        if st.button("Reset from Input", width="stretch"):
            reset_working_file()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
