from __future__ import annotations
import pandas as pd
import streamlit as st
from config.constants import *
from config.settings import DOWNLOAD_FILE_NAME
from core.persistence import reset_working_file, save_snapshot, workbook_bytes
from engines.pipeline import recalc_all
from services.master_rows import apply_master_edit
from services.summaries import add_total_row, build_summary


def render_cards(summary: dict[str, float], final_label: str = "Final Manpower"):
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-label">Visible Sections</div><div class="kpi-value">{int(summary['visible_section_count'])}</div></div>
      <div class="kpi-card"><div class="kpi-label">{final_label}</div><div class="kpi-value">{summary['final_total']:,.2f}</div></div>
    </div>
    """, unsafe_allow_html=True)




def arrow_safe_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    safe_df = df.copy()
    for col in safe_df.columns:
        series = safe_df[col]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            non_null = series.dropna()
            if non_null.empty:
                continue
            type_names = {type(v).__name__ for v in non_null.tolist()}
            if len(type_names) > 1:
                safe_df[col] = series.map(lambda x: '' if pd.isna(x) else str(x))
    return safe_df

def render_bottom_actions(state: dict, key_prefix: str):
    st.markdown('<div class="bottom-actions-spacer"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button('Freeze Changes', key=f'{key_prefix}_freeze', width='stretch'):
            save_snapshot(state)
            st.success('Working file updated.')
    with c2:
        st.download_button('Download Full Excel', data=workbook_bytes(state), file_name=DOWNLOAD_FILE_NAME, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=f'{key_prefix}_download', width='stretch')
    with c3:
        if st.button('Reset from Input', key=f'{key_prefix}_reset', width='stretch'):
            reset_working_file()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def section_df(state: dict, sections: list[str]) -> pd.DataFrame:
    return state['master_df'][state['master_df']['Section'].isin(sections)].copy()


def apply_master_filters(df: pd.DataFrame, key_prefix: str, show_section_filter: bool = True) -> pd.DataFrame:
    if df.empty:
        return df
    col1, col2 = st.columns(2)
    filtered_df = df.copy()
    if show_section_filter:
        with col1:
            section_options = filtered_df['Section'].dropna().astype(str).unique().tolist()
            selected_sections = st.multiselect('Section', section_options, default=[], key=f'{key_prefix}_sections')
        if selected_sections:
            filtered_df = filtered_df[filtered_df['Section'].isin(selected_sections)].copy()
    with col2:
        designation_options = filtered_df['Designation'].dropna().astype(str).unique().tolist()
        selected_designations = st.multiselect('Designation', designation_options, default=[], key=f'{key_prefix}_designations')
    if selected_designations:
        filtered_df = filtered_df[filtered_df['Designation'].isin(selected_designations)].copy()
    return filtered_df


def sync_ppc_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state['snapshots']['ppc_df']
    changed = False
    for i, row in edited_df.iterrows():
        if row['row_type'] != 'input':
            continue
        if float(old_df.at[i, 'Asking_Rate_Per_Day']) != float(row['Asking_Rate_Per_Day']):
            state['ppc_df'].at[i, 'Asking_Rate_Per_Day'] = float(row['Asking_Rate_Per_Day'])
            changed = True
    if changed:
        recalc_all(state)
        state['snapshots']['ppc_df'] = state['ppc_df'].copy(deep=True)


def sync_coating_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state['snapshots']['coating_df']
    changed = False
    for i, row in edited_df.iterrows():
        if row['row_type'] != 'input':
            continue
        if float(old_df.at[i, 'Value']) != float(row['Value']):
            state['coating_df'].at[i, 'Value'] = float(row['Value'])
            changed = True
    if changed:
        recalc_all(state)
        state['snapshots']['coating_df'] = state['coating_df'].copy(deep=True)


def sync_hydro_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state['snapshots']['hydro_df'].drop(columns=['row_order'])
    changed = False
    editable = {'Efficiency', 'additional Req', 'M/s Capacity Proposed', 'No. Of Batch'}
    for col in editable:
        if float(old_df.at[0, col]) != float(edited_df.at[0, col]):
            state['hydro_df'].at[0, col] = float(edited_df.at[0, col])
            changed = True
    if changed:
        recalc_all(state)
        state['snapshots']['hydro_df'] = state['hydro_df'].copy(deep=True)


def sync_dye_input_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state['snapshots']['dye_inputs_df']
    changed = False
    for i, row in edited_df.iterrows():
        if float(old_df.at[i, 'Value']) != float(row['Value']):
            state['dye_inputs_df'].at[i, 'Value'] = float(row['Value'])
            state['dye_input_overrides'][row['key']] = True
            changed = True
    if changed:
        recalc_all(state)
        state['snapshots']['dye_inputs_df'] = state['dye_inputs_df'].copy(deep=True)


def sync_dye_ezm_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state['snapshots']['dye_ezm_df']
    changed = False
    for i in edited_df.index:
        for col in ['MACHINE', 'CAPACITY', 'COTTON', 'DRYLON']:
            if str(old_df.at[i, col]) != str(edited_df.at[i, col]):
                state['dye_ezm_df'].at[i, col] = edited_df.at[i, col]
                changed = True
    if changed:
        recalc_all(state)
        state['snapshots']['dye_ezm_df'] = state['dye_ezm_df'].copy(deep=True)


def sync_dye_jet_changes(state: dict, edited_df: pd.DataFrame):
    old_df = state['snapshots']['dye_jet_df']
    changed = False
    for i in edited_df.index:
        for col in edited_df.columns:
            if str(old_df.at[i, col]) != str(edited_df.at[i, col]):
                state['dye_jet_df'].at[i, col] = edited_df.at[i, col]
                changed = True
    if changed:
        recalc_all(state)
        state['snapshots']['dye_jet_df'] = state['dye_jet_df'].copy(deep=True)


def sync_master_edits(state: dict, original_df: pd.DataFrame, edited_df: pd.DataFrame):
    compare_cols = list(edited_df.columns)
    for row_id in edited_df.index.tolist():
        old_row = original_df[original_df['row_id'] == row_id].iloc[0]
        new_row = edited_df.loc[row_id]
        for col in compare_cols:
            if str(old_row[col]) != str(new_row[col]):
                apply_master_edit(state, row_id, col, new_row[col])


def render_master_editor(state: dict, df: pd.DataFrame, key: str):
    if df.empty:
        st.info('No rows found.')
        return
    display_df = df.drop(columns=['row_order']).set_index('row_id')
    edited_df = st.data_editor(
        display_df,
        key=key,
        width='stretch',
        height=min(800, 44 * (len(display_df) + 3)),
        hide_index=True,
        disabled=[c for c in display_df.columns if c not in EDITABLE_MASTER_COLUMNS],
        column_config={'Operator_Type': st.column_config.SelectboxColumn('Operator_Type', options=OPERATOR_TYPE_OPTIONS)},
    )
    sync_master_edits(state, df.copy(), edited_df)


def render_ppc_tab(state: dict):
    temp = state['ppc_df'][['Main_Group', 'Asking_Rate_Per_Day']].copy()
    temp['Section'] = temp['Main_Group']
    temp['BE_Final_Manpower'] = temp['Asking_Rate_Per_Day']
    temp['Machine_Count'] = temp['Asking_Rate_Per_Day']
    summary = {'visible_section_count': float(len(state['ppc_df'][state['ppc_df']['row_type']=='input'])), 'final_total': float(temp['BE_Final_Manpower'].sum())}
    render_cards(summary, final_label='Total Asking Rate')
    st.caption('Edit only base PPC rows. Calculated rows will refresh automatically.')
    edited_df = st.data_editor(state['ppc_df'], key='ppc_editor', width='stretch', height=620, hide_index=True, disabled=['Main_Group', 'Sub_Group', 'Category', 'Subcategory', 'row_type', 'row_order'])
    sync_ppc_changes(state, edited_df)
    st.dataframe(arrow_safe_df(add_total_row(state['ppc_df'].drop(columns=['row_order']))), width='stretch', hide_index=True)
    render_bottom_actions(state, 'ppc')


def render_generic_section_tab(state: dict, sections: list[str], tab_key: str):
    df = apply_master_filters(section_df(state, sections), tab_key, show_section_filter=True)
    render_cards(build_summary(df))
    if df.empty:
        st.info('No rows found.')
        render_bottom_actions(state, tab_key)
        return
    compact = df[['Section', 'Dept_Machine_Name', 'Designation', 'Machine_Count', 'BE_Final_Manpower']]
    st.dataframe(arrow_safe_df(add_total_row(compact)), width='stretch', hide_index=True)
    for section_name in df['Section'].drop_duplicates().tolist():
        part = df[df['Section'] == section_name].copy()
        with st.expander(section_name, expanded=False):
            render_master_editor(state, part, f'{tab_key}_{section_name}')
    render_bottom_actions(state, tab_key)


def render_coating_tab(state: dict):
    df = apply_master_filters(section_df(state, [COATING_SECTION]), 'coating', show_section_filter=False)
    render_cards(build_summary(df))
    st.subheader('Coating Helper')
    helper_edit = st.data_editor(state['coating_df'], key='coating_helper_editor', width='stretch', height=420, hide_index=True, disabled=['Parameter', 'Material', 'row_type', 'row_order'])
    sync_coating_changes(state, helper_edit)
    st.dataframe(arrow_safe_df(add_total_row(state['coating_df'].drop(columns=['row_order']))), width='stretch', hide_index=True)
    st.subheader('Coating Manpower')
    render_master_editor(state, df, 'coating_master_editor')
    st.dataframe(arrow_safe_df(add_total_row(df[['Section', 'Sr_No', 'Dept_Machine_Name', 'Designation', 'Machine_Count', 'BE_Scientific_Manpower', 'BE_Final_Manpower']])), width='stretch', hide_index=True)
    render_bottom_actions(state, 'coating')


def render_cut_and_sew_tab(state: dict):
    df = apply_master_filters(section_df(state, [CUT_AND_SEW_SECTION]), 'cutandsew', show_section_filter=False)
    render_cards(build_summary(df))
    st.subheader('Capacity')
    st.dataframe(arrow_safe_df(add_total_row(state['capacity_df'].drop(columns=['row_order']))), width='stretch', hide_index=True)
    st.subheader('CS')
    st.dataframe(arrow_safe_df(add_total_row(state['cs_df'].drop(columns=['row_order']))), width='stretch', hide_index=True)
    st.subheader('Cut & Sew Manpower')
    render_master_editor(state, df, 'cut_sew_master_editor')
    render_bottom_actions(state, 'cutsew')


def render_dyeing_tab(state: dict):
    dyeing_df = apply_master_filters(section_df(state, [DYEING_SECTION]), 'dyeing', show_section_filter=False)
    render_cards(build_summary(dyeing_df))
    st.subheader('Dyeing Driver Inputs')
    driver_edit = st.data_editor(state['dye_inputs_df'], key='dye_inputs_editor', width='stretch', hide_index=True, disabled=['Input', 'key', 'Source'])
    sync_dye_input_changes(state, driver_edit)
    st.dataframe(arrow_safe_df(add_total_row(state['dye_inputs_df'][['Input', 'Value']])), width='stretch', hide_index=True)
    st.subheader('EZM / Paddle Machine Master')
    ezm_edit = st.data_editor(state['dye_ezm_df'], key='dye_ezm_editor', width='stretch', hide_index=True)
    sync_dye_ezm_changes(state, ezm_edit)
    ezm_out = state.get('dye_outputs', {}).get('ezm_paddle', {})
    left, right = st.columns(2)
    with left:
        st.caption('Final Summary')
        st.dataframe(arrow_safe_df(add_total_row(ezm_out.get('final_summary_table', pd.DataFrame()))), width='stretch', hide_index=True)
    with right:
        st.caption('Production Summary')
        st.dataframe(arrow_safe_df(add_total_row(ezm_out.get('production_summary_table', pd.DataFrame()))), width='stretch', hide_index=True)
    left2, right2 = st.columns(2)
    with left2:
        st.caption('Drylon Selected Machines')
        st.dataframe(arrow_safe_df(add_total_row(ezm_out.get('drylon_selected_table', pd.DataFrame()))), width='stretch', hide_index=True)
    with right2:
        st.caption('Cotton Selected Machines')
        st.dataframe(arrow_safe_df(add_total_row(ezm_out.get('cotton_selected_table', pd.DataFrame()))), width='stretch', hide_index=True)
    st.subheader('Jet Dyeing Machine Table')
    jet_edit = st.data_editor(state['dye_jet_df'], key='dye_jet_editor', width='stretch', hide_index=True)
    sync_dye_jet_changes(state, jet_edit)
    jet_out = state.get('dye_outputs', {}).get('jet', {})
    left3, right3 = st.columns(2)
    with left3:
        st.caption('Option 1 - Closest With Minimum Machines')
        st.dataframe(arrow_safe_df(add_total_row(jet_out.get('option1_summary', pd.DataFrame()))), width='stretch', hide_index=True)
        st.dataframe(arrow_safe_df(add_total_row(jet_out.get('option1_table', pd.DataFrame()))), width='stretch', hide_index=True)
    with right3:
        st.caption('Option 2 - New Machine Preference')
        st.dataframe(arrow_safe_df(add_total_row(jet_out.get('option2_summary', pd.DataFrame()))), width='stretch', hide_index=True)
        st.dataframe(arrow_safe_df(add_total_row(jet_out.get('option2_table', pd.DataFrame()))), width='stretch', hide_index=True)
    st.subheader('Hydro Helper')
    helper_edit = st.data_editor(state['hydro_df'].drop(columns=['row_order']), key='hydro_editor', width='stretch', height=180, hide_index=True)
    sync_hydro_changes(state, helper_edit)
    st.dataframe(arrow_safe_df(add_total_row(state['hydro_df'].drop(columns=['row_order']))), width='stretch', hide_index=True)
    st.subheader('Dyeing Manpower')
    render_master_editor(state, dyeing_df, 'dyeing_master_editor')
    render_bottom_actions(state, 'dyeing')


def render_packintqm_tab(state: dict):
    df = apply_master_filters(section_df(state, PACKING_TQM_SECTIONS), 'packintqm', show_section_filter=True)
    render_cards(build_summary(df), final_label='Packin&TQM Final')
    st.subheader('Packin&TQM Helper Source Table')
    if state.get('packing_tqm_source_df') is not None:
        src = state['packing_tqm_source_df'].drop(columns=[c for c in ['row_order','row_id'] if c in state['packing_tqm_source_df'].columns], errors='ignore')
        st.dataframe(arrow_safe_df(add_total_row(src)), width='stretch', hide_index=True)
    st.subheader('Packin&TQM Draft Table')
    draft_df = state.get('packing_tqm_draft_calc_df')
    if draft_df is None or getattr(draft_df, 'empty', False) and state.get('packing_tqm_draft_source_df') is not None:
        draft_df = state.get('packing_tqm_draft_source_df')
    if draft_df is not None:
        st.dataframe(arrow_safe_df(add_total_row(draft_df.drop(columns=[c for c in ['row_order','row_id'] if c in draft_df.columns], errors='ignore'))), width='stretch', hide_index=True)
    st.subheader('Calculated Helper Table')
    if state.get('packing_tqm_helper_df') is not None:
        st.dataframe(arrow_safe_df(add_total_row(state['packing_tqm_helper_df'].drop(columns=[c for c in ['row_order','row_id'] if c in state['packing_tqm_helper_df'].columns], errors='ignore'))), width='stretch', hide_index=True)
    st.subheader('Linked Packin&TQM Manpower')
    render_master_editor(state, df, 'packintqm_master_editor')
    render_bottom_actions(state, 'packintqm')


def render_final_master_tab(state: dict):
    df = apply_master_filters(state['master_df'].copy(), 'finalmaster', show_section_filter=True)
    render_cards(build_summary(df))
    render_master_editor(state, df.copy(), 'final_master_editor')
    st.dataframe(arrow_safe_df(add_total_row(df.drop(columns=['row_order', 'row_id']))), width='stretch', hide_index=True)
    render_bottom_actions(state, 'finalmaster')
