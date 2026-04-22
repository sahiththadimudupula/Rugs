from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from itertools import combinations
import itertools

import pandas as pd

from core.formatting import to_number, round_half_up
from calculations.capacity import LOCATION_COLUMN, ACTUAL_PCS_COLUMN

MACHINE_TYPE_EZM = "EZM"
MACHINE_TYPE_PADDLE = "Paddle"
MACHINE_TYPE_OTHER = "Other"

PRODUCT_DRYLON = "DRYLON"
PRODUCT_COTTON = "COTTON"
ALLOWED_MACHINE_TYPES = [MACHINE_TYPE_EZM, MACHINE_TYPE_PADDLE]
ALLOWED_SHORTAGE = 100
NEW_MACHINE_PREFIX = "new"


@dataclass(frozen=True)
class MachineRecord:
    machine_name: str
    machine_type: str
    production_rate: float


@dataclass(frozen=True)
class HalfCombination:
    total_production: float
    machine_count: int
    selected_indices: tuple[int, ...]


@dataclass
class MachineCombination:
    machine_ids: list[str]
    total_production: int
    machine_count: int
    gap: int
    new_machine_count: int


def get_machine_type(machine_name: str) -> str:
    normalized = str(machine_name).upper().strip()
    if normalized.startswith("EZM"):
        return MACHINE_TYPE_EZM
    if normalized.startswith("PD"):
        return MACHINE_TYPE_PADDLE
    return MACHINE_TYPE_OTHER


