from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from config.constants import *
from core.registries import ppc_key, capacity_key, coating_key, cs_key, hydro_key, dye_key, packintqm_key
from services.master_rows import rebuild_master_row
from engines.dyeing import ProductTargets, calculate_ezm_paddle, calculate_jet_dyeing

COATING_ROWS = [f"master.coating.sr_{n}" for n in range(1, 13)]
CUT_AND_SEW_ROWS = [f"master.cut_and_sew.sr_{n}" for n in [1, 2, 3, 4, 6, 7, 8, 9, 11, 19, 20, 23, 24]]
DYEING_ROWS = ["master.dyeing.sr_1", "master.dyeing.sr_4", "master.dyeing.sr_5", "master.dyeing.sr_10"]
PACKING_TQM_ROWS = [f"master.packing_line_mp.sr_{n}" for n in range(1,29)] + [f"master.packing_support_mp.sr_{n}" for n in range(29,47)] + [f"master.tqm.sr_{n}" for n in [47,48,49,50,52,53,54,55,56,57,58,59]] + [f"master.tqm_other_support.sr_{n}" for n in range(60,72)]


def recalc_all(state: dict) -> None:
    recalc_ppc(state)
    recalc_capacity(state)
    recalc_coating(state)
    recalc_cs(state)
    recalc_hydro(state)
    recalc_dyeing(state)
    recalc_packintqm(state)
    sync_frames(state)
    rebuild_linked_master_rows(state)
    state.setdefault("dirty", {})
    for key in ["capacity", "coating", "cs", "hydro", "dyeing", "packintqm", "master"]:
        state["dirty"][key] = False


def ensure_capacity_current(state: dict) -> None:
    dirty = state.setdefault("dirty", {})
    if not dirty.get("capacity", False):
        return
    recalc_capacity(state)
    sync_frames(state)
    dirty["capacity"] = False


def ensure_coating_current(state: dict) -> None:
    dirty = state.setdefault("dirty", {})
    ensure_capacity_current(state)
    if not dirty.get("coating", False):
        return
    recalc_coating(state)
    sync_frames(state)
    for row_id in COATING_ROWS:
        rebuild_master_row(state, row_id)
    dirty["coating"] = False
    dirty["master"] = True


def ensure_cs_current(state: dict) -> None:
    dirty = state.setdefault("dirty", {})
    ensure_capacity_current(state)
    if not dirty.get("cs", False):
        return
    recalc_cs(state)
    sync_frames(state)
    for row_id in CUT_AND_SEW_ROWS:
        rebuild_master_row(state, row_id)
    dirty["cs"] = False
    dirty["master"] = True


def ensure_hydro_current(state: dict) -> None:
    dirty = state.setdefault("dirty", {})
    ensure_capacity_current(state)
    if not dirty.get("hydro", False):
        return
    recalc_hydro(state)
    sync_frames(state)
    if "master.dyeing.sr_10" in DYEING_ROWS:
        rebuild_master_row(state, "master.dyeing.sr_10")
    dirty["hydro"] = False
    dirty["master"] = True


def ensure_dyeing_current(state: dict) -> None:
    dirty = state.setdefault("dirty", {})
    ensure_capacity_current(state)
    ensure_cs_current(state)
    ensure_hydro_current(state)
    if not dirty.get("dyeing", False):
        return
    recalc_dyeing(state)
    sync_frames(state)
    for row_id in ["master.dyeing.sr_1", "master.dyeing.sr_4", "master.dyeing.sr_5", "master.dyeing.sr_10"]:
        rebuild_master_row(state, row_id)
    dirty["dyeing"] = False
    dirty["master"] = True


def ensure_packintqm_current(state: dict) -> None:
    dirty = state.setdefault("dirty", {})
    ensure_capacity_current(state)
    if not dirty.get("packintqm", False):
        return
    recalc_packintqm(state)
    for row_id in PACKING_TQM_ROWS:
        if row_id in state["master_index"]:
            rebuild_master_row(state, row_id)
    dirty["packintqm"] = False
    dirty["master"] = True


def ensure_everything_current(state: dict) -> None:
    ensure_coating_current(state)
    ensure_cs_current(state)
    ensure_hydro_current(state)
    ensure_dyeing_current(state)
    ensure_packintqm_current(state)


