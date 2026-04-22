from __future__ import annotations

import pandas as pd

from core.formatting import to_number, round_half_up
from calculations.capacity import LOCATION_COLUMN, ACTUAL_MTR_COLUMN

MACHINE_CAPACITY_MULTIPLIER = 1400.0
DRYLON_BUFFER = 1.05


def prepare_coating_table(source_table: pd.DataFrame) -> pd.DataFrame:
    table = source_table.copy()
    table["Parameter"] = table["Parameter"].astype(str).str.strip()
    table["Material"] = table["Material"].astype(str).str.strip()
    table["Value"] = table["Value"].apply(to_number)
    return table


def get_capacity_mtr(capacity_table: pd.DataFrame, location_name: str) -> float:
    row = capacity_table[capacity_table[LOCATION_COLUMN] == location_name]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0][ACTUAL_MTR_COLUMN])


def get_value(table: pd.DataFrame, parameter: str, material: str) -> float:
    row = table[(table["Parameter"] == parameter) & (table["Material"] == material)]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0]["Value"])


def set_value(table: pd.DataFrame, parameter: str, material: str, value: float) -> None:
    mask = (table["Parameter"] == parameter) & (table["Material"] == material)
    if mask.any():
        table.loc[mask, "Value"] = float(value)


def recalculate_coating_table(source_table: pd.DataFrame, capacity_table: pd.DataFrame, edited_table: pd.DataFrame | None = None) -> pd.DataFrame:
    table = prepare_coating_table(edited_table if edited_table is not None else source_table)

    speed_cotton = get_value(table, "Speed", "Cotton")
    speed_drylon = get_value(table, "Speed", "Drylon")
    eff_cotton = get_value(table, "Efficiency", "Cotton")
    eff_drylon = get_value(table, "Efficiency", "Drylon")
    util_cotton = get_value(table, "Utilisation", "Cotton")
    util_drylon = get_value(table, "Utilisation", "Drylon")

    effective_cotton = speed_cotton * MACHINE_CAPACITY_MULTIPLIER * eff_cotton * util_cotton
    effective_drylon = speed_drylon * MACHINE_CAPACITY_MULTIPLIER * eff_drylon * util_drylon

    required_cotton = 0.0
    required_drylon = (
        get_capacity_mtr(capacity_table, "Bath Rugs (Wash)")
        + get_capacity_mtr(capacity_table, "Bath Rugs (Non- Wash with Tumble)")
    ) * DRYLON_BUFFER

    machines_cotton = 0.0 if effective_cotton == 0 else required_cotton / effective_cotton
    machines_drylon = 0.0 if effective_drylon == 0 else required_drylon / effective_drylon
    machines_total = round_half_up(machines_cotton + machines_drylon, 0)

    set_value(table, "Effective Production", "Cotton", effective_cotton)
    set_value(table, "Effective Production", "Drylon", effective_drylon)
    set_value(table, "Required Production", "Cotton", required_cotton)
    set_value(table, "Required Production", "Drylon", required_drylon)
    set_value(table, "Machines Required", "Cotton", machines_cotton)
    set_value(table, "Machines Required", "Drylon", machines_drylon)
    set_value(table, "Machines Required", "Total", machines_total)
    return table.reset_index(drop=True)