def build_ezm_paddle_master() -> pd.DataFrame:
    machine_rows = [
        {"MACHINE": "EZM-01", "CAPACITY": 120, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 943.03},
        {"MACHINE": "EZM-02", "CAPACITY": 120, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 943.03},
        {"MACHINE": "EZM-03", "CAPACITY": 120, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 943.03},
        {"MACHINE": "EZM-04", "CAPACITY": 120, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 943.03},
        {"MACHINE": "EZM-05", "CAPACITY": 120, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 943.03},
        {"MACHINE": "EZM-06", "CAPACITY": 120, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 943.03},
        {"MACHINE": "EZM-07", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 1728.90},
        {"MACHINE": "EZM-08", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 1728.90},
        {"MACHINE": "EZM-09", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 1728.90},
        {"MACHINE": "EZM-10", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 1728.90},
        {"MACHINE": "EZM-11", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 1728.90},
        {"MACHINE": "EZM012", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 1728.90},
        {"MACHINE": "PD-03", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 6417.87},
        {"MACHINE": "PD-04", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 6417.87},
        {"MACHINE": "PD-07", "CAPACITY": 750, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 4584.20},
        {"MACHINE": "PD-08", "CAPACITY": 750, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 4584.20},
        {"MACHINE": "PD-09", "CAPACITY": 500, "CHENILLE": 0.0, "COTTON": 0.0, "DRYLON": 3056.13},
        {"MACHINE": "EZM-12", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 441.94, "DRYLON": 0.0},
        {"MACHINE": "EZM-13", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 441.94, "DRYLON": 0.0},
        {"MACHINE": "EZM-14", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 441.94, "DRYLON": 0.0},
        {"MACHINE": "EZM-15", "CAPACITY": 220, "CHENILLE": 0.0, "COTTON": 441.94, "DRYLON": 0.0},
        {"MACHINE": "PD-01", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-02", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-05", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-06", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-10", "CAPACITY": 300, "CHENILLE": 0.0, "COTTON": 512.24, "DRYLON": 0.0},
        {"MACHINE": "PD-11", "CAPACITY": 300, "CHENILLE": 0.0, "COTTON": 512.24, "DRYLON": 0.0},
        {"MACHINE": "PD-12", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-13", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-14", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-15", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-16", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
        {"MACHINE": "PD-17", "CAPACITY": 1050, "CHENILLE": 0.0, "COTTON": 1792.85, "DRYLON": 0.0},
    ]
    table = pd.DataFrame(machine_rows)
    table["Machine_Type"] = table["MACHINE"].apply(get_machine_type)
    return table


def filter_product_machines(machine_master: pd.DataFrame, product_column: str) -> list[MachineRecord]:
    product_rows = machine_master[(machine_master[product_column] > 0) & (machine_master["Machine_Type"].isin(ALLOWED_MACHINE_TYPES))].copy()
    return [MachineRecord(row["MACHINE"], row["Machine_Type"], float(row[product_column])) for _, row in product_rows.iterrows()]


def generate_half_combinations(machine_records: list[MachineRecord]) -> list[HalfCombination]:
    result: list[HalfCombination] = []
    indices = list(range(len(machine_records)))
    for selection_size in range(len(machine_records) + 1):
        for selected_indices in combinations(indices, selection_size):
            total_production = sum(machine_records[index].production_rate for index in selected_indices)
            result.append(HalfCombination(total_production, selection_size, selected_indices))
    return result


def split_machine_records(machine_records: list[MachineRecord]) -> tuple[list[MachineRecord], list[MachineRecord]]:
    split_position = len(machine_records) // 2
    return machine_records[:split_position], machine_records[split_position:]


def build_second_half_lookup(second_half_combinations: list[HalfCombination]) -> tuple[list[float], dict[float, HalfCombination]]:
    best_by_total: dict[float, HalfCombination] = {}
    for combination_item in second_half_combinations:
        current_best = best_by_total.get(combination_item.total_production)
        if current_best is None or combination_item.machine_count < current_best.machine_count:
            best_by_total[combination_item.total_production] = combination_item
    sorted_totals = sorted(best_by_total.keys())
    return sorted_totals, best_by_total


def choose_better_solution(current_best, candidate_machine_count: int, candidate_total_production: float, target_production: float, candidate_indices: tuple[int, ...]):
    candidate_excess = candidate_total_production - target_production
    candidate_score = (candidate_machine_count, round(candidate_excess, 6), -round(candidate_total_production, 6), candidate_indices)
    if current_best is None or candidate_score < current_best:
        return candidate_score
    return current_best


def find_minimum_machine_solution(machine_records: list[MachineRecord], target_production: float) -> tuple[list[str], float]:
    if not machine_records:
        return [], 0.0
    first_half_records, second_half_records = split_machine_records(machine_records)
    first_half_combinations = generate_half_combinations(first_half_records)
    second_half_combinations = generate_half_combinations(second_half_records)
    second_half_totals, second_half_lookup = build_second_half_lookup(second_half_combinations)

    best_solution = None
    best_selected_indices: tuple[int, ...] = ()
    for first_half_combination in first_half_combinations:
        required_second_half_production = target_production - first_half_combination.total_production
        matched_position = bisect_left(second_half_totals, required_second_half_production)
        if matched_position >= len(second_half_totals):
            continue
        second_half_total = second_half_totals[matched_position]
        second_half_combination = second_half_lookup[second_half_total]
        combined_total = first_half_combination.total_production + second_half_combination.total_production
        combined_count = first_half_combination.machine_count + second_half_combination.machine_count
        combined_indices = first_half_combination.selected_indices + tuple(len(first_half_records) + index for index in second_half_combination.selected_indices)
        updated_solution = choose_better_solution(best_solution, combined_count, combined_total, target_production, combined_indices)
        if updated_solution != best_solution:
            best_solution = updated_solution
            best_selected_indices = combined_indices

    if best_solution is None:
        return [], 0.0
    selected_names = [machine_records[index].machine_name for index in best_selected_indices]
    return selected_names, best_solution[2]


def count_machine_types(machine_names: list[str]) -> dict[str, int]:
    ezm_count = sum(1 for name in machine_names if get_machine_type(name) == MACHINE_TYPE_EZM)
    paddle_count = sum(1 for name in machine_names if get_machine_type(name) == MACHINE_TYPE_PADDLE)
    return {MACHINE_TYPE_EZM: ezm_count, MACHINE_TYPE_PADDLE: paddle_count}


def build_selected_machine_dataframe(machine_master: pd.DataFrame, selected_machine_names: list[str], product_column: str) -> pd.DataFrame:
    selected_machine_set = set(selected_machine_names)
    selected_machine_table = machine_master[machine_master["MACHINE"].isin(selected_machine_set)].copy()
    if selected_machine_table.empty:
        return pd.DataFrame(columns=["MACHINE", "Machine_Type", product_column, "Selected_Production"])
    selected_machine_table["Selected_Production"] = selected_machine_table[product_column]
    return selected_machine_table[["MACHINE", "Machine_Type", product_column, "Selected_Production"]].sort_values(["Machine_Type", "MACHINE"])


def build_jet_machine_table() -> pd.DataFrame:
    machine_rows = [
        ["1", "Prod", 300, "65%", 195, "97%", "90%", 4.8, 5.00, 851, 2837, "Walmart"],
        ["2", "Prod", 300, "65%", 195, "97%", "90%", 4.8, 5.00, 851, 2837, "Walmart"],
        ["3", "Prod", 300, "65%", 195, "97%", "90%", 4.8, 5.00, 851, 2837, "Walmart"],
        ["4", "Prod", 300, "65%", 195, "97%", "90%", 4.8, 5.00, 851, 2837, "Walmart"],
        ["5A", "Prod", 150, "65%", 98, "97%", "90%", 4.8, 5.00, 426, 1419, "Walmart"],
        ["5B", "Prod", 150, "85%", 128, "100%", "90%", 6.0, 4.00, 459, 1530, "Target"],
        ["6", "Prod", 300, "85%", 255, "97%", "90%", 6.0, 4.00, 890, 1619, "Target"],
        ["7", "Prod", 405, "85%", 344, "97%", "90%", 6.0, 4.00, 1202, 2186, "Target"],
        ["8", "Prod", 600, "85%", 510, "97%", "90%", 4.8, 5.00, 2226, 4048, "Others"],
        ["new 1", "Prod", 300, "85%", 255, "100%", "90%", 4.5, 5.33, 1224, 2720, "ikea"],
        ["new 2A", "Prod", 300, "85%", 255, "97%", "90%", 4.5, 5.33, 1187, 2159, "ikea"],
        ["new 2B", "Prod", 600, "85%", 510, "97%", "90%", 6.0, 4.00, 1781, 3238, "Target"],
        ["new 2C", "Prod", 600, "85%", 510, "97%", "90%", 6.0, 4.00, 1781, 3238, "Target"],
        ["new 2D", "Prod", 600, "85%", 510, "97%", "90%", 6.0, 4.00, 1781, 3238, "Target"],
    ]
    columns = ["Sr. No.", "Type", "Capacity/batch", "Loadability", "Prod Capacity/batch", "RFT", "Eff", "Cycle Time", "Batches/day", "Prod/day Kgs", "Prod/day Pcs", "Buyer"]
    return pd.DataFrame(machine_rows, columns=columns)


def is_valid_combination(total_production: int, requirement: int) -> bool:
    return total_production >= requirement - ALLOWED_SHORTAGE


def is_new_machine(machine_id: str) -> bool:
    return machine_id.strip().lower().startswith(NEW_MACHINE_PREFIX)


def build_result(machine_group, requirement: int) -> MachineCombination:
    machine_ids = [machine_id for machine_id, _ in machine_group]
    total_production = sum(production for _, production in machine_group)
    new_machine_count = sum(is_new_machine(machine_id) for machine_id in machine_ids)
    return MachineCombination(machine_ids, total_production, len(machine_ids), total_production - requirement, new_machine_count)


def choose_closest_combination(current_best: MachineCombination | None, candidate: MachineCombination) -> MachineCombination:
    if current_best is None:
        return candidate
    current_gap = abs(current_best.gap)
    candidate_gap = abs(candidate.gap)
    if candidate_gap < current_gap:
        return candidate
    if candidate_gap > current_gap:
        return current_best
    if candidate.total_production > current_best.total_production:
        return candidate
    return current_best


def find_best_combination(machine_table: pd.DataFrame, requirement: int) -> MachineCombination | None:
    machine_options = list(zip(machine_table["Sr. No."], machine_table["Prod/day Pcs"]))
    for machine_count in range(1, len(machine_options) + 1):
        best_for_machine_count = None
        for machine_group in itertools.combinations(machine_options, machine_count):
            total_production = sum(production for _, production in machine_group)
            if not is_valid_combination(total_production, requirement):
                continue
            candidate = build_result(machine_group, requirement)
            best_for_machine_count = choose_closest_combination(best_for_machine_count, candidate)
        if best_for_machine_count is not None:
            return best_for_machine_count
    return None


def build_selected_jet_machine_table(machine_table: pd.DataFrame, result: MachineCombination | None) -> pd.DataFrame:
    if result is None:
        return pd.DataFrame(columns=machine_table.columns)
    selected_table = machine_table[machine_table["Sr. No."].isin(result.machine_ids)].copy()
    selected_table["selection_order"] = pd.Categorical(selected_table["Sr. No."], categories=result.machine_ids, ordered=True)
    return selected_table.sort_values("selection_order").drop(columns="selection_order")


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


def recalculate_dyeing_tables(asking_rate_table: pd.DataFrame, capacity_table: pd.DataFrame) -> dict[str, object]:
    drylon_target = get_asking_value(asking_rate_table, "Processing", "", "Process", "Drylon Washing")
    cotton_target = get_capacity_pcs(capacity_table, "Cotton-M/C Tufting") + get_capacity_pcs(capacity_table, "Cotton-Table Tufting")
    machine_master = build_ezm_paddle_master()

    drylon_selected_names, drylon_achieved = find_minimum_machine_solution(filter_product_machines(machine_master, PRODUCT_DRYLON), drylon_target)
    cotton_selected_names, cotton_achieved = find_minimum_machine_solution(filter_product_machines(machine_master, PRODUCT_COTTON), cotton_target)

    drylon_counts = count_machine_types(drylon_selected_names)
    cotton_counts = count_machine_types(cotton_selected_names)
    ezm_count = drylon_counts[MACHINE_TYPE_EZM] + cotton_counts[MACHINE_TYPE_EZM]
    paddle_count = drylon_counts[MACHINE_TYPE_PADDLE] + cotton_counts[MACHINE_TYPE_PADDLE]

    jet_requirement = round_half_up(get_capacity_pcs(capacity_table, "Chenille") * 1.05, 0)
    jet_table = build_jet_machine_table()
    jet_result = find_best_combination(jet_table, int(jet_requirement))
    jet_count = 0 if jet_result is None else jet_result.machine_count

    input_driver_df = pd.DataFrame({"Input": ["Drylon Target", "Cotton Target", "Jet Requirement"], "Value": [drylon_target, cotton_target, jet_requirement]})
    output_summary_df = pd.DataFrame({"Metric": ["EZM Count", "Paddle Count", "Jet Machine Count", "Drylon Achieved", "Cotton Achieved"], "Value": [ezm_count, paddle_count, jet_count, drylon_achieved, cotton_achieved]})
    drylon_selected_df = build_selected_machine_dataframe(machine_master, drylon_selected_names, PRODUCT_DRYLON)
    cotton_selected_df = build_selected_machine_dataframe(machine_master, cotton_selected_names, PRODUCT_COTTON)
    jet_selected_df = build_selected_jet_machine_table(jet_table, jet_result)

    summary_df = pd.concat([input_driver_df.rename(columns={"Input": "Metric"}), output_summary_df], ignore_index=True)

    return {
        "summary_df": summary_df,
        "input_driver_df": input_driver_df,
        "output_summary_df": output_summary_df,
        "drylon_selected_df": drylon_selected_df,
        "cotton_selected_df": cotton_selected_df,
        "jet_selected_df": jet_selected_df,
        "ezm_count": ezm_count,
        "paddle_count": paddle_count,
        "jet_count": jet_count,
        "drylon_achieved": drylon_achieved,
        "cotton_achieved": cotton_achieved,
        "drylon_selected": drylon_selected_names,
        "cotton_selected": cotton_selected_names,
        "jet_result": jet_result,
    }
