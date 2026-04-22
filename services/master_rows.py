from __future__ import annotations
import math
from decimal import Decimal, ROUND_HALF_UP

def transform(value: float, mode: str) -> float:
    if mode == "round":
        return float(round(value))
    if mode == "ceil":
        return float(math.ceil(value))
    if mode == "floor":
        return float(math.floor(value))
    if mode == "divide_3_ceil":
        return float(math.ceil(value / 3.0))
    if mode == "divide_3_round":
        return float(round(value / 3.0))
    return float(value)

def fmt_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")

def get_source_value(state: dict, node_key: str | None, default: float) -> float:
    if not node_key:
        return float(default)
    return float(state["nodes"].get(node_key, default))

def build_formula(rule, machine_value: float) -> str:
    if not rule.formula_template:
        return ""
    return rule.formula_template.replace("{mc}", fmt_number(machine_value))

def scientific_value(rule, machine_value: float, current: float) -> float:
    if rule.scientific_type == "mul":
        return machine_value * float(rule.scientific_params["a"]) * float(rule.scientific_params["b"])
    if rule.scientific_type == "div":
        divisor = float(rule.scientific_params["div"])
        if abs(divisor) < 1e-9:
            return 0.0
        return (machine_value / divisor) * float(rule.scientific_params["b"])
    return float(rule.scientific_params.get("value", current))

def excel_round(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def default_final(rule, scientific: float) -> float:
    if rule.default_final_rule == "round_up":
        return float(math.ceil(scientific))
    return excel_round(scientific)

def rebuild_master_row(state: dict, row_id: str) -> None:
    idx = state["master_index"][row_id]
    row = state["master_df"].iloc[idx]
    rule = state["row_rules"][row_id]
    overrides = state["overrides"][row_id]
    machine_value = float(row["Machine_Count"])
    if rule.machine_source and not overrides["machine"]:
        machine_value = transform(get_source_value(state, rule.machine_source, machine_value), rule.machine_transform)
        state["master_df"].at[idx, "Machine_Count"] = machine_value
    formula_machine = machine_value
    if rule.formula_source:
        transform_name = rule.formula_transform if rule.formula_transform != "same" else rule.machine_transform
        formula_machine = transform(get_source_value(state, rule.formula_source, machine_value), transform_name)
    scientific_machine = machine_value
    if rule.scientific_source:
        transform_name = rule.scientific_transform if rule.scientific_transform != "same" else rule.machine_transform
        scientific_machine = transform(get_source_value(state, rule.scientific_source, machine_value), transform_name)
    state["master_df"].at[idx, "Formulas"] = build_formula(rule, formula_machine)
    scientific = scientific_value(rule, scientific_machine, float(row["BE_Scientific_Manpower"]))
    state["master_df"].at[idx, "BE_Scientific_Manpower"] = scientific
    if not overrides["be_final"]:
        state["master_df"].at[idx, "BE_Final_Manpower"] = default_final(rule, scientific)

def apply_master_edit(state: dict, row_id: str, field_name: str, new_value) -> None:
    idx = state["master_index"][row_id]
    state["master_df"].at[idx, field_name] = new_value
    if field_name == "Machine_Count":
        state["overrides"][row_id]["machine"] = True
        rebuild_master_row(state, row_id)
    elif field_name == "BE_Final_Manpower":
        state["overrides"][row_id]["be_final"] = True
