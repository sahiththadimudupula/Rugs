from __future__ import annotations

import pandas as pd

from core.formatting import clean_text, to_number, safe_divide
from calculations.capacity import LOCATION_COLUMN, ACTUAL_PCS_COLUMN, ACTUAL_MTR_COLUMN, ACTUAL_LAC_COLUMN

DAYS_PER_MONTH_STANDARD = 25
DAYS_PER_MONTH_SQM = 30

DRYLON_UNION_FACTOR = 0.85
DRYLON_MAT_FACTOR = 0.5
TOTAL_PCS_MAT_CONSTANT = 28030.0
DRYLON_WASHING_SHAPE_DESIGN_CONSTANT = 1000.0
DRYLON_NON_WASHING_SHAPE_DESIGN_CONSTANT = 7500.0


def prepare_cs_table(source_table: pd.DataFrame) -> pd.DataFrame:
    table = source_table.copy()
    table["Section"] = table["Section"].apply(clean_text)
    table["Process"] = table["Process"].apply(clean_text)
    table["Metric"] = table["Metric"].apply(clean_text)
    table["Value"] = table["Value"].apply(to_number)
    return table


def get_capacity_value(capacity_table: pd.DataFrame, location_name: str, column_name: str) -> float:
    row = capacity_table[capacity_table[LOCATION_COLUMN] == location_name]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0][column_name])


def get_value(table: pd.DataFrame, section: str, process: str, metric: str) -> float:
    mask = (
        (table["Section"] == section)
        & (table["Process"] == process)
        & (table["Metric"] == metric)
    )
    row = table[mask]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0]["Value"])


def set_value(table: pd.DataFrame, section: str, process: str, metric: str, value: float) -> None:
    mask = (
        (table["Section"] == section)
        & (table["Process"] == process)
        & (table["Metric"] == metric)
    )
    if mask.any():
        table.loc[mask, "Value"] = float(value)