def recalc_ppc(state: dict) -> None:
    n = state["nodes"]
    for _, r in state["ppc_df"].iterrows():
        n[ppc_key(r["Main_Group"], r["Sub_Group"], r["Subcategory"])] = float(r["Asking_Rate_Per_Day"])
    n["ppc.packing.grand_total.ask_rate"] = sum(
        n[k]
        for k in [
            "ppc.packing.carving.ask_rate",
            "ppc.packing.chenile.ask_rate",
            "ppc.packing.non_carving.ask_rate",
            "ppc.packing.roll.ask_rate",
            "ppc.packing.rugs.ask_rate",
        ]
    )
    n["ppc.c_and_s.overedging.overedging_total.ask_rate"] = sum(
        n[k]
        for k in [
            "ppc.c_and_s.overedging.drylon_washing.ask_rate",
            "ppc.c_and_s.overedging.non_dyeing.ask_rate",
            "ppc.c_and_s.overedging.tumble.ask_rate",
        ]
    )
    n["ppc.c_and_s.union.union_total.ask_rate"] = sum(
        n[k]
        for k in [
            "ppc.c_and_s.union.cotton_dyeing.ask_rate",
            "ppc.c_and_s.union.drylon_washing.ask_rate",
            "ppc.c_and_s.union.polyester_dyeing.ask_rate",
        ]
    )
    n["ppc.c_and_s.grand_total.ask_rate"] = n["ppc.c_and_s.overedging.overedging_total.ask_rate"] + n["ppc.c_and_s.union.union_total.ask_rate"]
    n["ppc.grey_issue.grand_total.ask_rate"] = sum(
        n[k]
        for k in [
            "ppc.grey_issue.cotton_dyeing.ask_rate",
            "ppc.grey_issue.drylon_washing.ask_rate",
            "ppc.grey_issue.non_dyeing.ask_rate",
            "ppc.grey_issue.polyester_dyeing.ask_rate",
            "ppc.grey_issue.tumble.ask_rate",
        ]
    )
    n["ppc.processing.mt_pc_day.value"] = 54.42 * 1.1 * 3.9
    n["ppc.processing.tt_pc_day.value"] = n["ppc.processing.cotton_dyeing.ask_rate"] - n["ppc.processing.mt_pc_day.value"]
    n["ppc.processing.grand_total.ask_rate"] = sum(
        n[k] for k in ["ppc.processing.cotton_dyeing.ask_rate", "ppc.processing.drylon_washing.ask_rate", "ppc.processing.polyester_dyeing.ask_rate"]
    )
    n["ppc.coating.grand_total.ask_rate"] = n["ppc.coating.cotton.ask_rate"] + n["ppc.coating.foam.ask_rate"]
    n["ppc.machine_tufting.grand_total.ask_rate"] = sum(
        n[k]
        for k in [
            "ppc.machine_tufting.1_8_cut.ask_rate",
            "ppc.machine_tufting.1_8_mlcl.ask_rate",
            "ppc.machine_tufting.1_10_loop.ask_rate",
            "ppc.machine_tufting.3_8_cut.ask_rate",
            "ppc.machine_tufting.3_8_loop.ask_rate",
        ]
    )
    n["ppc.table_tufting.grand_total.ask_rate"] = n["ppc.table_tufting.1_4_rev.ask_rate"] + n["ppc.table_tufting.3_16_cut.ask_rate"]


def recalc_capacity(state: dict) -> None:
    n = state["nodes"]
    n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")] = n["ppc.processing.mt_pc_day.value"]
    n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")] = n["ppc.processing.tt_pc_day.value"]
    n[capacity_key("Chenille", "actual_pcs_per_day")] = n["ppc.packing.chenile.ask_rate"]
    n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")] = n["ppc.c_and_s.overedging.non_dyeing.ask_rate"] + n["ppc.c_and_s.overedging.tumble.ask_rate"]
    n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")] = (
        n["ppc.packing.grand_total.ask_rate"]
        - n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")]
        - n[capacity_key("Chenille", "actual_pcs_per_day")]
        - n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")]
    )
    locations = [
        "Cotton-M/C Tufting",
        "Cotton-Table Tufting",
        "Chenille",
        "Bath Rugs (Wash)",
        "Bath Rugs (Non- Wash with Tumble)",
    ]
    for loc in locations:
        pcs = n[capacity_key(loc, "actual_pcs_per_day")]
        avg = n[capacity_key(loc, "avg_area_per_piece")]
        n[capacity_key(loc, "actual_mtr_per_day")] = (pcs * avg) / SQUARE_METER_DIVISOR
        n[capacity_key(loc, "actual_lac_sqm_per_month")] = (pcs * avg * DAYS_PER_MONTH) / 100000.0
    n[capacity_key("Total", "actual_pcs_per_day")] = sum(n[capacity_key(loc, "actual_pcs_per_day")] for loc in locations)
    n[capacity_key("Total", "actual_mtr_per_day")] = sum(n[capacity_key(loc, "actual_mtr_per_day")] for loc in locations)
    n[capacity_key("Total", "actual_lac_sqm_per_month")] = sum(n[capacity_key(loc, "actual_lac_sqm_per_month")] for loc in locations)


