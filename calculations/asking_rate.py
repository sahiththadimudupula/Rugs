from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

import pandas as pd

from core.formatting import clean_text, to_number

RowKey: TypeAlias = tuple[str, str, str, str]

MAIN_GROUP_COLUMN = "Main_Group"
SUB_GROUP_COLUMN = "Sub_Group"
CATEGORY_COLUMN = "Category"
SUBCATEGORY_COLUMN = "Subcategory"
ASKING_RATE_COLUMN = "Asking_Rate_Per_Day"
ROW_TYPE_COLUMN = "row_type"
DISPLAY_ORDER_COLUMN = "display_order"

ROW_TYPE_INPUT = "input"
ROW_TYPE_SUM = "sum"
ROW_TYPE_FORMULA = "formula"

PROCESSING_MT_BASE_VALUE = 54.42
PROCESSING_MT_BUFFER_FACTOR = 1.10
PROCESSING_MT_MULTIPLIER = 3.90


def build_row_key(
    main_group: object,
    sub_group: object,
    category: object,
    subcategory: object,
) -> RowKey:
    return (
        clean_text(main_group),
        clean_text(sub_group),
        clean_text(category),
        clean_text(subcategory),
    )


def is_formula_row(subcategory: str) -> bool:
    return subcategory in {"MT (PC/Day)", "TT (PC/Day)"}


def is_sum_row(subcategory: str) -> bool:
    return subcategory in {"Grand Total", "Overedging Total", "Union Total"}


def resolve_row_type(subcategory: str) -> str:
    if is_formula_row(subcategory):
        return ROW_TYPE_FORMULA
    if is_sum_row(subcategory):
        return ROW_TYPE_SUM
    return ROW_TYPE_INPUT


def prepare_asking_rate_table(source_table: pd.DataFrame) -> pd.DataFrame:
    table = source_table.copy()
    table[MAIN_GROUP_COLUMN] = table[MAIN_GROUP_COLUMN].apply(clean_text)
    table[SUB_GROUP_COLUMN] = table[SUB_GROUP_COLUMN].apply(clean_text)
    table[CATEGORY_COLUMN] = table[CATEGORY_COLUMN].apply(clean_text)
    table[SUBCATEGORY_COLUMN] = table[SUBCATEGORY_COLUMN].apply(clean_text)
    table[ASKING_RATE_COLUMN] = table[ASKING_RATE_COLUMN].apply(to_number)
    table[ROW_TYPE_COLUMN] = table[SUBCATEGORY_COLUMN].apply(resolve_row_type)
    table[DISPLAY_ORDER_COLUMN] = range(len(table))
    return table


def build_lookup(table: pd.DataFrame) -> dict[RowKey, int]:
    return {
        build_row_key(
            row[MAIN_GROUP_COLUMN],
            row[SUB_GROUP_COLUMN],
            row[CATEGORY_COLUMN],
            row[SUBCATEGORY_COLUMN],
        ): index
        for index, row in table.iterrows()
    }


def get_value(table: pd.DataFrame, lookup: Mapping[RowKey, int], row_key: RowKey) -> float:
    return to_number(table.at[lookup[row_key], ASKING_RATE_COLUMN])


def set_value(table: pd.DataFrame, lookup: Mapping[RowKey, int], row_key: RowKey, value: float) -> None:
    table.at[lookup[row_key], ASKING_RATE_COLUMN] = float(value)


def apply_user_inputs(table: pd.DataFrame, edited_table: pd.DataFrame | None) -> pd.DataFrame:
    if edited_table is None:
        return table

    edited = prepare_asking_rate_table(edited_table)
    merged = table.copy()
    base_lookup = build_lookup(merged)
    for _, row in edited.iterrows():
        if row[ROW_TYPE_COLUMN] != ROW_TYPE_INPUT:
            continue
        row_key = build_row_key(
            row[MAIN_GROUP_COLUMN],
            row[SUB_GROUP_COLUMN],
            row[CATEGORY_COLUMN],
            row[SUBCATEGORY_COLUMN],
        )
        if row_key in base_lookup:
            merged.at[base_lookup[row_key], ASKING_RATE_COLUMN] = to_number(row[ASKING_RATE_COLUMN])
    return merged


