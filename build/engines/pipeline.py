from __future__ import annotations
from config.constants import *
from core.registries import ppc_key, capacity_key, coating_key, cs_key, hydro_key
from services.master_rows import rebuild_master_row

COATING_ROWS = [f"master.coating.sr_{n}" for n in range(1, 13)]
CUT_AND_SEW_ROWS = [f"master.cut_and_sew.sr_{n}" for n in [1,2,3,4,6,7,8,9,11,19,20,23,24]]
HYDRO_ROWS = ["master.dyeing.sr_10"]

def recalc_all(state: dict) -> None:
    recalc_ppc(state)
    recalc_capacity(state)
    recalc_coating(state)
    recalc_cs(state)
    recalc_hydro(state)
    sync_frames(state)
    rebuild_linked_master_rows(state)

def recalc_ppc(state: dict) -> None:
    n = state["nodes"]
    for _, r in state["ppc_df"].iterrows():
        n[ppc_key(r["Main_Group"], r["Sub_Group"], r["Subcategory"])] = float(r["Asking_Rate_Per_Day"])
    n["ppc.packing.grand_total.ask_rate"] = sum(n[k] for k in ["ppc.packing.carving.ask_rate","ppc.packing.chenile.ask_rate","ppc.packing.non_carving.ask_rate","ppc.packing.roll.ask_rate","ppc.packing.rugs.ask_rate"])
    n["ppc.c_and_s.overedging.overedging_total.ask_rate"] = sum(n[k] for k in ["ppc.c_and_s.overedging.drylon_washing.ask_rate","ppc.c_and_s.overedging.non_dyeing.ask_rate","ppc.c_and_s.overedging.tumble.ask_rate"])
    n["ppc.c_and_s.union.union_total.ask_rate"] = sum(n[k] for k in ["ppc.c_and_s.union.cotton_dyeing.ask_rate","ppc.c_and_s.union.drylon_washing.ask_rate","ppc.c_and_s.union.polyester_dyeing.ask_rate"])
    n["ppc.c_and_s.grand_total.ask_rate"] = n["ppc.c_and_s.overedging.overedging_total.ask_rate"] + n["ppc.c_and_s.union.union_total.ask_rate"]
    n["ppc.grey_issue.grand_total.ask_rate"] = sum(n[k] for k in ["ppc.grey_issue.cotton_dyeing.ask_rate","ppc.grey_issue.drylon_washing.ask_rate","ppc.grey_issue.non_dyeing.ask_rate","ppc.grey_issue.polyester_dyeing.ask_rate","ppc.grey_issue.tumble.ask_rate"])
    n["ppc.processing.mt_pc_day.value"] = 54.42 * 1.1 * 3.9
    n["ppc.processing.tt_pc_day.value"] = n["ppc.processing.cotton_dyeing.ask_rate"] - n["ppc.processing.mt_pc_day.value"]
    n["ppc.processing.grand_total.ask_rate"] = sum(n[k] for k in ["ppc.processing.cotton_dyeing.ask_rate","ppc.processing.drylon_washing.ask_rate","ppc.processing.polyester_dyeing.ask_rate"])
    n["ppc.coating.grand_total.ask_rate"] = n["ppc.coating.cotton.ask_rate"] + n["ppc.coating.foam.ask_rate"]
    n["ppc.machine_tufting.grand_total.ask_rate"] = sum(n[k] for k in ["ppc.machine_tufting.1_8_cut.ask_rate","ppc.machine_tufting.1_8_mlcl.ask_rate","ppc.machine_tufting.1_10_loop.ask_rate","ppc.machine_tufting.3_8_cut.ask_rate","ppc.machine_tufting.3_8_loop.ask_rate"])
    n["ppc.table_tufting.grand_total.ask_rate"] = n["ppc.table_tufting.1_4_rev.ask_rate"] + n["ppc.table_tufting.3_16_cut.ask_rate"]