def recalc_coating(state: dict) -> None:
    n = state["nodes"]
    n[coating_key("Effective Production", "Cotton")] = n[coating_key("Speed", "Cotton")] * COATING_CAPACITY_BASE * n[coating_key("Efficiency", "Cotton")] * n[coating_key("Utilisation", "Cotton")]
    n[coating_key("Effective Production", "Drylon")] = n[coating_key("Speed", "Drylon")] * COATING_CAPACITY_BASE * n[coating_key("Efficiency", "Drylon")] * n[coating_key("Utilisation", "Drylon")]
    n[coating_key("Required Production", "Cotton")] = 0.0
    n[coating_key("Required Production", "Drylon")] = (n[capacity_key("Bath Rugs (Wash)", "actual_mtr_per_day")] + n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_mtr_per_day")]) * COATING_BUFFER
    eff_c = n[coating_key("Effective Production", "Cotton")]
    eff_d = n[coating_key("Effective Production", "Drylon")]
    n[coating_key("Machines Required", "Cotton")] = 0.0 if abs(eff_c) < 1e-9 else n[coating_key("Required Production", "Cotton")] / eff_c
    n[coating_key("Machines Required", "Drylon")] = 0.0 if abs(eff_d) < 1e-9 else n[coating_key("Required Production", "Drylon")] / eff_d
    n[coating_key("Machines Required", "Total")] = round(n[coating_key("Machines Required", "Cotton")] + n[coating_key("Machines Required", "Drylon")])


def recalc_cs(state: dict) -> None:
    n = state["nodes"]
    def setv(sec, proc, met, val):
        n[cs_key(sec, proc, met)] = float(val)

    cotton_tt = n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")]
    cotton_mt = n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")]
    cotton_mt_mtr = n[capacity_key("Cotton-M/C Tufting", "actual_mtr_per_day")]
    dry_w = n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")]
    dry_w_mtr = n[capacity_key("Bath Rugs (Wash)", "actual_mtr_per_day")]
    dry_n = n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")]
    dry_n_mtr = n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_mtr_per_day")]
    chen = n[capacity_key("Chenille", "actual_pcs_per_day")]

    vals = {
        ("Production", "Cotton Dyeing (TT)", "Pcs/Day"): cotton_tt,
        ("Production", "Cotton Dyeing (TT)", "Pcs/Month"): cotton_tt * CS_DAYS_PER_MONTH,
        ("Production", "Cotton Dyeing (TT)", "Linear Mtr"): 0,
        ("Production", "Cotton Dyeing (TT)", "Union"): 0,
        ("Production", "Cotton Dyeing (TT)", "Mat"): 0,
        ("Production", "Cotton Dyeing (TT)", "Shape/Design"): 0,
        ("Production", "Cotton Dyeing (TT)", "Over Edging"): 0,
        ("Production", "Cotton Dyeing (MT)", "Pcs/Day"): cotton_mt,
        ("Production", "Cotton Dyeing (MT)", "Pcs/Month"): cotton_mt * CS_DAYS_PER_MONTH,
        ("Production", "Cotton Dyeing (MT)", "Linear Mtr"): cotton_mt_mtr,
        ("Production", "Cotton Dyeing (MT)", "Union"): cotton_mt,
        ("Production", "Cotton Dyeing (MT)", "Mat"): cotton_mt,
        ("Production", "Cotton Dyeing (MT)", "Shape/Design"): 0,
        ("Production", "Cotton Dyeing (MT)", "Over Edging"): 0,
        ("Production", "Drylon (Washing)", "Pcs/Day"): dry_w,
        ("Production", "Drylon (Washing)", "Pcs/Month"): dry_w * CS_DAYS_PER_MONTH,
        ("Production", "Drylon (Washing)", "Linear Mtr"): dry_w_mtr,
        ("Production", "Drylon (Washing)", "Union"): dry_w * 0.85,
        ("Production", "Drylon (Washing)", "Over Edging"): dry_w - (dry_w * 0.85),
        ("Production", "Drylon (Washing)", "Mat"): dry_w * 0.5,
        ("Production", "Drylon (Washing)", "Shape/Design"): 1000,
        ("Production", "Drylon_Rugs (Non_Washing)", "Pcs/Day"): dry_n,
        ("Production", "Drylon_Rugs (Non_Washing)", "Pcs/Month"): dry_n * CS_DAYS_PER_MONTH,
        ("Production", "Drylon_Rugs (Non_Washing)", "Linear Mtr"): dry_n_mtr,
        ("Production", "Drylon_Rugs (Non_Washing)", "Union"): 0,
        ("Production", "Drylon_Rugs (Non_Washing)", "Over Edging"): dry_n,
        ("Production", "Drylon_Rugs (Non_Washing)", "Shape/Design"): 7500,
        ("Production", "Drylon_Rugs (Non_Washing)", "Mat"): dry_n - 7500,
        ("Production", "Carpet_Rolling", "Pcs/Day"): 0,
        ("Production", "Carpet_Rolling", "Pcs/Month"): 0,
        ("Production", "Carpet_Rolling", "Linear Mtr"): 0,
        ("Production", "Carpet_Rolling", "Union"): 0,
        ("Production", "Carpet_Rolling", "Over Edging"): 0,
        ("Production", "Carpet_Rolling", "Mat"): 0,
        ("Production", "Carpet_Rolling", "Shape/Design"): 0,
        ("Production", "Chenille", "Pcs/Day"): chen,
        ("Production", "Chenille", "Pcs/Month"): chen * CS_DAYS_PER_MONTH,
        ("Production", "Chenille", "Linear Mtr"): 0,
        ("Production", "Chenille", "Union"): chen,
        ("Production", "Chenille", "Over Edging"): 0,
        ("Production", "Chenille", "Mat"): 0,
        ("Production", "Chenille", "Shape/Design"): 0,
    }
    for k, v in vals.items():
        setv(*k, v)

    def g(proc, met):
        return n[cs_key("Production", proc, met)]

    total_pcs_day = sum(g(p, "Pcs/Day") for p in ["Cotton Dyeing (TT)", "Cotton Dyeing (MT)", "Drylon (Washing)", "Drylon_Rugs (Non_Washing)", "Carpet_Rolling", "Chenille"])
    total_pcs_mon = sum(g(p, "Pcs/Month") for p in ["Cotton Dyeing (TT)", "Cotton Dyeing (MT)", "Drylon (Washing)", "Drylon_Rugs (Non_Washing)", "Carpet_Rolling", "Chenille"])
    total_lin = sum(g(p, "Linear Mtr") for p in ["Cotton Dyeing (TT)", "Cotton Dyeing (MT)", "Drylon (Washing)", "Drylon_Rugs (Non_Washing)", "Carpet_Rolling", "Chenille"])
    total_union = sum(g(p, "Union") for p in ["Cotton Dyeing (TT)", "Cotton Dyeing (MT)", "Drylon (Washing)", "Drylon_Rugs (Non_Washing)", "Carpet_Rolling", "Chenille"])
    total_over = sum(g(p, "Over Edging") for p in ["Cotton Dyeing (TT)", "Cotton Dyeing (MT)", "Drylon (Washing)", "Drylon_Rugs (Non_Washing)", "Carpet_Rolling", "Chenille"])
    total_shape = sum(g(p, "Shape/Design") for p in ["Cotton Dyeing (TT)", "Cotton Dyeing (MT)", "Drylon (Washing)", "Drylon_Rugs (Non_Washing)", "Carpet_Rolling", "Chenille"])
    setv("Production", "Total Pcs", "Pcs/Day", total_pcs_day)
    setv("Production", "Total Pcs", "Pcs/Month", total_pcs_mon)
    setv("Production", "Total Pcs", "Linear Mtr", total_lin)
    setv("Production", "Total Pcs", "Union", total_union)
    setv("Production", "Total Pcs", "Over Edging", total_over)
    setv("Production", "Total Pcs", "Mat", 28030)
    setv("Production", "Total Pcs", "Shape/Design", total_shape)
    setv("Production", "Total In SqMtr", "Pcs/Day", n[capacity_key("Total", "actual_lac_sqm_per_month")])
    setv("Production", "Total In SqMtr", "Pcs/Month", n[cs_key("Production", "Total In SqMtr", "Pcs/Day")] * 30)
    setv("Production", "Total In SqMtr", "Shape/Design", total_pcs_day - chen - total_shape - 28030)

    setv("Machine", "Length Cutting M/C", "Existing Capacity/MC", 13 * 60 * 24 * 0.8 * 0.65)
    setv("Machine", "Length Cutting M/C", "Requirements/day", total_lin)
    setv("Machine", "Length Cutting M/C", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Length Cutting M/C", "Existing Capacity/MC")]) < 1e-9 else total_lin / n[cs_key("Machine", "Length Cutting M/C", "Existing Capacity/MC")])
    setv("Machine", "Length Cutting M/C", "New M/C Reqd", n[cs_key("Machine", "Length Cutting M/C", "Total M/C Reqd")] - n[cs_key("Machine", "Length Cutting M/C", "Existing MCs available")])

    setv("Machine", "Cross cutting M/C", "Existing Capacity/MC", 10 * 60 * 24 * 0.8)
    setv("Machine", "Cross cutting M/C", "Requirements/day", 28030)
    setv("Machine", "Cross cutting M/C", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Cross cutting M/C", "Existing Capacity/MC")]) < 1e-9 else 28030 / n[cs_key("Machine", "Cross cutting M/C", "Existing Capacity/MC")])
    setv("Machine", "Cross cutting M/C", "New M/C Reqd", n[cs_key("Machine", "Cross cutting M/C", "Total M/C Reqd")] - n[cs_key("Machine", "Cross cutting M/C", "Existing MCs available")])

    printed_req = n[cs_key("Production", "Total In SqMtr", "Shape/Design")]
    setv("Machine", "Printed / Manual cutting", "Requirements/day", printed_req)
    setv("Machine", "Printed / Manual cutting", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Printed / Manual cutting", "Existing Capacity/MC")]) < 1e-9 else printed_req / n[cs_key("Machine", "Printed / Manual cutting", "Existing Capacity/MC")])

    shape_req = total_shape
    setv("Machine", "Shape cutting M/C", "Requirements/day", shape_req)
    setv("Machine", "Shape cutting M/C", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Shape cutting M/C", "Existing Capacity/MC")]) < 1e-9 else shape_req / n[cs_key("Machine", "Shape cutting M/C", "Existing Capacity/MC")])
    setv("Machine", "Shape cutting M/C", "New M/C Reqd", n[cs_key("Machine", "Shape cutting M/C", "Total M/C Reqd")] - n[cs_key("Machine", "Shape cutting M/C", "Existing MCs available")])

    length_over_req = g("Drylon (Washing)", "Over Edging") + g("Drylon_Rugs (Non_Washing)", "Over Edging")
    setv("Machine", "Length Over edging(Rugs)", "Existing Capacity/MC", 7 * 60 * 24 * 0.82)
    setv("Machine", "Length Over edging(Rugs)", "Requirements/day", length_over_req)
    setv("Machine", "Length Over edging(Rugs)", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Length Over edging(Rugs)", "Existing Capacity/MC")]) < 1e-9 else length_over_req / n[cs_key("Machine", "Length Over edging(Rugs)", "Existing Capacity/MC")])
    setv("Machine", "Length Over edging(Rugs)", "New M/C Reqd", n[cs_key("Machine", "Length Over edging(Rugs)", "Total M/C Reqd")] - n[cs_key("Machine", "Length Over edging(Rugs)", "Existing MCs available")])

    setv("Machine", "Length Over edging(carpet)", "Existing Capacity/MC", 6 * 60 * 24 * 0.82 / 1.7)
    setv("Machine", "Length Over edging(carpet)", "Requirements/day", 0)
    setv("Machine", "Length Over edging(carpet)", "Total M/C Reqd", 0)

    setv("Machine", "Tape Binding", "Requirements/day", total_union)
    setv("Machine", "Tape Binding", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Tape Binding", "Existing Capacity/MC")]) < 1e-9 else total_union / n[cs_key("Machine", "Tape Binding", "Existing Capacity/MC")])
    setv("Machine", "Tape Binding", "New M/C Reqd", n[cs_key("Machine", "Tape Binding", "Total M/C Reqd")] - n[cs_key("Machine", "Tape Binding", "Existing MCs available")])

    setv("Machine", "Over edging for Rugs", "Requirements/day", length_over_req)
    setv("Machine", "Over edging for Rugs", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Over edging for Rugs", "Existing Capacity/MC")]) < 1e-9 else length_over_req / n[cs_key("Machine", "Over edging for Rugs", "Existing Capacity/MC")])
    setv("Machine", "Over edging for Rugs", "New M/C Reqd", n[cs_key("Machine", "Over edging for Rugs", "Total M/C Reqd")] - n[cs_key("Machine", "Over edging for Rugs", "Existing MCs available")])

    bartack_req = total_union + total_over
    setv("Machine", "Bartack", "Requirements/day", bartack_req)
    setv("Machine", "Bartack", "Total M/C Reqd", 0 if abs(n[cs_key("Machine", "Bartack", "Existing Capacity/MC")]) < 1e-9 else bartack_req / n[cs_key("Machine", "Bartack", "Existing Capacity/MC")])
    setv("Machine", "Bartack", "New M/C Reqd", n[cs_key("Machine", "Bartack", "Total M/C Reqd")] - n[cs_key("Machine", "Bartack", "Existing MCs available")])

    setv("Machine", "Table Tufting (3/16)", "Total M/C Reqd", n[cs_key("Machine", "Tape Binding", "Total M/C Reqd")] * 3 / 2)
    setv("Machine", "Table Tufting (Reversable)", "Total M/C Reqd", n[cs_key("Machine", "Over edging for Rugs", "Total M/C Reqd")] * 3 / 2)

    setv("Machine", "Cross Over edging (carpet)", "Existing Capacity/MC", 5 * 60 * 24 * 0.82)
    setv("Machine", "Cross Over edging (carpet)", "Requirements/day", 0)
    setv("Machine", "Cross Over edging (carpet)", "Total M/C Reqd", 0)

    n["cs.custom.ims_checker.machine_count"] = (cotton_mt + dry_w + dry_n) / 7500.0


def recalc_hydro(state: dict) -> None:
    n = state["nodes"]
    for col in state["hydro_df"].columns:
        if col != "row_order":
            n[hydro_key(col)] = float(state["hydro_df"].at[0, col])
    n[hydro_key("Required Pcs")] = (
        n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")]
        + n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")]
        + n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")]
    )
    n[hydro_key("Prod/mc/day (Kgs)")] = n[hydro_key("No. Of Batch")] * n[hydro_key("M/s Capacity Proposed")] * (n[hydro_key("Efficiency")] / 100.0)
    n[hydro_key("Pcs/day/mc")] = n[hydro_key("Prod/mc/day (Kgs)")] * HYDRO_PCS_CONVERSION
    base = n[hydro_key("Prod/mc/day (Kgs)")]
    n[hydro_key("Total M/c Req")] = 0 if abs(base) < 1e-9 else round(n[hydro_key("Required Pcs")] / base)


def recalc_dyeing(state: dict) -> None:
    n = state["nodes"]
    driver_df = state["dye_inputs_df"].copy()
    derived_map = {
        "drylon_target": n[cs_key("Production", "Drylon (Washing)", "Pcs/Day")],
        "cotton_target": n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")] + n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")],
        "jet_requirement": n[capacity_key("Chenille", "actual_pcs_per_day")] * 1.05,
    }
    for key, derived in derived_map.items():
        if not state["dye_input_overrides"].get(key, False):
            driver_df.loc[driver_df["key"] == key, "Value"] = float(derived)
    state["dye_inputs_df"] = driver_df
    values = {row["key"]: float(row["Value"]) for _, row in driver_df.iterrows()}
    ezm_result = calculate_ezm_paddle(state["dye_ezm_df"], ProductTargets(drylon=values["drylon_target"], cotton=values["cotton_target"]))
    jet_result = calculate_jet_dyeing(state["dye_jet_df"], values["jet_requirement"], values["allowed_shortage"])
    state["dye_outputs"] = {"ezm_paddle": ezm_result, "jet": jet_result}
    n[dye_key("ezm_paddle", "paddle_count")] = float(ezm_result["paddle_count"])
    n[dye_key("ezm_paddle", "ezm_count")] = float(ezm_result["ezm_count"])
    n[dye_key("jet", "machine_count")] = float(jet_result["selected_machine_count"])


def _find_row_index(df, section, dept, designation):
    mask=(df["Section"].astype(str).str.strip()==section)&(df["Dept_Machine_Name"].astype(str).str.strip()==dept)&(df["Designation"].astype(str).str.strip()==designation)
    if not mask.any():
        return None
    return df[mask].index[0]


def _update_row_direct(state, section, dept, designation, machine_count=None, formula=None, scientific=None, default_final=True):
    df=state["master_df"]
    idx=_find_row_index(df, section, dept, designation)
    if idx is None:
        return
    row_id=df.at[idx, "row_id"]
    overrides=state["overrides"][row_id]
    if machine_count is not None and not overrides["machine"]:
        df.at[idx, "Machine_Count"]=float(machine_count)
    if formula is not None and not overrides["machine"]:
        df.at[idx, "Formulas"]=formula
    if scientific is not None and not overrides["machine"]:
        df.at[idx, "BE_Scientific_Manpower"]=float(scientific)
        if default_final and not overrides["be_final"]:
            df.at[idx, "BE_Final_Manpower"] = float(Decimal(str(scientific)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def recalc_packintqm(state: dict) -> None:
    import math
    import pandas as pd

    n = state["nodes"]

    def round1(value: float) -> float:
        return round(float(value), 1)

    def fmt1(value: float) -> str:
        return f"{round1(value):.1f}"

    def fmt_req(value: float) -> str:
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        return f"{value:.1f}"

    smart_req = float(n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")] + n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")])
    chen_req = float(n[capacity_key("Chenille", "actual_pcs_per_day")])
    cotton_req = float(n["ppc.processing.cotton_dyeing.ask_rate"])

    smart_prod_cap = 4500.0
    ina_prod_cap = 4500.0
    chen_prod_cap = 1500.0
    cotton_prod_cap = 1500.0

    smart_available = 2.0
    ina_available = 6.0

    raw_drylon_lines = 0.0 if abs(smart_prod_cap) < 1e-9 else smart_req / smart_prod_cap / 3.0
    smart_lines = min(raw_drylon_lines, smart_available)
    ina_lines = max(raw_drylon_lines - smart_lines, 0.0)
    ina_lines = min(ina_lines, ina_available)

    smart_lines = round1(smart_lines)
    ina_lines = round1(ina_lines)
    chen_lines = round1(0.0 if abs(chen_prod_cap) < 1e-9 else chen_req / chen_prod_cap / 3.0)
    cotton_lines = round1(0.0 if abs(cotton_prod_cap) < 1e-9 else cotton_req / cotton_prod_cap / 3.0)

    dry_tqm = round1(smart_prod_cap / 1200.0)
    chen_tqm = round1(chen_prod_cap / 1500.0)
    cotton_tqm = round1(cotton_prod_cap / 800.0)

    helper_rows = [
        ("Drylon", "Smart Line", smart_req, smart_prod_cap, smart_lines, 1200.0, dry_tqm, smart_available),
        ("Drylon", "INA", smart_req, ina_prod_cap, ina_lines, 1200.0, dry_tqm, ina_available),
        ("Chenille", "Manual (Chenille)", chen_req, chen_prod_cap, chen_lines, 1500.0, chen_tqm, None),
        ("Cotton", "Manual (Cotton)", cotton_req, cotton_prod_cap, cotton_lines, 800.0, cotton_tqm, None),
    ]

    helper_df = pd.DataFrame(helper_rows, columns=["Type", "Line", "Req/Day", "Production Capacity", "Reqd. Lines", "TQM Capacity", "TQM", "aveleble lines"])
    helper_df["row_order"] = range(len(helper_df))
    state["packing_tqm_helper_df"] = helper_df

    helper_lookup = {
        row[1]: {
            "req_day": float(row[2]),
            "production_capacity": float(row[3]),
            "reqd_lines": float(row[4]),
            "tqm_capacity": float(row[5]),
            "tqm": float(row[6]),
            "available_lines": row[7],
        }
        for row in helper_rows
    }

    for line, row_num in {"Smart Line": 3, "INA": 4, "Manual (Chenille)": 5, "Manual (Cotton)": 6}.items():
        vals = helper_lookup[line]
        for metric, value in [("Req/Day", vals["req_day"]), ("Production Capacity", vals["production_capacity"]), ("Reqd. Lines", vals["reqd_lines"]), ("TQM Capacity", vals["tqm_capacity"]), ("TQM", vals["tqm"]), ("ExcelRow", float(row_num))]:
            n[packintqm_key(line, metric)] = float(value)

    def line_mc(line: str) -> float:
        return float(helper_lookup[line]["reqd_lines"])

    def tqm_val(line: str) -> float:
        return float(helper_lookup[line]["tqm"])

    smart_lines = line_mc("Smart Line")
    ina_lines = line_mc("INA")
    chen_lines = line_mc("Manual (Chenille)")
    cotton_lines = line_mc("Manual (Cotton)")
    total_lines = smart_lines + ina_lines + chen_lines + cotton_lines
    dry_tqm = tqm_val("Smart Line")
    chen_tqm = tqm_val("Manual (Chenille)")
    cotton_tqm = tqm_val("Manual (Cotton)")

    draft_rows = []

    def add_draft_row(sr_no: int, section: str, dept: str, designation: str, machine_count: float, workload: str, formulas: str, scientific: float, remarks: str = ""):
        idx = _find_row_index(state["master_df"], section, dept, designation)
        if idx is None:
            return
        base = state["master_df"].iloc[idx].copy()
        row = {col: base[col] for col in state["master_df"].columns if col not in ["row_order", "row_id"]}
        row["Sr_No"] = sr_no
        row["Machine_Count"] = float(machine_count)
        row["Workload"] = workload
        row["Formulas"] = formulas
        row["BE_Scientific_Manpower"] = float(scientific)
        row["Remarks"] = remarks or row.get("Remarks", "")
        row["BE_Final_Manpower"] = float(Decimal(str(scientific)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        draft_rows.append(row)
        _update_row_direct(state, section, dept, designation, machine_count=machine_count, formula=formulas, scientific=scientific)

    line_specs = [
        (1, "Smart Line", "Loading", 1), (2, "Smart Line", "Tailor", 3), (3, "Smart Line", "Finisher", 6),
        (4, "Smart Line", "Hot Air", 2), (5, "Smart Line", "UL & AC", 1), (6, "Smart Line", "Gunner", 1), (7, "Smart Line", "Poly Packer", 4),
        (8, "INA", "Loading", 1), (9, "INA", "Tailor", 3), (10, "INA", "Finisher", 6),
        (11, "INA", "Hot Air", 2), (12, "INA", "UL & AC", 1), (13, "INA", "Gunner", 1), (14, "INA", "Poly Packer", 4),
        (15, "Manual (Chenille)", "Loading", 1), (16, "Manual (Chenille)", "Tailor", 1), (17, "Manual (Chenille)", "Finisher", 2),
        (18, "Manual (Chenille)", "Hot Air", 1), (19, "Manual (Chenille)", "UL & AC", 0), (20, "Manual (Chenille)", "Gunner", 1), (21, "Manual (Chenille)", "Poly Packer", 4),
        (22, "Manual (Cotton)", "Loading", 1), (23, "Manual (Cotton)", "Tailor", 2), (24, "Manual (Cotton)", "Finisher", 3),
        (25, "Manual (Cotton)", "Hot Air", 1), (26, "Manual (Cotton)", "UL & AC", 1), (27, "Manual (Cotton)", "Gunner", 1), (28, "Manual (Cotton)", "Poly Packer", 4),
    ]
    remarks_map = {"Smart Line": "Drylon", "INA": "Drylon", "Manual (Chenille)": "Chenille", "Manual (Cotton)": "Cotton"}
    for sr_no, dept, designation, mult in line_specs:
        mc = line_mc(dept)
        scientific = mc * mult * 3
        noun = "person"
        if designation == "Tailor":
            noun = "tailor"
        elif designation == "Finisher":
            noun = "finisher"
        workload = f"{mult} {noun}/line/shift"
        formulas = f"({fmt1(mc)}*{mult})*3"
        add_draft_row(sr_no, "Packing  Line MP", dept, designation, mc, workload, formulas, scientific, remarks_map[dept])

    sum_lines_formula = f"SUM({fmt1(smart_lines)}+{fmt1(ina_lines)}+{fmt1(chen_lines)}+{fmt1(cotton_lines)})"
    sum_lines_scientific = total_lines * 3
    add_draft_row(29, "Packing Support MP", "Packing Support", "IMS", 1.0, "sum of required lines", sum_lines_formula, sum_lines_scientific)
    add_draft_row(30, "Packing Support MP", "Packing Support", "Material Handler", 1.0, "4 person/shift", "4*3", 12.0)
    add_draft_row(31, "Packing Support MP", "Packing Support", "Line Jobber", 1.0, "sum of required lines", f"{sum_lines_formula}*3", sum_lines_scientific)
    ceil_half = math.ceil(total_lines / 2.0) * 3
    add_draft_row(32, "Packing Support MP", "Packing Support", "Rework (Stain/Coating)", 1.0, "half of total lines", "ROUNDUP(SUM(lines)/2,0)*3", ceil_half)
    add_draft_row(33, "Packing Support MP", "Packing Support", "Mender", 1.0, "half of total lines", "ROUNDUP(SUM(lines)/2,0)*3", ceil_half)
    add_draft_row(34, "Packing Support MP", "Packing Support", "Carton Pkg", 1.0, "3 x total required lines", "SUM(lines)*3*3", total_lines * 9)
    add_draft_row(35, "Packing Support MP", "Packing Support", "Carton Pkg jobber", 1.0, "half of total lines", "ROUNDUP(SUM(lines)/2,0)*3", ceil_half)

    fixed_support = {
        36: ("Packing Support", "LO packing", 1.0, "ROUNDUP(4/3,0) person/shift", "ROUNDUP(4/3,0)*3", math.ceil(4 / 3.0) * 3),
        37: ("Packing Support", "Carving/ Color Cut", 1.0, "7 person/shift", "7*3", 21.0),
        38: ("Packing Support", "DEO", 1.0, "2 person/shift", "2*3", 6.0),
        39: ("Packing Support", "Metal Detector", 1.0, "6 person/shift", "6*3", 18.0),
        40: ("Packing Support", "Down Grade", 1.0, "6 person/shift", "6*3", 18.0),
        41: ("Packing Support", "DG Jobber", 1.0, "1 person/shift", "1*3", 3.0),
        42: ("Packing Support", "House Keeping", 1.0, "2 person/shift", "2*3", 6.0),
        43: ("Packing Hot Melt", "Hot Melt Operator", 1.0, "6 person/shift", "6*3", 18.0),
        44: ("Packing Support", "Shortfall", 1.0, "4 person/shift", "4*3", 12.0),
        45: ("Packing Support", "Inspection", 1.0, "4 person/day", "4", 4.0),
    }
    for sr_no, spec in fixed_support.items():
        dept, desig, mc, workload, formulas, scientific = spec
        add_draft_row(sr_no, "Packing Support MP", dept, desig, mc, workload, formulas, scientific)

    chen_scientific = ((chen_req / 3.0) / 600.0) * 3.0
    add_draft_row(46, "Packing Support MP", "Packing Support", "Chenille Preparation (Only Sewing Line)", 1.0, "(Chenille Req/Day/3)/600", f"(({fmt_req(chen_req)}/3)/600)*3", chen_scientific)

    tqm_total_drylon_lines = smart_lines + ina_lines
    add_draft_row(47, "TQM", "Drylon TQM", "TQM Per Day", dry_tqm, "ROUNDUP(TQM*Reqd.Lines,0) per shift", f"ROUNDUP(({fmt1(dry_tqm)}*{fmt1(tqm_total_drylon_lines)}),0)*3", math.ceil(dry_tqm * tqm_total_drylon_lines) * 3, "Drylon")
    add_draft_row(48, "TQM", "Drylon TQM", "Poly PK AQL", dry_tqm, "4 person/shift", "4*3", 12.0, "Drylon")
    add_draft_row(49, "TQM", "Drylon TQM", "Carton AQL", dry_tqm, "5 person/shift", "5*3", 15.0, "Drylon")
    add_draft_row(50, "TQM", "Drylon TQM", "Carton DEO", dry_tqm, "2 person/shift", "2*3", 6.0, "Drylon")
    add_draft_row(52, "TQM", "Chenille TQM", "TQM Per Day", chen_tqm, "ROUNDUP(TQM*Reqd.Lines,0) per shift", f"ROUNDUP(({fmt1(chen_tqm)}*{fmt1(chen_lines)}),0)*3", math.ceil(chen_tqm * chen_lines) * 3, "Chenille")
    add_draft_row(53, "TQM", "Chenille TQM", "Poly PK AQL", chen_tqm, "2 person/shift", "2*3", 6.0, "Chenille")
    add_draft_row(54, "TQM", "Chenille TQM", "Carton AQL", chen_tqm, "1 person/shift", "1*3", 3.0, "Chenille")
    add_draft_row(55, "TQM", "Chenille TQM", "Carton DEO", chen_tqm, "1 person/shift", "1*3", 3.0, "Chenille")
    add_draft_row(56, "TQM", "Cotton TQM", "TQM Per Day", cotton_tqm, "ROUNDUP(TQM*Reqd.Lines,0) per shift", f"ROUNDUP(({fmt1(cotton_tqm)}*{fmt1(cotton_lines)}),0)*3", math.ceil(cotton_tqm * cotton_lines) * 3, "Cotton")
    add_draft_row(57, "TQM", "Cotton TQM", "Poly PK AQL", cotton_tqm, "1 person/shift", "1*3", 3.0, "Cotton")
    add_draft_row(58, "TQM", "Cotton TQM", "Carton AQL", cotton_tqm, "0 person/shift", "0", 0.0, "Cotton")
    add_draft_row(59, "TQM", "Cotton TQM", "Carton DEO", cotton_tqm, "0 person/shift", "0", 0.0, "Cotton")

    other_support_rows = [
        (60, 'Dyeing', 1.0, '1 person/shift', '1*3', 3.0),
        (61, 'Coating', 1.0, '1 person/shift', '1*3', 3.0),
        (62, 'Che Spng', 1.0, '1 person/shift', '1*3', 3.0),
        (63, 'MT', 1.0, '1 person/2 shifts', '1*2', 2.0),
        (64, 'TT', 1.0, '1 person/1 shift', '1*1', 1.0),
        (65, 'Sample', 1.0, '1 person/shift', '1*3', 3.0),
        (66, 'Lab', 2.0, '2 person/shift', '2*3', 6.0),
        (67, 'Inspection', 1.0, '1 person/shift', '1*3', 3.0),
        (68, 'Cut', 2.0, '2 person/2 shifts', '2*2', 4.0),
        (69, 'Piping', 1.0, '1 person/2 shifts', '1*2', 2.0),
        (70, 'TQM Line Jobber', 1.0, '1 person/shift', '1*3', 3.0),
        (71, 'In-coming', 1.0, '1 person/shift', '1*3', 3.0),
    ]
    for sr_no, desig, mc, workload, formulas, scientific in other_support_rows:
        add_draft_row(sr_no, 'TQM Other Support', 'Other Support', desig, mc, workload, formulas, scientific)

    draft_df = pd.DataFrame(draft_rows)
    if not draft_df.empty:
        draft_df["row_order"] = range(len(draft_df))
        draft_df["row_id"] = [f"temp.packintqm.sr_{i}" for i in range(1, len(draft_df) + 1)]
    state["packing_tqm_draft_calc_df"] = draft_df

def sync_frames(state: dict) -> None:
    n = state["nodes"]
    for i, r in state["ppc_df"].iterrows():
        state["ppc_df"].at[i, "Asking_Rate_Per_Day"] = n[ppc_key(r["Main_Group"], r["Sub_Group"], r["Subcategory"])]
    for i, r in state["capacity_df"].iterrows():
        for metric in ["actual_pcs_per_day", "actual_mtr_per_day", "actual_lac_sqm_per_month"]:
            state["capacity_df"].at[i, metric] = n[capacity_key(r["location"], metric)]
    for i, r in state["coating_df"].iterrows():
        state["coating_df"].at[i, "Value"] = n[coating_key(r["Parameter"], r["Material"])]
    for i, r in state["cs_df"].iterrows():
        state["cs_df"].at[i, "Value"] = n[cs_key(r["Section"], r["Process"], r["Metric"])]
    if not state["hydro_df"].empty:
        for col in state["hydro_df"].columns:
            if col == "row_order":
                continue
            state["hydro_df"].at[0, col] = n[hydro_key(col)]


def rebuild_linked_master_rows(state: dict) -> None:
    for row_id in COATING_ROWS + CUT_AND_SEW_ROWS + DYEING_ROWS:
        rebuild_master_row(state, row_id)
