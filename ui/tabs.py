from __future__ import annotations

import pandas as pd
import streamlit as st

from config.constants import PRE_PROCESSING_SECTIONS, FINAL_SECTION_GROUP, PACKING_TQM_SECTIONS
from ui.components import (
    filter_master_df,
    render_cards,
    render_filter_bar,
    render_filtered_section_group,
    render_summary_table,
    render_table_cards,
)


def render_ppc_tab() -> pd.DataFrame | None:
    st.markdown("### PPC data")
    current_df = st.session_state["asking_rate_df"].copy()
    editable_mask = current_df["row_type"] == "input"

    render_table_cards("Input Rows", int(editable_mask.sum()), "Total Asking Rate", float(current_df["Asking_Rate_Per_Day"].sum()))

    editable_view = current_df[["Main_Group", "Sub_Group", "Category", "Subcategory", "Asking_Rate_Per_Day", "row_type"]].copy()
    edited_df = st.data_editor(
        editable_view,
        key="packing_editor",
        width="stretch",
        hide_index=True,
        disabled=["Main_Group", "Sub_Group", "Category", "Subcategory", "row_type"],
    )
    st.session_state["packing_edit_df"] = edited_df.drop(columns=["row_type"])
    return edited_df


def render_pre_processing_tab() -> None:
    st.markdown("### pre procesing")
    st.session_state["master_df"] = render_filtered_section_group("pre_processing", PRE_PROCESSING_SECTIONS, st.session_state["master_df"])


def render_coating_tab() -> pd.DataFrame | None:
    st.markdown("### Coating")
    coating_df = st.session_state["coating_df"].copy()
    coating_total = float(coating_df[(coating_df["Parameter"] == "Machines Required") & (coating_df["Material"] == "Total")]["Value"].iloc[0])
    coating_drylon = float(coating_df[(coating_df["Parameter"] == "Machines Required") & (coating_df["Material"] == "Drylon")]["Value"].iloc[0])
    render_table_cards("Coating Rows", int(len(coating_df)), "Machines Required", coating_total)

    st.markdown("#### Coating Helper Table")
    edited_df = st.data_editor(coating_df, key="coating_editor", width="stretch", hide_index=True, disabled=["Parameter", "Material"])
    st.session_state["coating_edit_df"] = edited_df
    st.caption(f"Machines Required - Drylon: {coating_drylon:,.6f} | Machines Required - Total: {coating_total:,.0f}")

    st.session_state["master_df"] = render_filtered_section_group("coating_section", ["Coating"], st.session_state["master_df"])
    return edited_df


def render_cut_and_sew_tab() -> None:
    st.markdown("### Cut & Sew")
    cut_and_sew_df = st.session_state["master_df"].copy()
    cut_and_sew_df = cut_and_sew_df[cut_and_sew_df["Section"] == "Cut & Sew"]
    render_cards(cut_and_sew_df["Section"].nunique(), cut_and_sew_df["BE_Final_Manpower"].sum())

    st.markdown("#### Capacity Table")
    st.dataframe(st.session_state["capacity_df"], width="stretch", hide_index=True)
    st.markdown("#### CS Table")
    st.dataframe(st.session_state["cs_df"], width="stretch", hide_index=True)
    st.session_state["master_df"] = render_filtered_section_group("cut_and_sew_section", ["Cut & Sew"], st.session_state["master_df"])


def render_dyeing_tab() -> None:
    st.markdown("### Dyeing")
    dyeing_section_df = st.session_state["master_df"].copy()
    dyeing_section_df = dyeing_section_df[dyeing_section_df["Section"] == "Dyeing"]
    render_cards(dyeing_section_df["Section"].nunique(), dyeing_section_df["BE_Final_Manpower"].sum())

    st.markdown("#### Dyeing Input Drivers")
    st.dataframe(st.session_state["dyeing_result"]["input_driver_df"], width="stretch", hide_index=True)
    st.markdown("#### Dyeing Output Summary")
    st.dataframe(st.session_state["dyeing_result"]["output_summary_df"], width="stretch", hide_index=True)

    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        st.markdown("#### EZM/Paddle Drylon Selection")
        st.dataframe(st.session_state["dyeing_result"]["drylon_selected_df"], width="stretch", hide_index=True)
        st.markdown("#### EZM/Paddle Cotton Selection")
        st.dataframe(st.session_state["dyeing_result"]["cotton_selected_df"], width="stretch", hide_index=True)
    with detail_col2:
        st.markdown("#### Jet Dyeing Selection")
        st.dataframe(st.session_state["dyeing_result"]["jet_selected_df"], width="stretch", hide_index=True)
        st.markdown("#### Hydro Table")
        hydro_df = st.data_editor(st.session_state["hydro_df"], key="hydro_editor", width="stretch", hide_index=True)
        st.session_state["hydro_edit_df"] = hydro_df

    st.session_state["master_df"] = render_filtered_section_group("dyeing_section", ["Dyeing"], st.session_state["master_df"])


def render_packing_tqm_tab() -> None:
    st.markdown("### packing&tqm")
    linked_df = st.session_state["master_df"].copy()
    linked_df = linked_df[linked_df["Section"].isin(PACKING_TQM_SECTIONS)]
    render_cards(linked_df["Section"].nunique(), linked_df["BE_Final_Manpower"].sum())
    st.markdown("#### packing&tqm source sheet")
    st.dataframe(st.session_state["packing_tfo_raw_df"], width="stretch", hide_index=True)
    st.markdown("#### Helper Table")
    st.dataframe(st.session_state["packing_tqm_helper_df"], width="stretch", hide_index=True)
    st.session_state["master_df"] = render_filtered_section_group("packing_tqm_section", PACKING_TQM_SECTIONS, st.session_state["master_df"])


def render_final_sections_tab() -> None:
    st.markdown("### final section")
    st.session_state["master_df"] = render_filtered_section_group("final_section_group", FINAL_SECTION_GROUP, st.session_state["master_df"])


def render_final_master_sheet() -> None:
    st.markdown("### Final Master Sheet")
    selected_sections, selected_designations = render_filter_bar(st.session_state["master_df"], key_prefix="final_master")
    filtered_df = filter_master_df(st.session_state["master_df"], selected_sections, selected_designations)
    render_cards(filtered_df["Section"].nunique(), filtered_df["BE_Final_Manpower"].sum())
    render_summary_table(filtered_df)

    total_row = {column_name: "" for column_name in filtered_df.columns}
    total_row["Section"] = "Total"
    total_row["Machine_Count"] = filtered_df["Machine_Count"].sum()
    total_row["BE_Scientific_Manpower"] = filtered_df["BE_Scientific_Manpower"].sum()
    total_row["Contractors"] = filtered_df["Contractors"].sum()
    total_row["Company_Associate"] = filtered_df["Company_Associate"].sum()
    total_row["BE_Final_Manpower"] = filtered_df["BE_Final_Manpower"].sum()
    display_df = pd.concat([filtered_df, pd.DataFrame([total_row])], ignore_index=True)
    st.dataframe(display_df, width="stretch", hide_index=True)
