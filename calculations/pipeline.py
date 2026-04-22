from __future__ import annotations

import pandas as pd

from calculations.asking_rate import recalculate_asking_rate_table
from calculations.capacity import recalculate_capacity_table
from calculations.coating import recalculate_coating_table
from calculations.cs import recalculate_cs_table
from calculations.hydro import recalculate_hydro_table
from calculations.dyeing import recalculate_dyeing_tables
from calculations.packing_tqm import build_packing_tqm_helper
from calculations.master import recalculate_master_table


def run_full_pipeline(state: dict) -> dict:
    asking_rate_df = recalculate_asking_rate_table(
        state["packing_source_df"],
        state.get("packing_edit_df"),
    )
    capacity_df = recalculate_capacity_table(state["capacity_source_df"], asking_rate_df)
    coating_df = recalculate_coating_table(
        state["coating_source_df"],
        capacity_df,
        state.get("coating_edit_df"),
    )
    cs_df = recalculate_cs_table(state["cs_source_df"], capacity_df)
    hydro_df = recalculate_hydro_table(
        state["hydro_source_df"],
        capacity_df,
        state.get("hydro_edit_df"),
    )
    dyeing_result = recalculate_dyeing_tables(asking_rate_df, capacity_df)
    packing_tqm_helper_df = build_packing_tqm_helper(capacity_df, asking_rate_df)
    master_df = recalculate_master_table(
        state["master_source_df"],
        state.get("master_df"),
        coating_df,
        cs_df,
        hydro_df,
        dyeing_result,
        packing_tqm_helper_df,
    )
    return {
        "asking_rate_df": asking_rate_df,
        "capacity_df": capacity_df,
        "coating_df": coating_df,
        "cs_df": cs_df,
        "hydro_df": hydro_df,
        "dyeing_result": dyeing_result,
        "packing_tqm_helper_df": packing_tqm_helper_df,
        "master_df": master_df,
    }
