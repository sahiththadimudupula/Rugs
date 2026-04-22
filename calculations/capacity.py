from __future__ import annotations

import pandas as pd

from core.formatting import clean_text, to_number
from calculations.asking_rate import build_row_key

LOCATION_COLUMN = "location"
AVG_AREA_COLUMN = "avg_area_per_piece"
REFERENCE_PCS_COLUMN = "reference_pcs_per_day"
REFERENCE_MTR_COLUMN = "reference_mtr_per_day"
REFERENCE_LAC_COLUMN = "reference_lac_sqm_per_month"
ACTUAL_PCS_COLUMN = "actual_pcs_per_day"
ACTUAL_MTR_COLUMN = "actual_mtr_per_day"
ACTUAL_LAC_COLUMN = "actual_lac_sqm_per_month"

SQM_DIVISOR = 3.9
MONTH_DAYS = 30
LAC_DIVISOR = 100000


def prepare_capacity_table(source_table: pd.DataFrame) -> pd.DataFrame:
    table = source_table.iloc[:, :8].copy()
    table.columns = [
        LOCATION_COLUMN,
        AVG_AREA_COLUMN,
        REFERENCE_PCS_COLUMN,
        REFERENCE_MTR_COLUMN,
        REFERENCE_LAC_COLUMN,
        ACTUAL_PCS_COLUMN,
        ACTUAL_MTR_COLUMN,
        ACTUAL_LAC_COLUMN,
    ]
    table[LOCATION_COLUMN] = table[LOCATION_COLUMN].apply(lambda value: "Total" if clean_text(value) == "" else clean_text(value))
    for column_name in table.columns[1:]:
        table[column_name] = table[column_name].apply(to_number)
    return table


def build_asking_lookup(asking_rate_table: pd.DataFrame) -> dict[tuple[str, str, str, str], float]:
    lookup: dict[tuple[str, str, str, str], float] = {}
    for _, row in asking_rate_table.iterrows():
        lookup[
            build_row_key(row["Main_Group"], row["Sub_Group"], row["Category"], row["Subcategory"])
        ] = to_number(row["Asking_Rate_Per_Day"])
    return lookup


def calculate_mtr(pcs_per_day: float, avg_area_per_piece: float) -> float:
    return pcs_per_day * avg_area_per_piece / SQM_DIVISOR


def calculate_lac(pcs_per_day: float, avg_area_per_piece: float) -> float:
    return pcs_per_day * avg_area_per_piece * MONTH_DAYS / LAC_DIVISOR


def recalculate_capacity_table(source_table: pd.DataFrame, asking_rate_table: pd.DataFrame) -> pd.DataFrame:
    table = prepare_capacity_table(source_table)
    asking_lookup = build_asking_lookup(asking_rate_table)

    actual_values = {
        "Cotton-M/C Tufting": asking_lookup[build_row_key("Processing", "", "Process", "MT (PC/Day)")],
        "Cotton-Table Tufting": asking_lookup[build_row_key("Processing", "", "Process", "TT (PC/Day)")],
        "Chenille": asking_lookup[build_row_key("Packing", "", "Packing", "Chenile")],
        "Bath Rugs (Non- Wash with Tumble)": (
            asking_lookup[build_row_key("C&S", "Overedging", "Stitching Type", "Non dyeing")]
            + asking_lookup[build_row_key("C&S", "Overedging", "Stitching Type", "tumble")]
        ),
    }

    actual_values["Bath Rugs (Wash)"] = (
        asking_lookup[build_row_key("Packing", "", "Packing", "Grand Total")]
        - actual_values["Cotton-M/C Tufting"]
        - actual_values["Chenille"]
        - actual_values["Bath Rugs (Non- Wash with Tumble)"]
    )

    for row_index, row in table.iterrows():
        location_name = row[LOCATION_COLUMN]
        if location_name == "Total":
            continue
        avg_area = to_number(row[AVG_AREA_COLUMN])
        table.at[row_index, REFERENCE_MTR_COLUMN] = calculate_mtr(to_number(row[REFERENCE_PCS_COLUMN]), avg_area)
        table.at[row_index, REFERENCE_LAC_COLUMN] = calculate_lac(to_number(row[REFERENCE_PCS_COLUMN]), avg_area)

        pcs_value = actual_values.get(location_name, to_number(row[ACTUAL_PCS_COLUMN]))
        table.at[row_index, ACTUAL_PCS_COLUMN] = pcs_value
        table.at[row_index, ACTUAL_MTR_COLUMN] = calculate_mtr(pcs_value, avg_area)
        table.at[row_index, ACTUAL_LAC_COLUMN] = calculate_lac(pcs_value, avg_area)

    total_mask = table[LOCATION_COLUMN] == "Total"
    non_total_mask = ~total_mask
    table.loc[total_mask, REFERENCE_PCS_COLUMN] = table.loc[non_total_mask, REFERENCE_PCS_COLUMN].sum()
    table.loc[total_mask, REFERENCE_MTR_COLUMN] = table.loc[non_total_mask, REFERENCE_MTR_COLUMN].sum()
    table.loc[total_mask, REFERENCE_LAC_COLUMN] = table.loc[non_total_mask, REFERENCE_LAC_COLUMN].sum()
    table.loc[total_mask, ACTUAL_PCS_COLUMN] = table.loc[non_total_mask, ACTUAL_PCS_COLUMN].sum()
    table.loc[total_mask, ACTUAL_MTR_COLUMN] = table.loc[non_total_mask, ACTUAL_MTR_COLUMN].sum()
    table.loc[total_mask, ACTUAL_LAC_COLUMN] = table.loc[non_total_mask, ACTUAL_LAC_COLUMN].sum()
    return table.reset_index(drop=True)
