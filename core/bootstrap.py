from __future__ import annotations

from core.persistence import load_raw_sheets, current_workbook_path
from core.sheet_parser import parse_ppc, parse_capacity, parse_coating, parse_cs, parse_hydro, parse_master, parse_packintqm
from core.registries import init_nodes, build_row_rules, init_manual_overrides
from engines.pipeline import recalc_all
from engines.dyeing import build_default_dye_inputs_df, build_default_ezm_paddle_df, build_default_jet_df


def bootstrap_state() -> dict:
    raw = load_raw_sheets()
    state = {
        "using_working_file": current_workbook_path().name == 'Rugs_working.xlsx',
        "ppc_df": parse_ppc(raw["Packing"]),
        "capacity_df": parse_capacity(raw["Capacity"]),
        "coating_df": parse_coating(raw["Coating"]),
        "cs_df": parse_cs(raw["CS"]),
        "hydro_df": parse_hydro(raw["Hydro "]),
        "master_df": parse_master(raw["Rugs"]),
        "dye_inputs_df": build_default_dye_inputs_df(),
        "dye_ezm_df": build_default_ezm_paddle_df(),
        "dye_jet_df": build_default_jet_df(),
        "dye_outputs": {},
        "dye_input_overrides": {"drylon_target": False, "cotton_target": False, "jet_requirement": False, "allowed_shortage": False},
    }
    state["packing_tqm_source_df"], state["packing_tqm_draft_source_df"] = parse_packintqm(raw.get("Packing&TQM"))
    state["packing_tqm_helper_df"] = state["packing_tqm_source_df"].copy(deep=True)
    state["nodes"] = init_nodes(state)
    state["row_rules"] = build_row_rules(state["master_df"])
    state["master_index"] = {row_id: idx for idx, row_id in enumerate(state["master_df"]["row_id"].tolist())}
    state["overrides"] = init_manual_overrides(state["master_df"])
    state["snapshots"] = {
        "ppc_df": state["ppc_df"].copy(deep=True),
        "coating_df": state["coating_df"].copy(deep=True),
        "hydro_df": state["hydro_df"].copy(deep=True),
        "dye_inputs_df": state["dye_inputs_df"].copy(deep=True),
        "dye_ezm_df": state["dye_ezm_df"].copy(deep=True),
        "dye_jet_df": state["dye_jet_df"].copy(deep=True),
    }
    state["dirty"] = {
        "capacity": False,
        "coating": False,
        "cs": False,
        "hydro": False,
        "dyeing": False,
        "packintqm": False,
        "master": False,
    }
    recalc_all(state)
    state["download_bytes"] = None
    state["download_dirty"] = True
    for key in list(state["snapshots"].keys()):
        state["snapshots"][key] = state[key].copy(deep=True)
    return state
