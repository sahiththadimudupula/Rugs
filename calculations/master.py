from __future__ import annotations

import pandas as pd

from core.formatting import clean_text, to_number, round_half_up
from config.constants import MASTER_COLUMNS, PACKING_TQM_SECTIONS

SECTION_ALIASES = {
    "Support MP": ["Support MP", "Packing Support MP"],
    "Other Support": ["Other Support", "TQM Other Support"],
}


def get_section_candidates(section_name: str) -> list[str]:
    return SECTION_ALIASES.get(section_name, [section_name])


def prepare_master_table(source_table: pd.DataFrame) -> pd.DataFrame:
    table = source_table.copy()
    for column_name in MASTER_COLUMNS:
        if column_name not in table.columns:
            table[column_name] = ""
    for text_column in ["Location", "Business", "Section", "Dept_Machine_Name", "Designation", "Workload", "Formulas", "Operator_Type", "Remarks"]:
        table[text_column] = table[text_column].apply(clean_text)
    for numeric_column in [
        "Sr_No", "Machine_Count", "BE_Scientific_Manpower", "Contractors", "Company_Associate",
        "BE_Final_Manpower", "N_shift", "General_Shift", "Shift_A", "Shift_B", "Shift_C", "Reliever"
    ]:
        table[numeric_column] = table[numeric_column].apply(to_number)
    table["_business_order"] = range(len(table))
    table["_scientific_ratio"] = table.apply(
        lambda row: 0.0 if to_number(row["Machine_Count"]) == 0 else to_number(row["BE_Scientific_Manpower"]) / to_number(row["Machine_Count"]),
        axis=1,
    )
    return table


def clone_master_with_user_edits(base_master: pd.DataFrame, live_master: pd.DataFrame | None) -> pd.DataFrame:
    if live_master is None:
        return base_master.copy()
    updated = base_master.copy()
    editable_columns = [
        "Operator_Type", "Contractors", "Company_Associate", "BE_Final_Manpower",
        "General_Shift", "Shift_A", "Shift_B", "Shift_C", "Reliever", "Remarks"
    ]
    for column_name in editable_columns:
        if column_name in live_master.columns:
            updated[column_name] = live_master[column_name].values
    return updated


def build_row_mask(master_table: pd.DataFrame, section: str, dept_machine_name: str, designation: str) -> pd.Series:
    return (
        master_table["Section"].isin(get_section_candidates(section))
        & (master_table["Dept_Machine_Name"] == dept_machine_name)
        & (master_table["Designation"] == designation)
    )


def apply_linked_machine_count(master_table: pd.DataFrame, section: str, dept_machine_name: str, designation: str, machine_count: float) -> None:
    mask = build_row_mask(master_table, section, dept_machine_name, designation)
    if not mask.any():
        return
    row_index = master_table[mask].index[0]
    master_table.at[row_index, "Machine_Count"] = machine_count
    ratio = to_number(master_table.at[row_index, "_scientific_ratio"])
    master_table.at[row_index, "BE_Scientific_Manpower"] = machine_count * ratio


