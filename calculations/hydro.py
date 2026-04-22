from __future__ import annotations

import pandas as pd

from core.formatting import to_number, round_half_up, safe_divide
from calculations.capacity import LOCATION_COLUMN, ACTUAL_PCS_COLUMN

PIECES_CONVERSION_FACTOR = 0.98
PERCENT_DIVISOR = 100.0


def prepare_hydro_table(source_table: pd.DataFrame) -> pd.DataFrame:
    table = source_table.copy()
    for column_name in table.columns:
        table[column_name] = table[column_name].apply(to_number)
    return table.iloc[[0]].reset_index(drop=True)


def get_capacity_pcs(capacity_table: pd.DataFrame, location_name: str) -> float:
    row = capacity_table[capacity_table[LOCATION_COLUMN] == location_name]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0][ACTUAL_PCS_COLUMN])


def recalculate_hydro_table(source_table: pd.DataFrame, capacity_table: pd.DataFrame, edited_table: pd.DataFrame | None = None) -> pd.DataFrame:
    table = prepare_hydro_table(edited_table if edited_table is not None else source_table)

    required_pcs = (
        get_capacity_pcs(capacity_table, "Cotton-M/C Tufting")
        + get_capacity_pcs(capacity_table, "Cotton-Table Tufting")
        + get_capacity_pcs(capacity_table, "Bath Rugs (Wash)")
    )
    efficiency = to_number(table.at[0, "Efficiency"])
    machine_capacity = to_number(table.at[0, "M/s Capacity Proposed"])
    batch_count = to_number(table.at[0, "No. Of Batch"])

    prod_per_mc = batch_count * machine_capacity * (efficiency / PERCENT_DIVISOR)
    pcs_per_day_per_mc = prod_per_mc * PIECES_CONVERSION_FACTOR
    total_mc_required = round_half_up(safe_divide(required_pcs, prod_per_mc), 0)

    table.at[0, "Required Pcs"] = required_pcs
    table.at[0, "Prod/mc/day (Kgs)"] = prod_per_mc
    table.at[0, "Pcs/day/mc"] = pcs_per_day_per_mc
    table.at[0, "Total M/c Req"] = total_mc_required
    return table
