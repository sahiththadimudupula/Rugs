from __future__ import annotations

import pandas as pd

from core.formatting import to_number
from calculations.capacity import LOCATION_COLUMN, ACTUAL_PCS_COLUMN


def get_capacity_pcs(capacity_table: pd.DataFrame, location_name: str) -> float:
    row = capacity_table[capacity_table[LOCATION_COLUMN] == location_name]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0][ACTUAL_PCS_COLUMN])


def get_asking_value(asking_rate_table: pd.DataFrame, main_group: str, sub_group: str, category: str, subcategory: str) -> float:
    mask = (
        (asking_rate_table["Main_Group"].astype(str).str.strip() == main_group)
        & (asking_rate_table["Sub_Group"].fillna("").astype(str).str.strip() == sub_group)
        & (asking_rate_table["Category"].astype(str).str.strip() == category)
        & (asking_rate_table["Subcategory"].astype(str).str.strip() == subcategory)
    )
    row = asking_rate_table[mask]
    if row.empty:
        return 0.0
    return to_number(row.iloc[0]["Asking_Rate_Per_Day"])


def build_packing_tqm_helper(capacity_table: pd.DataFrame, asking_rate_table: pd.DataFrame) -> pd.DataFrame:
    smart_line_req_day = get_capacity_pcs(capacity_table, "Bath Rugs (Wash)") + get_capacity_pcs(capacity_table, "Bath Rugs (Non- Wash with Tumble)")
    ina_req_day = get_capacity_pcs(capacity_table, "Bath Rugs (Non- Wash with Tumble)") + get_capacity_pcs(capacity_table, "Total")
    chenille_req_day = get_capacity_pcs(capacity_table, "Chenille")
    cotton_req_day = get_asking_value(asking_rate_table, "Processing", "", "Process", "Cotton dyeing")

    helper_rows = [
        {
            "Type": "Drylon",
            "Line": "Smart Line",
            "Req/Day": smart_line_req_day,
            "Production Capacity": 4500.0,
            "Reqd. Lines": smart_line_req_day / 4500.0 / 3.0,
            "TQM Capacity": 1200.0,
            "TQM": 4500.0 / 1200.0,
            "Notes": "Reqd. Lines = Req/Day / Production Capacity / 3",
        },
        {
            "Type": "Drylon",
            "Line": "INA",
            "Req/Day": ina_req_day,
            "Production Capacity": 4500.0,
            "Reqd. Lines": ina_req_day / 4500.0 / 3.0,
            "TQM Capacity": 1200.0,
            "TQM": 4500.0 / 1200.0,
            "Notes": "Loading = always 1 person per line per shift",
        },
        {
            "Type": "Chenille",
            "Line": "Manual (Chenille)",
            "Req/Day": chenille_req_day,
            "Production Capacity": 1500.0,
            "Reqd. Lines": chenille_req_day / 1500.0 / 3.0,
            "TQM Capacity": 1500.0,
            "TQM": 1500.0 / 1500.0,
            "Notes": "Smart Line capped at 2 lines; balance moves to INA",
        },
        {
            "Type": "Cotton",
            "Line": "Manual (Cotton)",
            "Req/Day": cotton_req_day,
            "Production Capacity": 1500.0,
            "Reqd. Lines": cotton_req_day / 1500.0 / 3.0,
            "TQM Capacity": 800.0,
            "TQM": 1500.0 / 800.0,
            "Notes": "TQM = Production Capacity / TQM Capacity",
        },
    ]
    return pd.DataFrame(helper_rows)