def distribute_shifts(final_value: float, n_shift: float, general_shift: float) -> tuple[float, float, float, float]:
    if n_shift <= 1:
        return general_shift, 0.0, 0.0, 0.0
    remaining = max(final_value - general_shift, 0.0)
    shift_a = int(remaining // 3)
    shift_b = int(remaining // 3)
    shift_c = round_half_up(remaining - shift_a - shift_b, 0)
    return general_shift, shift_a, shift_b, shift_c


def sync_final_from_scientific(master_table: pd.DataFrame, sections_to_sync: list[str]) -> None:
    section_candidates: set[str] = set()
    for section_name in sections_to_sync:
        section_candidates.update(get_section_candidates(section_name))
    mask = master_table["Section"].isin(section_candidates)
    for row_index in master_table[mask].index:
        scientific = to_number(master_table.at[row_index, "BE_Scientific_Manpower"])
        final_value = round_half_up(scientific, 0)
        master_table.at[row_index, "BE_Final_Manpower"] = final_value
        general_shift = to_number(master_table.at[row_index, "General_Shift"])
        n_shift = to_number(master_table.at[row_index, "N_shift"])
        if general_shift == 0:
            general_shift, shift_a, shift_b, shift_c = distribute_shifts(final_value, n_shift, general_shift)
            master_table.at[row_index, "General_Shift"] = general_shift
            master_table.at[row_index, "Shift_A"] = shift_a
            master_table.at[row_index, "Shift_B"] = shift_b
            master_table.at[row_index, "Shift_C"] = shift_c


def update_packing_tqm_rows(master_table: pd.DataFrame, helper_table: pd.DataFrame) -> None:
    smart_lines = float(helper_table.loc[helper_table["Line"] == "Smart Line", "Reqd. Lines"].iloc[0])
    ina_lines = float(helper_table.loc[helper_table["Line"] == "INA", "Reqd. Lines"].iloc[0])
    chenille_lines = float(helper_table.loc[helper_table["Line"] == "Manual (Chenille)", "Reqd. Lines"].iloc[0])
    cotton_lines = float(helper_table.loc[helper_table["Line"] == "Manual (Cotton)", "Reqd. Lines"].iloc[0])

    mapping = {
        ("Production Line MP", "Smart Line"): smart_lines,
        ("Production Line MP", "INA"): ina_lines,
        ("Production Line MP", "Manual (Chenille)"): chenille_lines,
        ("Production Line MP", "Manual (Cotton)"): cotton_lines,
    }
    for (section, dept_machine_name), machine_count in mapping.items():
        mask = master_table["Section"].isin(get_section_candidates(section)) & (master_table["Dept_Machine_Name"] == dept_machine_name)
        master_table.loc[mask, "Machine_Count"] = machine_count
        master_table.loc[mask, "BE_Scientific_Manpower"] = master_table.loc[mask, "_scientific_ratio"] * machine_count
        master_table.loc[mask, "BE_Final_Manpower"] = master_table.loc[mask, "BE_Scientific_Manpower"].apply(lambda value: round_half_up(value, 0))

    total_lines = smart_lines + ina_lines + chenille_lines + cotton_lines
    chenille_req_day = float(helper_table.loc[helper_table["Line"] == "Manual (Chenille)", "Req/Day"].iloc[0])
    drylon_tqm = float(helper_table.loc[helper_table["Line"] == "Smart Line", "TQM"].iloc[0])
    chenille_tqm = float(helper_table.loc[helper_table["Line"] == "Manual (Chenille)", "TQM"].iloc[0])
    cotton_tqm = float(helper_table.loc[helper_table["Line"] == "Manual (Cotton)", "TQM"].iloc[0])

    custom_scientific = {
        ("Support MP", "Packing Support", "IMS"): total_lines * 3,
        ("Support MP", "Packing Support", "Line Jobber"): total_lines * 3,
        ("Support MP", "Packing Support", "Rework (Stain/Coating)"): round_half_up(total_lines / 2, 0) * 3,
        ("Support MP", "Packing Support", "Mender"): round_half_up(total_lines / 2, 0) * 3,
        ("Support MP", "Packing Support", "Carton Pkg"): total_lines * 9,
        ("Support MP", "Packing Support", "Carton Pkg jobber"): round_half_up(total_lines / 2, 0) * 3,
        ("Support MP", "Packing Support", "Chenille Preparation (Only Sewing Line)"): chenille_req_day / 600,
        ("TQM", "Drylon TQM", "TQM Per Day"): round_half_up(drylon_tqm * (smart_lines + ina_lines), 0) * 3,
        ("TQM", "Chenille TQM", "TQM Per Day"): round_half_up(chenille_tqm * chenille_lines, 0) * 3,
        ("TQM", "Cotton TQM", "TQM Per Day"): round_half_up(cotton_tqm * cotton_lines, 0) * 3,
    }

    for (section, dept_machine_name, designation), scientific_value in custom_scientific.items():
        mask = build_row_mask(master_table, section, dept_machine_name, designation)
        if mask.any():
            master_table.loc[mask, "BE_Scientific_Manpower"] = scientific_value
            master_table.loc[mask, "BE_Final_Manpower"] = round_half_up(scientific_value, 0)


def recalculate_master_table(
    master_source_table: pd.DataFrame,
    live_master_table: pd.DataFrame | None,
    coating_table: pd.DataFrame,
    cs_table: pd.DataFrame,
    hydro_table: pd.DataFrame,
    dyeing_result: dict[str, object],
    packing_tqm_helper: pd.DataFrame,
) -> pd.DataFrame:
    master_table = prepare_master_table(master_source_table)
    master_table = clone_master_with_user_edits(master_table, live_master_table)

    coating_total = float(coating_table[(coating_table["Parameter"] == "Machines Required") & (coating_table["Material"] == "Total")]["Value"].iloc[0])
    coating_drylon = float(coating_table[(coating_table["Parameter"] == "Machines Required") & (coating_table["Material"] == "Drylon")]["Value"].iloc[0])
    apply_linked_machine_count(master_table, "Coating", "Latex Coating", "OPERATOR (MONORAIL-ROLL RECEIVING, ROLL STORAGE & SHIFTING)", coating_total)
    apply_linked_machine_count(master_table, "Coating", "Latex Coating", "OPERATOR (RE-ROLLING)", 0.0)
    for row in [
        ("Coating", "Latex Coating", "OPERATOR (STITCHING  & Feeding)"),
        ("Coating", "Latex Coating", "OPERATOR (PRE-COAT APPLICATION HEAD)"),
        ("Coating", "Latex Coating", "OPERATOR (MAIN COAT APPLICATION HEAD)"),
        ("Coating", "Latex Coating", "OPERATOR (LATEX KITCHEN)"),
    ]:
        apply_linked_machine_count(master_table, *row, machine_count=coating_drylon)

    def cs_value(process: str, metric: str) -> float:
        row = cs_table[(cs_table["Section"] == "Machine") & (cs_table["Process"] == process) & (cs_table["Metric"] == metric)]
        if row.empty:
            return 0.0
        return to_number(row.iloc[0]["Value"])

    apply_linked_machine_count(master_table, "Cut & Sew", "Length Cutting", "Operator", round(cs_value("Length Cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Length Cutting", "Operator (Roll Feeder / Roll to Roll stitching)", round(cs_value("Length Cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Length Cutting", "Material Handler", round(cs_value("Length Cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Length Over edging", "Operator", round(cs_value("Cross cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Automaic Shape Cutting m/c", "Cutter Operator", round(cs_value("Shape cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Automaic Shape Cutting m/c", "Spreader Operator /layering", round(cs_value("Shape cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Automaic Shape Cutting m/c", "Material Handler", round(cs_value("Shape cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Cross Cutting", "Operator", round(cs_value("Cross cutting M/C", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Manual Cutting", "(750 Pcs Per Person output considered)", round(cs_value("Printed / Manual cutting", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Stitching m/c", "Union - Stitcher + Tape Binding", round(cs_value("Tape Binding", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Stitching m/c", "Bartack  - Stitcher (Tape Binding + Over Edgimg)", round(cs_value("Bartack", "Total M/C Reqd")))
    apply_linked_machine_count(master_table, "Cut & Sew", "Stitching m/c", "Titan - Stitcher", round(cs_value("Over edging for Rugs", "Total M/C Reqd")))

    apply_linked_machine_count(master_table, "Dyeing", "Paddle", "Operator", float(dyeing_result["paddle_count"]))
    apply_linked_machine_count(master_table, "Dyeing", "EZM", "Operator", float(dyeing_result["ezm_count"]))
    apply_linked_machine_count(master_table, "Dyeing", "Jet Dyeing", "Operator", float(dyeing_result["jet_count"]))
    apply_linked_machine_count(master_table, "Dyeing", "Hydro", "Operator", to_number(hydro_table.at[0, "Total M/c Req"]))

    update_packing_tqm_rows(master_table, packing_tqm_helper)

    linked_sections = ["Coating", "Cut & Sew", "Dyeing"] + PACKING_TQM_SECTIONS
    sync_final_from_scientific(master_table, linked_sections)

    master_table["Section"] = pd.Categorical(
        master_table["Section"],
        categories=list(dict.fromkeys(master_table["Section"].tolist())),
        ordered=True,
    )
    master_table = master_table.sort_values("_business_order").reset_index(drop=True)
    return master_table
