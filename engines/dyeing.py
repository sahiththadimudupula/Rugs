from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from itertools import combinations
import pandas as pd

MACHINE_TYPE_EZM = "EZM"
MACHINE_TYPE_PADDLE = "Paddle"
ALLOWED_MACHINE_TYPES = [MACHINE_TYPE_EZM, MACHINE_TYPE_PADDLE]
PRODUCT_DRYLON = "DRYLON"
PRODUCT_COTTON = "COTTON"
SUMMARY_ROWS = ["Drylon", "Cotton", "Total", "Avail", "Short/Excess"]
DEFAULT_ALLOWED_SHORTAGE = 100.0
JET_SELECTED_OPTION = "option1"


@dataclass(frozen=True)
class ProductTargets:
    drylon: float
    cotton: float


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


def build_default_dye_inputs_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Input": "Drylon Target", "key": "drylon_target", "Value": 0.0, "Source": "CS -> Drylon (Washing) Pcs/Day"},
            {"Input": "Cotton Target", "key": "cotton_target", "Value": 0.0, "Source": "Capacity -> Cotton-M/C + Cotton-Table PCS/DAY"},
            {"Input": "Jet Requirement", "key": "jet_requirement", "Value": 0.0, "Source": "Capacity -> Chenille PCS/DAY * 1.05"},
            {"Input": "Allowed Shortage", "key": "allowed_shortage", "Value": DEFAULT_ALLOWED_SHORTAGE, "Source": "Jet Dyeing scenario input"},
        ]
    )


def get_machine_type(machine_name: str) -> str:
    normalized_name = str(machine_name).upper().strip()
    if normalized_name.startswith("EZM"):
        return MACHINE_TYPE_EZM
    if normalized_name.startswith("PD"):
        return MACHINE_TYPE_PADDLE
    return "Other"