def recalc_capacity(state: dict) -> None:
    n = state["nodes"]
    n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")] = n["ppc.processing.mt_pc_day.value"]
    n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")] = n["ppc.processing.tt_pc_day.value"]
    n[capacity_key("Chenille", "actual_pcs_per_day")] = n["ppc.packing.chenile.ask_rate"]
    n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")] = n["ppc.c_and_s.overedging.non_dyeing.ask_rate"] + n["ppc.c_and_s.overedging.tumble.ask_rate"]
    n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")] = n["ppc.packing.grand_total.ask_rate"] - n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")] - n[capacity_key("Chenille", "actual_pcs_per_day")] - n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")]
    locs = ["Cotton-M/C Tufting","Cotton-Table Tufting","Chenille","Bath Rugs (Wash)","Bath Rugs (Non- Wash with Tumble)"]
    for loc in locs:
        pcs = n[capacity_key(loc, "actual_pcs_per_day")]
        avg = n[capacity_key(loc, "avg_area_per_piece")]
        n[capacity_key(loc, "actual_mtr_per_day")] = (pcs * avg) / SQUARE_METER_DIVISOR
        n[capacity_key(loc, "actual_lac_sqm_per_month")] = (pcs * avg * DAYS_PER_MONTH) / 100000.0
    n[capacity_key("Total", "actual_pcs_per_day")] = sum(n[capacity_key(loc, "actual_pcs_per_day")] for loc in locs)
    n[capacity_key("Total", "actual_mtr_per_day")] = sum(n[capacity_key(loc, "actual_mtr_per_day")] for loc in locs)
    n[capacity_key("Total", "actual_lac_sqm_per_month")] = sum(n[capacity_key(loc, "actual_lac_sqm_per_month")] for loc in locs)

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
    def setv(sec, proc, met, val): n[cs_key(sec, proc, met)] = float(val)
    cotton_tt = n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")]
    cotton_mt = n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")]
    cotton_mt_mtr = n[capacity_key("Cotton-M/C Tufting", "actual_mtr_per_day")]
    dry_w = n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")]
    dry_w_mtr = n[capacity_key("Bath Rugs (Wash)", "actual_mtr_per_day")]
    dry_n = n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_pcs_per_day")]
    dry_n_mtr = n[capacity_key("Bath Rugs (Non- Wash with Tumble)", "actual_mtr_per_day")]
    chen = n[capacity_key("Chenille", "actual_pcs_per_day")]
    vals = {
        ("Production","Cotton Dyeing (TT)","Pcs/Day"): cotton_tt,
        ("Production","Cotton Dyeing (TT)","Pcs/Month"): cotton_tt * CS_DAYS_PER_MONTH,
        ("Production","Cotton Dyeing (TT)","Linear Mtr"): 0,
        ("Production","Cotton Dyeing (TT)","Union"): 0,
        ("Production","Cotton Dyeing (TT)","Mat"): 0,
        ("Production","Cotton Dyeing (TT)","Shape/Design"): 0,
        ("Production","Cotton Dyeing (TT)","Over Edging"): 0,
        ("Production","Cotton Dyeing (MT)","Pcs/Day"): cotton_mt,
        ("Production","Cotton Dyeing (MT)","Pcs/Month"): cotton_mt * CS_DAYS_PER_MONTH,
        ("Production","Cotton Dyeing (MT)","Linear Mtr"): cotton_mt_mtr,
        ("Production","Cotton Dyeing (MT)","Union"): cotton_mt,
        ("Production","Cotton Dyeing (MT)","Mat"): cotton_mt,
        ("Production","Cotton Dyeing (MT)","Shape/Design"): 0,
        ("Production","Cotton Dyeing (MT)","Over Edging"): 0,
        ("Production","Drylon (Washing)","Pcs/Day"): dry_w,
        ("Production","Drylon (Washing)","Pcs/Month"): dry_w * CS_DAYS_PER_MONTH,
        ("Production","Drylon (Washing)","Linear Mtr"): dry_w_mtr,
        ("Production","Drylon (Washing)","Union"): dry_w * 0.85,
        ("Production","Drylon (Washing)","Over Edging"): dry_w - (dry_w * 0.85),
        ("Production","Drylon (Washing)","Mat"): dry_w * 0.5,
        ("Production","Drylon (Washing)","Shape/Design"): 1000,
        ("Production","Drylon_Rugs (Non_Washing)","Pcs/Day"): dry_n,
        ("Production","Drylon_Rugs (Non_Washing)","Pcs/Month"): dry_n * CS_DAYS_PER_MONTH,
        ("Production","Drylon_Rugs (Non_Washing)","Linear Mtr"): dry_n_mtr,
        ("Production","Drylon_Rugs (Non_Washing)","Union"): 0,
        ("Production","Drylon_Rugs (Non_Washing)","Over Edging"): dry_n,
        ("Production","Drylon_Rugs (Non_Washing)","Shape/Design"): 7500,
        ("Production","Drylon_Rugs (Non_Washing)","Mat"): dry_n - 7500,
        ("Production","Carpet_Rolling","Pcs/Day"): 0,
        ("Production","Carpet_Rolling","Pcs/Month"): 0,
        ("Production","Carpet_Rolling","Linear Mtr"): 0,
        ("Production","Carpet_Rolling","Union"): 0,
        ("Production","Carpet_Rolling","Over Edging"): 0,
        ("Production","Carpet_Rolling","Mat"): 0,
        ("Production","Carpet_Rolling","Shape/Design"): 0,
        ("Production","Chenille","Pcs/Day"): chen,
        ("Production","Chenille","Pcs/Month"): chen * CS_DAYS_PER_MONTH,
        ("Production","Chenille","Linear Mtr"): 0,
        ("Production","Chenille","Union"): chen,
        ("Production","Chenille","Over Edging"): 0,
        ("Production","Chenille","Mat"): 0,
        ("Production","Chenille","Shape/Design"): 0,
    }
    for k, v in vals.items():
        setv(*k, v)
    def g(proc, met): return n[cs_key("Production", proc, met)]
    total_pcs_day = sum(g(p, "Pcs/Day") for p in ["Cotton Dyeing (TT)","Cotton Dyeing (MT)","Drylon (Washing)","Drylon_Rugs (Non_Washing)","Carpet_Rolling","Chenille"])
    total_pcs_mon = sum(g(p, "Pcs/Month") for p in ["Cotton Dyeing (TT)","Cotton Dyeing (MT)","Drylon (Washing)","Drylon_Rugs (Non_Washing)","Carpet_Rolling","Chenille"])
    total_lin = sum(g(p, "Linear Mtr") for p in ["Cotton Dyeing (TT)","Cotton Dyeing (MT)","Drylon (Washing)","Drylon_Rugs (Non_Washing)","Carpet_Rolling","Chenille"])
    total_union = sum(g(p, "Union") for p in ["Cotton Dyeing (TT)","Cotton Dyeing (MT)","Drylon (Washing)","Drylon_Rugs (Non_Washing)","Carpet_Rolling","Chenille"])
    total_over = sum(g(p, "Over Edging") for p in ["Cotton Dyeing (TT)","Cotton Dyeing (MT)","Drylon (Washing)","Drylon_Rugs (Non_Washing)","Carpet_Rolling","Chenille"])
    total_shape = sum(g(p, "Shape/Design") for p in ["Cotton Dyeing (TT)","Cotton Dyeing (MT)","Drylon (Washing)","Drylon_Rugs (Non_Washing)","Carpet_Rolling","Chenille"])
    setv("Production","Total Pcs","Pcs/Day", total_pcs_day)
    setv("Production","Total Pcs","Pcs/Month", total_pcs_mon)
    setv("Production","Total Pcs","Linear Mtr", total_lin)
    setv("Production","Total Pcs","Union", total_union)
    setv("Production","Total Pcs","Over Edging", total_over)
    setv("Production","Total Pcs","Mat", 28030)
    setv("Production","Total Pcs","Shape/Design", total_shape)
    total_sqm = n[capacity_key("Total", "actual_lac_sqm_per_month")]
    setv("Production","Total In SqMtr","Pcs/Day", total_sqm)
    setv("Production","Total In SqMtr","Pcs/Month", total_sqm * DAYS_PER_MONTH)
    setv("Production","Total In SqMtr","Shape/Design", total_pcs_day - chen - total_shape - 28030)
    existing_caps = {
        "Length Cutting M/C": 13 * 60 * 24 * 0.8 * 0.65,
        "Cross cutting M/C": 10 * 60 * 24 * 0.8,
        "Printed / Manual cutting": 750,
        "Shape cutting M/C": 14000,
        "Length Over edging(Rugs)": 7 * 60 * 24 * 0.82,
        "Length Over edging(carpet)": 6 * 60 * 24 * 0.82 / 1.7,
        "Tape Binding": 1300,
        "Over edging for Rugs": 1200,
        "Bartack": 3400,
        "Cross Over edging (carpet)": 5 * 60 * 24 * 0.82,
    }
    reqs = {
        "Length Cutting M/C": total_lin,
        "Cross cutting M/C": 28030,
        "Printed / Manual cutting": n[cs_key("Production","Total In SqMtr","Shape/Design")],
        "Shape cutting M/C": total_shape,
        "Length Over edging(Rugs)": g("Drylon (Washing)","Over Edging") + g("Drylon_Rugs (Non_Washing)","Over Edging"),
        "Length Over edging(carpet)": 0,
        "Tape Binding": total_union,
        "Over edging for Rugs": g("Drylon (Washing)","Over Edging") + g("Drylon_Rugs (Non_Washing)","Over Edging"),
        "Bartack": total_union + total_over,
        "Cross Over edging (carpet)": g("Carpet_Rolling","Over Edging"),
    }
    available = {"Length Cutting M/C": 1,"Cross cutting M/C": 5,"Printed / Manual cutting": 43,"Shape cutting M/C": 1,"Length Over edging(Rugs)": 2,"Length Over edging(carpet)": 0,"Tape Binding": 57,"Over edging for Rugs": 35,"Bartack": 26,"Cross Over edging (carpet)": 0}
    for proc, cap in existing_caps.items():
        setv("Machine", proc, "Existing Capacity/MC", cap)
        req = reqs[proc]
        setv("Machine", proc, "Requirements/day", req)
        total = 0 if abs(cap) < 1e-9 else req / cap
        setv("Machine", proc, "Total M/C Reqd", total)
        setv("Machine", proc, "Existing MCs available", available[proc])
        if proc != "Printed / Manual cutting":
            setv("Machine", proc, "New M/C Reqd", total - available[proc])
    setv("Machine","Over Lock","Total M/C Reqd", 8)
    setv("Machine","Over Lock","Existing MCs available", 3)
    setv("Machine","Over Lock","New M/C Reqd", 5)
    setv("Machine","Table Tufting (3/16)","Total M/C Reqd", n[cs_key("Machine","Tape Binding","Total M/C Reqd")] * 3 / 2)
    setv("Machine","Table Tufting (Reversable)","Total M/C Reqd", n[cs_key("Machine","Over edging for Rugs","Total M/C Reqd")] * 3 / 2)
    setv("Machine","Manual Overlock","Existing Capacity/MC", 1500)
    setv("Machine","Manual Overlock","Requirements/day", 47047)
    setv("Machine","Manual Overlock","Total M/C Reqd", 0)
    n["cs.custom.ims_checker.machine_count"] = (cotton_mt + dry_w + dry_n) / 7500.0

