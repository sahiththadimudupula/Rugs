from __future__ import annotations
import re
from dataclasses import dataclass
from core.sheet_parser import slugify

@dataclass
class RowRule:
    row_id: str
    machine_source: str | None = None
    machine_transform: str = "identity"
    formula_template: str = ""
    formula_source: str | None = None
    formula_transform: str = "same"
    scientific_type: str = "fixed"
    scientific_params: dict | None = None
    scientific_source: str | None = None
    scientific_transform: str = "same"
    default_final_rule: str = "round"

def ppc_key(main_group: str, sub_group: str, subcategory: str) -> str:
    parts = ["ppc", slugify(main_group)]
    if sub_group:
        parts.append(slugify(sub_group))
    parts.append(slugify(subcategory))
    parts.append("value" if subcategory in {"MT (PC/Day)","TT (PC/Day)"} else "ask_rate")
    return ".".join(parts)

def capacity_key(location: str, metric: str) -> str:
    return f"capacity.{slugify(location)}.{metric}"

def coating_key(parameter: str, material: str) -> str:
    return f"coating.{slugify(parameter)}.{slugify(material)}"

def cs_key(section: str, process: str, metric: str) -> str:
    return f"cs.{slugify(section)}.{slugify(process)}.{slugify(metric)}"

def hydro_key(column_name: str) -> str:
    return f"hydro.{slugify(column_name)}.value"

def init_nodes(parsed: dict) -> dict[str, float]:
    nodes: dict[str, float] = {}
    for _, r in parsed["ppc_df"].iterrows():
        nodes[ppc_key(r["Main_Group"], r["Sub_Group"], r["Subcategory"])] = float(r["Asking_Rate_Per_Day"])
    for _, r in parsed["capacity_df"].iterrows():
        for metric in ["avg_area_per_piece","reference_pcs_per_day","reference_mtr_per_day","reference_lac_sqm_per_month","actual_pcs_per_day","actual_mtr_per_day","actual_lac_sqm_per_month"]:
            nodes[capacity_key(r["location"], metric)] = float(r[metric])
    for _, r in parsed["coating_df"].iterrows():
        nodes[coating_key(r["Parameter"], r["Material"])] = float(r["Value"])
    for _, r in parsed["cs_df"].iterrows():
        nodes[cs_key(r["Section"], r["Process"], r["Metric"])] = float(r["Value"])
    if not parsed["hydro_df"].empty:
        for col in parsed["hydro_df"].columns:
            if col == "row_order":
                continue
            nodes[hydro_key(col)] = float(parsed["hydro_df"].at[0, col])
    nodes["cs.custom.ims_checker.machine_count"] = 0.0
    return nodes

def parse_generic_row_rule(row) -> RowRule:
    formula = str(row["Formulas"] or "").strip()
    machine_count = float(row["Machine_Count"])
    rule = RowRule(row_id=row["row_id"], formula_template=formula, scientific_type="fixed", scientific_params={"value": float(row["BE_Scientific_Manpower"])})
    m1 = re.match(r"^\(([\d.\-]+)\*([\d.\-]+)\)\*([\d.\-]+)$", formula)
    if m1 and abs(float(m1.group(1)) - machine_count) < 1e-6:
        rule.formula_template = "({mc}*" + m1.group(2) + ")*" + m1.group(3)
        rule.scientific_type = "mul"
        rule.scientific_params = {"a": float(m1.group(2)), "b": float(m1.group(3))}
        return rule
    m2 = re.match(r"^\(([\d.\-]+)\/([\d.\-]+)\)\*([\d.\-]+)$", formula)
    if m2 and abs(float(m2.group(1)) - machine_count) < 1e-6:
        rule.formula_template = "({mc}/" + m2.group(2) + ")*" + m2.group(3)
        rule.scientific_type = "div"
        rule.scientific_params = {"div": float(m2.group(2)), "b": float(m2.group(3))}
        return rule
    m3 = re.match(r"^([\d.\-]+)\*([\d.\-]+)$", formula)
    if m3:
        rule.scientific_type = "fixed"
        rule.scientific_params = {"value": float(m3.group(1)) * float(m3.group(2))}
        return rule
    if formula in {"0", ""}:
        rule.scientific_type = "fixed"
        rule.scientific_params = {"value": 0.0}
    return rule