def build_default_ezm_paddle_df() -> pd.DataFrame:
    machine_data = [
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
    df = pd.DataFrame(machine_data)
    df["Machine_Type"] = df["MACHINE"].apply(get_machine_type)
    return df


def build_default_jet_df() -> pd.DataFrame:
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


def filter_product_machines(machine_master: pd.DataFrame, product_column: str) -> list[MachineRecord]:
    product_rows = machine_master[(machine_master[product_column] > 0) & (machine_master["Machine_Type"].isin(ALLOWED_MACHINE_TYPES))].copy()
    return [MachineRecord(row["MACHINE"], row["Machine_Type"], float(row[product_column])) for _, row in product_rows.iterrows()]


def generate_half_combinations(machine_records: list[MachineRecord]) -> list[HalfCombination]:
    combos: list[HalfCombination] = []
    record_indices = list(range(len(machine_records)))
    for selection_size in range(len(machine_records) + 1):
        for selected_index_tuple in combinations(record_indices, selection_size):
            total_production = sum(machine_records[index].production_rate for index in selected_index_tuple)
            combos.append(HalfCombination(total_production, selection_size, selected_index_tuple))
    return combos


def split_machine_records(machine_records: list[MachineRecord]) -> tuple[list[MachineRecord], list[MachineRecord]]:
    split_position = len(machine_records) // 2
    return machine_records[:split_position], machine_records[split_position:]


def build_second_half_lookup(second_half_combinations: list[HalfCombination]) -> tuple[list[float], dict[float, HalfCombination]]:
    best_by_total: dict[float, HalfCombination] = {}
    for combo in second_half_combinations:
        current = best_by_total.get(combo.total_production)
        if current is None or combo.machine_count < current.machine_count:
            best_by_total[combo.total_production] = combo
    return sorted(best_by_total.keys()), best_by_total


def choose_better_solution(current_best, candidate_machine_count, candidate_total_production, target_production, candidate_indices):
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
    for first_combo in first_half_combinations:
        required_second = target_production - first_combo.total_production
        matched_position = bisect_left(second_half_totals, required_second)
        if matched_position >= len(second_half_totals):
            continue
        second_total = second_half_totals[matched_position]
        second_combo = second_half_lookup[second_total]
        combined_total = first_combo.total_production + second_combo.total_production
        combined_count = first_combo.machine_count + second_combo.machine_count
        combined_indices = first_combo.selected_indices + tuple(len(first_half_records) + idx for idx in second_combo.selected_indices)
        updated = choose_better_solution(best_solution, combined_count, combined_total, target_production, combined_indices)
        if updated != best_solution:
            best_solution = updated
            best_selected_indices = combined_indices
    if best_solution is None:
        return [], 0.0
    return [machine_records[index].machine_name for index in best_selected_indices], best_solution[2]


def build_selected_machine_dataframe(machine_master: pd.DataFrame, selected_machine_names: list[str], product_column: str) -> pd.DataFrame:
    selected_set = set(selected_machine_names)
    table = machine_master[machine_master["MACHINE"].isin(selected_set)].copy()
    if table.empty:
        return pd.DataFrame(columns=["MACHINE", "Machine_Type", product_column, "Machine_count", "Selected_Production"])
    table["Machine_count"] = 1
    table["Selected_Production"] = table[product_column]
    return table[["MACHINE", "Machine_Type", product_column, "Machine_count", "Selected_Production"]].sort_values(["Machine_Type", "MACHINE"])


def count_selected_machines_by_type(selected_machine_table: pd.DataFrame) -> pd.Series:
    if selected_machine_table.empty:
        return pd.Series([0, 0], index=[MACHINE_TYPE_EZM, MACHINE_TYPE_PADDLE], dtype=int)
    return selected_machine_table.groupby("Machine_Type")["Machine_count"].sum().reindex(ALLOWED_MACHINE_TYPES, fill_value=0).astype(int)


def count_available_machines_by_type(machine_master: pd.DataFrame) -> pd.Series:
    return machine_master[machine_master["Machine_Type"].isin(ALLOWED_MACHINE_TYPES)].groupby("Machine_Type")["MACHINE"].count().reindex(ALLOWED_MACHINE_TYPES, fill_value=0).astype(int)


def build_final_summary_table(available_machine_count: pd.Series, drylon_machine_count: pd.Series, cotton_machine_count: pd.Series) -> pd.DataFrame:
    total_machine_count = drylon_machine_count + cotton_machine_count
    short_or_excess_machine_count = available_machine_count - total_machine_count
    return pd.DataFrame({
        "MC": SUMMARY_ROWS,
        MACHINE_TYPE_EZM: [int(drylon_machine_count[MACHINE_TYPE_EZM]), int(cotton_machine_count[MACHINE_TYPE_EZM]), int(total_machine_count[MACHINE_TYPE_EZM]), int(available_machine_count[MACHINE_TYPE_EZM]), int(short_or_excess_machine_count[MACHINE_TYPE_EZM])],
        MACHINE_TYPE_PADDLE: [int(drylon_machine_count[MACHINE_TYPE_PADDLE]), int(cotton_machine_count[MACHINE_TYPE_PADDLE]), int(total_machine_count[MACHINE_TYPE_PADDLE]), int(available_machine_count[MACHINE_TYPE_PADDLE]), int(short_or_excess_machine_count[MACHINE_TYPE_PADDLE])],
    })


def build_production_summary_table(targets: ProductTargets, achieved_drylon_production: float, achieved_cotton_production: float) -> pd.DataFrame:
    return pd.DataFrame({
        "Product": ["Drylon", "Cotton"],
        "Target_Production": [targets.drylon, targets.cotton],
        "Achieved_Production": [achieved_drylon_production, achieved_cotton_production],
        "Excess_or_Short": [round(achieved_drylon_production - targets.drylon, 4), round(achieved_cotton_production - targets.cotton, 4)],
    })


def optimize_product_selection(machine_master: pd.DataFrame, product_column: str, target_production: float) -> tuple[pd.DataFrame, float]:
    records = filter_product_machines(machine_master, product_column)
    selected_names, achieved_production = find_minimum_machine_solution(records, target_production)
    selected_table = build_selected_machine_dataframe(machine_master, selected_names, product_column)
    return selected_table, achieved_production


def calculate_ezm_paddle(machine_master: pd.DataFrame, targets: ProductTargets) -> dict:
    machine_master = machine_master.copy()
    machine_master["Machine_Type"] = machine_master["MACHINE"].apply(get_machine_type)
    drylon_selected, achieved_drylon = optimize_product_selection(machine_master, PRODUCT_DRYLON, targets.drylon)
    cotton_selected, achieved_cotton = optimize_product_selection(machine_master, PRODUCT_COTTON, targets.cotton)
    available_count = count_available_machines_by_type(machine_master)
    drylon_count = count_selected_machines_by_type(drylon_selected)
    cotton_count = count_selected_machines_by_type(cotton_selected)
    final_summary = build_final_summary_table(available_count, drylon_count, cotton_count)
    production_summary = build_production_summary_table(targets, achieved_drylon, achieved_cotton)
    return {
        "final_summary_table": final_summary,
        "production_summary_table": production_summary,
        "drylon_selected_table": drylon_selected,
        "cotton_selected_table": cotton_selected,
        "paddle_count": int(final_summary.loc[final_summary["MC"] == "Total", MACHINE_TYPE_PADDLE].iloc[0]),
        "ezm_count": int(final_summary.loc[final_summary["MC"] == "Total", MACHINE_TYPE_EZM].iloc[0]),
    }


def is_valid_combination(total_production: int, requirement: int, allowed_shortage: int) -> bool:
    return total_production >= requirement - allowed_shortage


def is_new_machine(machine_id: str) -> bool:
    return machine_id.strip().lower().startswith("new")


def build_result(machine_group, requirement: int) -> MachineCombination:
    machine_ids = [machine_id for machine_id, _ in machine_group]
    total_production = sum(production for _, production in machine_group)
    new_machine_count = sum(is_new_machine(machine_id) for machine_id in machine_ids)
    return MachineCombination(machine_ids, int(total_production), len(machine_ids), int(total_production - requirement), int(new_machine_count))


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


def choose_new_machine_preference(current_best: MachineCombination | None, candidate: MachineCombination) -> MachineCombination:
    if current_best is None:
        return candidate
    if candidate.new_machine_count > current_best.new_machine_count:
        return candidate
    if candidate.new_machine_count < current_best.new_machine_count:
        return current_best
    current_gap = abs(current_best.gap)
    candidate_gap = abs(candidate.gap)
    if candidate_gap < current_gap:
        return candidate
    if candidate_gap > current_gap:
        return current_best
    if candidate.total_production > current_best.total_production:
        return candidate
    return current_best


def find_best_combination(machine_table: pd.DataFrame, requirement: int, allowed_shortage: int, selection_rule) -> MachineCombination | None:
    machine_options = list(zip(machine_table["Sr. No."], machine_table["Prod/day Pcs"]))
    for machine_count in range(1, len(machine_options) + 1):
        best_for_count = None
        for machine_group in combinations(machine_options, machine_count):
            total_production = sum(production for _, production in machine_group)
            if not is_valid_combination(int(total_production), int(requirement), int(allowed_shortage)):
                continue
            candidate = build_result(machine_group, int(requirement))
            best_for_count = selection_rule(best_for_count, candidate)
        if best_for_count is not None:
            return best_for_count
    return None


def build_selected_jet_table(machine_table: pd.DataFrame, result: MachineCombination | None) -> pd.DataFrame:
    if result is None:
        return pd.DataFrame(columns=machine_table.columns)
    table = machine_table[machine_table["Sr. No."].isin(result.machine_ids)].copy()
    table["selection_order"] = pd.Categorical(table["Sr. No."], categories=result.machine_ids, ordered=True)
    return table.sort_values("selection_order").drop(columns="selection_order")


def build_option_summary(title: str, result: MachineCombination | None, requirement: int, allowed_shortage: int) -> pd.DataFrame:
    if result is None:
        return pd.DataFrame([{"Metric": "Status", "Value": "No valid combination found"}])
    gap_label = "Excess" if result.gap >= 0 else "Shortage"
    gap_value = result.gap if result.gap >= 0 else abs(result.gap)
    return pd.DataFrame([
        {"Metric": "Option", "Value": title},
        {"Metric": "Requirement", "Value": int(requirement)},
        {"Metric": "Allowed Shortage", "Value": int(allowed_shortage)},
        {"Metric": "Machines Used", "Value": int(result.machine_count)},
        {"Metric": "New Machines", "Value": int(result.new_machine_count)},
        {"Metric": "Selected Machines", "Value": ", ".join(result.machine_ids)},
        {"Metric": "Total Production", "Value": int(result.total_production)},
        {"Metric": gap_label, "Value": int(gap_value)},
    ])


def calculate_jet_dyeing(machine_table: pd.DataFrame, requirement: float, allowed_shortage: float) -> dict:
    machine_table = machine_table.copy()
    machine_table["Prod/day Pcs"] = pd.to_numeric(machine_table["Prod/day Pcs"], errors="coerce").fillna(0).astype(int)
    closest_result = find_best_combination(machine_table, int(round(requirement)), int(round(allowed_shortage)), choose_closest_combination)
    new_machine_result = find_best_combination(machine_table, int(round(requirement)), int(round(allowed_shortage)), choose_new_machine_preference)
    selected_option = closest_result if JET_SELECTED_OPTION == "option1" else new_machine_result
    return {
        "option1_summary": build_option_summary("OPTION 1 - CLOSEST WITH MINIMUM MACHINES", closest_result, int(round(requirement)), int(round(allowed_shortage))),
        "option1_table": build_selected_jet_table(machine_table, closest_result),
        "option2_summary": build_option_summary("OPTION 2 - NEW MACHINE PREFERENCE WITH MINIMUM MACHINES", new_machine_result, int(round(requirement)), int(round(allowed_shortage))),
        "option2_table": build_selected_jet_table(machine_table, new_machine_result),
        "selected_machine_count": int(selected_option.machine_count) if selected_option else 0,
    }