def recalculate_asking_rate_table(source_table: pd.DataFrame, edited_table: pd.DataFrame | None = None) -> pd.DataFrame:
    table = prepare_asking_rate_table(source_table)
    table = apply_user_inputs(table, edited_table)
    lookup = build_lookup(table)

    rules = {
        build_row_key("Packing", "", "Packing", "Grand Total"): [
            build_row_key("Packing", "", "Packing", "Carving"),
            build_row_key("Packing", "", "Packing", "Chenile"),
            build_row_key("Packing", "", "Packing", "non carving"),
            build_row_key("Packing", "", "Packing", "Roll"),
            build_row_key("Packing", "", "Packing", "Rugs"),
        ],
        build_row_key("C&S", "Overedging", "Stitching Type", "Overedging Total"): [
            build_row_key("C&S", "Overedging", "Stitching Type", "Drylon Washing"),
            build_row_key("C&S", "Overedging", "Stitching Type", "Non dyeing"),
            build_row_key("C&S", "Overedging", "Stitching Type", "tumble"),
        ],
        build_row_key("C&S", "Union", "Stitching Type", "Union Total"): [
            build_row_key("C&S", "Union", "Stitching Type", "Cotton dyeing"),
            build_row_key("C&S", "Union", "Stitching Type", "Drylon Washing"),
            build_row_key("C&S", "Union", "Stitching Type", "Polyester dyeing"),
        ],
        build_row_key("C&S", "", "Stitching Type", "Grand Total"): [
            build_row_key("C&S", "Overedging", "Stitching Type", "Overedging Total"),
            build_row_key("C&S", "Union", "Stitching Type", "Union Total"),
        ],
        build_row_key("Grey Issue", "", "Process", "Grand Total"): [
            build_row_key("Grey Issue", "", "Process", "Cotton dyeing"),
            build_row_key("Grey Issue", "", "Process", "Drylon Washing"),
            build_row_key("Grey Issue", "", "Process", "Non dyeing"),
            build_row_key("Grey Issue", "", "Process", "Polyester dyeing"),
            build_row_key("Grey Issue", "", "Process", "tumble"),
        ],
        build_row_key("Processing", "", "Process", "Grand Total"): [
            build_row_key("Processing", "", "Process", "Cotton dyeing"),
            build_row_key("Processing", "", "Process", "Drylon Washing"),
            build_row_key("Processing", "", "Process", "Polyester dyeing"),
        ],
        build_row_key("Coating", "", "Coating", "Grand Total"): [
            build_row_key("Coating", "", "Coating", "cotton"),
            build_row_key("Coating", "", "Coating", "Foam"),
        ],
        build_row_key("Machine Tufting", "", "M/c", "Grand Total"): [
            build_row_key("Machine Tufting", "", "M/c", "1/8 Cut"),
            build_row_key("Machine Tufting", "", "M/c", "1/8 MLCL"),
            build_row_key("Machine Tufting", "", "M/c", "1/10 Loop"),
            build_row_key("Machine Tufting", "", "M/c", "3/8 Cut"),
            build_row_key("Machine Tufting", "", "M/c", "3/8 Loop"),
        ],
        build_row_key("Table Tufting", "", "M/c", "Grand Total"): [
            build_row_key("Table Tufting", "", "M/c", "1/4 Rev"),
            build_row_key("Table Tufting", "", "M/c", "3/16 Cut"),
        ],
    }

    for total_key, source_keys in rules.items():
        total_value = sum(get_value(table, lookup, source_key) for source_key in source_keys)
        set_value(table, lookup, total_key, total_value)

    processing_mt = PROCESSING_MT_BASE_VALUE * PROCESSING_MT_BUFFER_FACTOR * PROCESSING_MT_MULTIPLIER
    set_value(table, lookup, build_row_key("Processing", "", "Process", "MT (PC/Day)"), processing_mt)

    processing_cotton = get_value(table, lookup, build_row_key("Processing", "", "Process", "Cotton dyeing"))
    processing_tt = processing_cotton - processing_mt
    set_value(table, lookup, build_row_key("Processing", "", "Process", "TT (PC/Day)"), processing_tt)

    return table.sort_values(DISPLAY_ORDER_COLUMN).reset_index(drop=True)