def build_row_rules(master_df) -> dict[str, RowRule]:
    rules = {row["row_id"]: parse_generic_row_rule(row) for _, row in master_df.iterrows()}
    total_node = coating_key("Machines Required", "Total")
    drylon_node = coating_key("Machines Required", "Drylon")
    def set_rule(row_id, **kwargs):
        base = rules[row_id]
        for k, v in kwargs.items():
            setattr(base, k, v)
    set_rule("master.coating.sr_1", machine_source=total_node, formula_source=total_node, scientific_source=total_node, formula_template="({mc}*2)*3", scientific_type="mul", scientific_params={"a": 2.0, "b": 3.0})
    set_rule("master.coating.sr_2", formula_template="(0*0)*3", scientific_type="fixed", scientific_params={"value": 0.0})
    for sr in [3, 4, 5, 6]:
        set_rule(f"master.coating.sr_{sr}", machine_source=drylon_node, formula_source=total_node, scientific_source=total_node, formula_template="({mc}*1)*2.15", scientific_type="mul", scientific_params={"a": 1.0, "b": 2.15}, default_final_rule="round_up")
    for sr, mult in {7: 2, 8: 1, 9: 2, 10: 1, 11: 3, 12: 3}.items():
        set_rule(f"master.coating.sr_{sr}", machine_source=total_node, formula_source=total_node, scientific_source=total_node, formula_template=f"({{mc}}*{mult})*3", scientific_type="mul", scientific_params={"a": float(mult), "b": 3.0})
    cut_map = {
        1:(cs_key("Machine","Length Cutting M/C","Total M/C Reqd"), "round"),
        2:(cs_key("Machine","Length Cutting M/C","Total M/C Reqd"), "round"),
        3:(cs_key("Machine","Length Cutting M/C","Total M/C Reqd"), "round"),
        4:(cs_key("Machine","Length Over edging(Rugs)","Total M/C Reqd"), "ceil"),
        6:(cs_key("Machine","Shape cutting M/C","Total M/C Reqd"), "ceil"),
        7:(cs_key("Machine","Shape cutting M/C","Total M/C Reqd"), "ceil"),
        8:(cs_key("Machine","Shape cutting M/C","Total M/C Reqd"), "ceil"),
        9:(cs_key("Machine","Cross cutting M/C","Total M/C Reqd"), "round"),
        11:(cs_key("Machine","Printed / Manual cutting","Total M/C Reqd"), "divide_3_ceil"),
        19:(cs_key("Machine","Tape Binding","Total M/C Reqd"), "round"),
        20:(cs_key("Machine","Bartack","Total M/C Reqd"), "round"),
        23:(cs_key("Machine","Over edging for Rugs","Total M/C Reqd"), "round"),
    }
    for sr, (source, transform) in cut_map.items():
        set_rule(f"master.cut_and_sew.sr_{sr}", machine_source=source, machine_transform=transform, formula_source=source, formula_transform=transform, scientific_source=source, scientific_transform=transform)
    set_rule("master.cut_and_sew.sr_24", machine_source="cs.custom.ims_checker.machine_count", formula_source="cs.custom.ims_checker.machine_count", scientific_source="cs.custom.ims_checker.machine_count")
    set_rule("master.dyeing.sr_10", machine_source=hydro_key("Total M/c Req"), machine_transform="round", formula_source=hydro_key("Total M/c Req"), formula_transform="round", scientific_source=hydro_key("Total M/c Req"), scientific_transform="round")
    return rules

def init_manual_overrides(master_df) -> dict[str, dict[str, bool]]:
    return {row_id: {"machine": False, "be_final": False} for row_id in master_df["row_id"].tolist()}
