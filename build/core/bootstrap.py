from __future__ import annotations
from core.persistence import load_raw_sheets
from core.sheet_parser import parse_ppc, parse_capacity, parse_coating, parse_cs, parse_hydro, parse_master
from core.registries import init_nodes, build_row_rules, init_manual_overrides
from engines.pipeline import recalc_all

def bootstrap_state() -> dict:
    raw = load_raw_sheets()
    state = {
        "ppc_df": parse_ppc(raw["Packing"]),
        "capacity_df": parse_capacity(raw["Capacity"]),
        "coating_df": parse_coating(raw["Coating"]),
        "cs_df": parse_cs(raw["CS"]),
        "hydro_df": parse_hydro(raw["Hydro "]),
        "master_df": parse_master(raw["Rugs"]),
    }
    state["nodes"] = init_nodes(state)
    state["row_rules"] = build_row_rules(state["master_df"])
    state["master_index"] = {row_id: idx for idx, row_id in enumerate(state["master_df"]["row_id"].tolist())}
    state["overrides"] = init_manual_overrides(state["master_df"])
    state["snapshots"] = {
        "ppc_df": state["ppc_df"].copy(deep=True),
        "coating_df": state["coating_df"].copy(deep=True),
        "hydro_df": state["hydro_df"].copy(deep=True),
    }
    recalc_all(state)
    state["snapshots"]["ppc_df"] = state["ppc_df"].copy(deep=True)
    state["snapshots"]["coating_df"] = state["coating_df"].copy(deep=True)
    state["snapshots"]["hydro_df"] = state["hydro_df"].copy(deep=True)
    return state
