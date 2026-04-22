from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from config.constants import (
    COMPACT_SECTION_COLUMNS,
    EDITABLE_MASTER_COLUMNS,
    MASTER_COLUMNS,
    OPERATOR_TYPE_OPTIONS,
)
from core.formatting import format_display_number


def build_unique_key(prefix: str, section_name: str) -> str:
    normalized_prefix = re.sub(r"[^a-zA-Z0-9_]+", "_", prefix.strip().lower())
    normalized_section = re.sub(r"[^a-zA-Z0-9_]+", "_", section_name.strip().lower())
    return f"editor_{normalized_prefix}_{normalized_section}"



def render_cards(section_count: int, total_be_final: float) -> None:
    card_col1, card_col2 = st.columns(2)

    with card_col1:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-label">SECTION</div>
                <div class="metric-value">{format_display_number(section_count)}</div>
                <div class="metric-note">Number of visible sections</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with card_col2:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-label">SUM OF BE_FINAL_MANPOWER</div>
                <div class="metric-value">{format_display_number(total_be_final)}</div>
                <div class="metric-note">Current visible manpower total</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )



def render_table_cards(title_left: str, value_left: float | int, title_right: str, value_right: float | int) -> None:
    card_col1, card_col2 = st.columns(2)

    with card_col1:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-label">{title_left.upper()}</div>
                <div class="metric-value">{format_display_number(value_left)}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with card_col2:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-label">{title_right.upper()}</div>
                <div class="metric-value">{format_display_number(value_right)}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )



def build_summary_table(master_df: pd.DataFrame) -> pd.DataFrame:
    summary_df = (
        master_df.groupby("Section", as_index=False, sort=False)
        .agg(
            Machine_Count=("Machine_Count", "sum"),
            BE_Final_Manpower=("BE_Final_Manpower", "sum"),
        )
        .rename(columns={"BE_Final_Manpower": "sum(BE_Final_Manpower)"})
    )
    total_row = pd.DataFrame(
        {
            "Section": ["Total"],
            "Machine_Count": [summary_df["Machine_Count"].sum()],
            "sum(BE_Final_Manpower)": [summary_df["sum(BE_Final_Manpower)"].sum()],
        }
    )
    return pd.concat([summary_df, total_row], ignore_index=True)



def render_summary_table(master_df: pd.DataFrame) -> None:
    summary_df = build_summary_table(master_df)
    st.markdown("#### Section Summary")
    st.dataframe(summary_df, width="stretch", hide_index=True)



def render_compact_table(section_df: pd.DataFrame) -> None:
    compact_df = section_df[COMPACT_SECTION_COLUMNS].copy()
    st.dataframe(compact_df, width="stretch", hide_index=True)



def render_editable_section(section_name: str, master_df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    section_mask = master_df["Section"] == section_name
    section_df = master_df.loc[section_mask].copy()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{section_name}</div>', unsafe_allow_html=True)
    render_compact_table(section_df)

    with st.expander(f"Expand Section - {section_name}", expanded=False):
        editable_df = section_df[MASTER_COLUMNS].copy()
        editable_df["Operator_Type"] = editable_df["Operator_Type"].replace("", "Direct")
        disabled_columns = [column_name for column_name in MASTER_COLUMNS if column_name not in EDITABLE_MASTER_COLUMNS]
        edited_df = st.data_editor(
            editable_df,
            key=build_unique_key(key_prefix, section_name),
            width="stretch",
            num_rows="fixed",
            hide_index=True,
            disabled=disabled_columns,
            column_config={
                "Operator_Type": st.column_config.SelectboxColumn(
                    "Operator_Type",
                    options=OPERATOR_TYPE_OPTIONS,
                    required=False,
                ),
            },
        )
        for column_name in EDITABLE_MASTER_COLUMNS:
            master_df.loc[section_mask, column_name] = edited_df[column_name].values

    st.markdown("</div>", unsafe_allow_html=True)
    return master_df



def render_filtered_section_group(
    tab_name: str,
    sections: list[str],
    master_df: pd.DataFrame,
    show_summary: bool = True,
) -> pd.DataFrame:
    visible_df = master_df[master_df["Section"].isin(sections)].copy()

    if visible_df.empty:
        st.info("No rows available for this tab.")
        return master_df

    render_cards(
        section_count=visible_df["Section"].nunique(),
        total_be_final=visible_df["BE_Final_Manpower"].sum(),
    )

    if show_summary:
        render_summary_table(visible_df)

    for section_name in visible_df["Section"].drop_duplicates().tolist():
        master_df = render_editable_section(section_name, master_df, key_prefix=tab_name)

    return master_df



def render_filter_bar(master_df: pd.DataFrame, key_prefix: str) -> tuple[list[str], list[str]]:
    st.markdown("#### Filters")
    filter_col1, filter_col2 = st.columns(2)

    section_options = master_df["Section"].drop_duplicates().tolist()
    selected_sections = st.session_state.get(f"{key_prefix}_sections", [])

    designation_source_df = master_df
    if selected_sections:
        designation_source_df = master_df[master_df["Section"].isin(selected_sections)]
    designation_options = designation_source_df["Designation"].drop_duplicates().tolist()

    with filter_col1:
        selected_sections = st.multiselect(
            "Section",
            options=section_options,
            default=[],
            key=f"{key_prefix}_sections",
            placeholder="Choose options",
        )

    with filter_col2:
        selected_designations = st.multiselect(
            "Designation",
            options=designation_options,
            default=[],
            key=f"{key_prefix}_designations",
            placeholder="Choose options",
        )

    return selected_sections, selected_designations



def filter_master_df(master_df: pd.DataFrame, sections: list[str], designations: list[str]) -> pd.DataFrame:
    filtered_df = master_df.copy()

    if sections:
        filtered_df = filtered_df[filtered_df["Section"].isin(sections)]

    if designations:
        filtered_df = filtered_df[filtered_df["Designation"].isin(designations)]

    return filtered_df