def recalculate_cs_table(source_table: pd.DataFrame, capacity_table: pd.DataFrame) -> pd.DataFrame:
    table = prepare_cs_table(source_table)

    cotton_tt_pcs_day = get_capacity_value(capacity_table, "Cotton-Table Tufting", ACTUAL_PCS_COLUMN)
    set_value(table, "Production", "Cotton Dyeing (TT)", "Pcs/Day", cotton_tt_pcs_day)
    set_value(table, "Production", "Cotton Dyeing (TT)", "Pcs/Month", cotton_tt_pcs_day * DAYS_PER_MONTH_STANDARD)

    cotton_mt_pcs_day = get_capacity_value(capacity_table, "Cotton-M/C Tufting", ACTUAL_PCS_COLUMN)
    cotton_mt_linear_mtr = get_capacity_value(capacity_table, "Cotton-M/C Tufting", ACTUAL_MTR_COLUMN)
    set_value(table, "Production", "Cotton Dyeing (MT)", "Pcs/Day", cotton_mt_pcs_day)
    set_value(table, "Production", "Cotton Dyeing (MT)", "Pcs/Month", cotton_mt_pcs_day * DAYS_PER_MONTH_STANDARD)
    set_value(table, "Production", "Cotton Dyeing (MT)", "Linear Mtr", cotton_mt_linear_mtr)
    set_value(table, "Production", "Cotton Dyeing (MT)", "Union", cotton_mt_pcs_day)
    set_value(table, "Production", "Cotton Dyeing (MT)", "Mat", cotton_mt_pcs_day)

    drylon_wash_pcs_day = get_capacity_value(capacity_table, "Bath Rugs (Wash)", ACTUAL_PCS_COLUMN)
    drylon_wash_linear_mtr = get_capacity_value(capacity_table, "Bath Rugs (Wash)", ACTUAL_MTR_COLUMN)
    drylon_union = drylon_wash_pcs_day * DRYLON_UNION_FACTOR
    drylon_over_edging = drylon_wash_pcs_day - drylon_union
    drylon_mat = drylon_wash_pcs_day * DRYLON_MAT_FACTOR

    set_value(table, "Production", "Drylon (Washing)", "Pcs/Day", drylon_wash_pcs_day)
    set_value(table, "Production", "Drylon (Washing)", "Pcs/Month", drylon_wash_pcs_day * DAYS_PER_MONTH_STANDARD)
    set_value(table, "Production", "Drylon (Washing)", "Linear Mtr", drylon_wash_linear_mtr)
    set_value(table, "Production", "Drylon (Washing)", "Union", drylon_union)
    set_value(table, "Production", "Drylon (Washing)", "Over Edging", drylon_over_edging)
    set_value(table, "Production", "Drylon (Washing)", "Mat", drylon_mat)
    set_value(table, "Production", "Drylon (Washing)", "Shape/Design", DRYLON_WASHING_SHAPE_DESIGN_CONSTANT)

    drylon_non_pcs_day = get_capacity_value(capacity_table, "Bath Rugs (Non- Wash with Tumble)", ACTUAL_PCS_COLUMN)
    drylon_non_linear_mtr = get_capacity_value(capacity_table, "Bath Rugs (Non- Wash with Tumble)", ACTUAL_MTR_COLUMN)
    set_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Pcs/Day", drylon_non_pcs_day)
    set_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Pcs/Month", drylon_non_pcs_day * DAYS_PER_MONTH_STANDARD)
    set_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Linear Mtr", drylon_non_linear_mtr)
    set_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Over Edging", drylon_non_pcs_day)
    set_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Shape/Design", DRYLON_NON_WASHING_SHAPE_DESIGN_CONSTANT)
    set_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Mat", drylon_non_pcs_day - DRYLON_NON_WASHING_SHAPE_DESIGN_CONSTANT)

    chenille_pcs_day = get_capacity_value(capacity_table, "Chenille", ACTUAL_PCS_COLUMN)
    set_value(table, "Production", "Chenille", "Pcs/Day", chenille_pcs_day)
    set_value(table, "Production", "Chenille", "Pcs/Month", chenille_pcs_day * DAYS_PER_MONTH_STANDARD)
    set_value(table, "Production", "Chenille", "Union", chenille_pcs_day)

    carpet_rolling_pcs_day = get_value(table, "Production", "Carpet_Rolling", "Pcs/Day")
    set_value(table, "Production", "Carpet_Rolling", "Pcs/Month", carpet_rolling_pcs_day * DAYS_PER_MONTH_STANDARD)

    total_pcs_day = (
        get_value(table, "Production", "Cotton Dyeing (TT)", "Pcs/Day")
        + get_value(table, "Production", "Cotton Dyeing (MT)", "Pcs/Day")
        + get_value(table, "Production", "Drylon (Washing)", "Pcs/Day")
        + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Pcs/Day")
        + get_value(table, "Production", "Carpet_Rolling", "Pcs/Day")
        + get_value(table, "Production", "Chenille", "Pcs/Day")
    )
    total_pcs_month = (
        get_value(table, "Production", "Cotton Dyeing (TT)", "Pcs/Month")
        + get_value(table, "Production", "Cotton Dyeing (MT)", "Pcs/Month")
        + get_value(table, "Production", "Drylon (Washing)", "Pcs/Month")
        + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Pcs/Month")
        + get_value(table, "Production", "Carpet_Rolling", "Pcs/Month")
        + get_value(table, "Production", "Chenille", "Pcs/Month")
    )
    total_linear_mtr = (
        get_value(table, "Production", "Cotton Dyeing (TT)", "Linear Mtr")
        + get_value(table, "Production", "Cotton Dyeing (MT)", "Linear Mtr")
        + get_value(table, "Production", "Drylon (Washing)", "Linear Mtr")
        + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Linear Mtr")
        + get_value(table, "Production", "Carpet_Rolling", "Linear Mtr")
        + get_value(table, "Production", "Chenille", "Linear Mtr")
    )
    total_union = (
        get_value(table, "Production", "Cotton Dyeing (TT)", "Union")
        + get_value(table, "Production", "Cotton Dyeing (MT)", "Union")
        + get_value(table, "Production", "Drylon (Washing)", "Union")
        + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Union")
        + get_value(table, "Production", "Carpet_Rolling", "Union")
        + get_value(table, "Production", "Chenille", "Union")
    )
    total_over_edging = (
        get_value(table, "Production", "Cotton Dyeing (TT)", "Over Edging")
        + get_value(table, "Production", "Cotton Dyeing (MT)", "Over Edging")
        + get_value(table, "Production", "Drylon (Washing)", "Over Edging")
        + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Over Edging")
        + get_value(table, "Production", "Carpet_Rolling", "Over Edging")
        + get_value(table, "Production", "Chenille", "Over Edging")
    )
    total_shape_design = (
        get_value(table, "Production", "Cotton Dyeing (TT)", "Shape/Design")
        + get_value(table, "Production", "Cotton Dyeing (MT)", "Shape/Design")
        + get_value(table, "Production", "Drylon (Washing)", "Shape/Design")
        + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Shape/Design")
        + get_value(table, "Production", "Carpet_Rolling", "Shape/Design")
        + get_value(table, "Production", "Chenille", "Shape/Design")
    )

    set_value(table, "Production", "Total Pcs", "Pcs/Day", total_pcs_day)
    set_value(table, "Production", "Total Pcs", "Pcs/Month", total_pcs_month)
    set_value(table, "Production", "Total Pcs", "Linear Mtr", total_linear_mtr)
    set_value(table, "Production", "Total Pcs", "Union", total_union)
    set_value(table, "Production", "Total Pcs", "Over Edging", total_over_edging)
    set_value(table, "Production", "Total Pcs", "Mat", TOTAL_PCS_MAT_CONSTANT)
    set_value(table, "Production", "Total Pcs", "Shape/Design", total_shape_design)

    total_in_sqmtr = get_capacity_value(capacity_table, "Total", ACTUAL_LAC_COLUMN)
    set_value(table, "Production", "Total In SqMtr", "Pcs/Day", total_in_sqmtr)
    set_value(table, "Production", "Total In SqMtr", "Pcs/Month", total_in_sqmtr * DAYS_PER_MONTH_SQM)
    set_value(
        table,
        "Production",
        "Total In SqMtr",
        "Shape/Design",
        total_pcs_day - chenille_pcs_day - total_shape_design - TOTAL_PCS_MAT_CONSTANT,
    )

    def set_machine(process: str, metric: str, value: float) -> None:
        set_value(table, "Machine", process, metric, value)

    length_cutting_capacity = 13 * 60 * 24 * 0.8 * 0.65
    length_cutting_req = get_value(table, "Production", "Total In SqMtr", "Shape/Design")
    set_machine("Length Cutting M/C", "Existing Capacity/MC", length_cutting_capacity)
    set_machine("Length Cutting M/C", "Requirements/day", length_cutting_req)
    length_total = safe_divide(length_cutting_req, length_cutting_capacity)
    set_machine("Length Cutting M/C", "Total M/C Reqd", length_total)
    set_machine("Length Cutting M/C", "New M/C Reqd", length_total - get_value(table, "Machine", "Length Cutting M/C", "Existing MCs available"))

    cross_cutting_capacity = 10 * 60 * 24 * 0.8
    cross_req = TOTAL_PCS_MAT_CONSTANT
    set_machine("Cross cutting M/C", "Existing Capacity/MC", cross_cutting_capacity)
    set_machine("Cross cutting M/C", "Requirements/day", cross_req)
    cross_total = safe_divide(cross_req, cross_cutting_capacity)
    set_machine("Cross cutting M/C", "Total M/C Reqd", cross_total)
    set_machine("Cross cutting M/C", "New M/C Reqd", cross_total - get_value(table, "Machine", "Cross cutting M/C", "Existing MCs available"))

    printed_req = get_value(table, "Production", "Total In SqMtr", "Shape/Design")
    printed_cap = get_value(table, "Machine", "Printed / Manual cutting", "Existing Capacity/MC")
    set_machine("Printed / Manual cutting", "Requirements/day", printed_req)
    set_machine("Printed / Manual cutting", "Total M/C Reqd", safe_divide(printed_req, printed_cap))

    shape_req = total_shape_design
    shape_cap = get_value(table, "Machine", "Shape cutting M/C", "Existing Capacity/MC")
    shape_total = safe_divide(shape_req, shape_cap)
    set_machine("Shape cutting M/C", "Requirements/day", shape_req)
    set_machine("Shape cutting M/C", "Total M/C Reqd", shape_total)
    set_machine("Shape cutting M/C", "New M/C Reqd", shape_total - get_value(table, "Machine", "Shape cutting M/C", "Existing MCs available"))

    length_rugs_cap = 7 * 60 * 24 * 0.82
    length_rugs_req = get_value(table, "Production", "Drylon (Washing)", "Over Edging") + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Over Edging")
    length_rugs_total = safe_divide(length_rugs_req, length_rugs_cap)
    set_machine("Length Over edging(Rugs)", "Existing Capacity/MC", length_rugs_cap)
    set_machine("Length Over edging(Rugs)", "Requirements/day", length_rugs_req)
    set_machine("Length Over edging(Rugs)", "Total M/C Reqd", length_rugs_total)
    set_machine("Length Over edging(Rugs)", "New M/C Reqd", length_rugs_total - get_value(table, "Machine", "Length Over edging(Rugs)", "Existing MCs available"))

    length_carpet_cap = 6 * 60 * 24 * 0.82 / 1.7
    length_carpet_req = carpet_rolling_pcs_day * 0
    set_machine("Length Over edging(carpet)", "Existing Capacity/MC", length_carpet_cap)
    set_machine("Length Over edging(carpet)", "Requirements/day", length_carpet_req)
    set_machine("Length Over edging(carpet)", "Total M/C Reqd", safe_divide(length_carpet_req, length_carpet_cap))

    tape_req = total_union
    tape_cap = get_value(table, "Machine", "Tape Binding", "Existing Capacity/MC")
    tape_total = safe_divide(tape_req, tape_cap)
    set_machine("Tape Binding", "Requirements/day", tape_req)
    set_machine("Tape Binding", "Total M/C Reqd", tape_total)
    set_machine("Tape Binding", "New M/C Reqd", tape_total - get_value(table, "Machine", "Tape Binding", "Existing MCs available"))

    over_req = get_value(table, "Production", "Drylon (Washing)", "Over Edging") + get_value(table, "Production", "Drylon_Rugs (Non_Washing)", "Over Edging")
    over_cap = get_value(table, "Machine", "Over edging for Rugs", "Existing Capacity/MC")
    over_total = safe_divide(over_req, over_cap)
    set_machine("Over edging for Rugs", "Requirements/day", over_req)
    set_machine("Over edging for Rugs", "Total M/C Reqd", over_total)
    set_machine("Over edging for Rugs", "New M/C Reqd", over_total - get_value(table, "Machine", "Over edging for Rugs", "Existing MCs available"))

    bartack_req = total_union + total_over_edging
    bartack_cap = get_value(table, "Machine", "Bartack", "Existing Capacity/MC")
    bartack_total = safe_divide(bartack_req, bartack_cap)
    set_machine("Bartack", "Requirements/day", bartack_req)
    set_machine("Bartack", "Total M/C Reqd", bartack_total)
    set_machine("Bartack", "New M/C Reqd", bartack_total - get_value(table, "Machine", "Bartack", "Existing MCs available"))

    set_machine("Table Tufting (3/16)", "Total M/C Reqd", tape_total * 3 / 2)
    set_machine("Table Tufting (Reversable)", "Total M/C Reqd", over_total * 3 / 2)

    cross_over_cap = 5 * 60 * 24 * 0.82
    cross_over_req = get_value(table, "Production", "Carpet_Rolling", "Over Edging")
    set_machine("Cross Over edging (carpet)", "Existing Capacity/MC", cross_over_cap)
    set_machine("Cross Over edging (carpet)", "Requirements/day", cross_over_req)
    set_machine("Cross Over edging (carpet)", "Total M/C Reqd", safe_divide(cross_over_req, cross_over_cap))

    return table.reset_index(drop=True)