def recalc_hydro(state: dict) -> None:
    n = state["nodes"]
    n[hydro_key("Required Pcs")] = n[capacity_key("Cotton-M/C Tufting", "actual_pcs_per_day")] + n[capacity_key("Cotton-Table Tufting", "actual_pcs_per_day")] + n[capacity_key("Bath Rugs (Wash)", "actual_pcs_per_day")]
    n[hydro_key("Prod/mc/day (Kgs)")] = n[hydro_key("No. Of Batch")] * n[hydro_key("M/s Capacity Proposed")] * (n[hydro_key("Efficiency")] / 100.0)
    n[hydro_key("Pcs/day/mc")] = n[hydro_key("Prod/mc/day (Kgs)")] * HYDRO_PCS_CONVERSION
    prod = n[hydro_key("Prod/mc/day (Kgs)")]
    n[hydro_key("Total M/c Req")] = 0.0 if abs(prod) < 1e-9 else round(n[hydro_key("Required Pcs")] / prod)

def sync_frames(state: dict) -> None:
    for i, r in state["ppc_df"].iterrows():
        state["ppc_df"].at[i, "Asking_Rate_Per_Day"] = state["nodes"][ppc_key(r["Main_Group"], r["Sub_Group"], r["Subcategory"])]
    for i, r in state["capacity_df"].iterrows():
        for metric in ["avg_area_per_piece","reference_pcs_per_day","reference_mtr_per_day","reference_lac_sqm_per_month","actual_pcs_per_day","actual_mtr_per_day","actual_lac_sqm_per_month"]:
            state["capacity_df"].at[i, metric] = state["nodes"][capacity_key(r["location"], metric)]
    for i, r in state["coating_df"].iterrows():
        state["coating_df"].at[i, "Value"] = state["nodes"][coating_key(r["Parameter"], r["Material"])]
    for i, r in state["cs_df"].iterrows():
        state["cs_df"].at[i, "Value"] = state["nodes"][cs_key(r["Section"], r["Process"], r["Metric"])]
    if not state["hydro_df"].empty:
        for col in [c for c in state["hydro_df"].columns if c != "row_order"]:
            state["hydro_df"].at[0, col] = state["nodes"][hydro_key(col)]

def rebuild_linked_master_rows(state: dict) -> None:
    for row_id in COATING_ROWS + CUT_AND_SEW_ROWS + HYDRO_ROWS:
        if row_id in state["row_rules"]:
            rebuild_master_row(state, row_id)
