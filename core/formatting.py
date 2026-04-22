from __future__ import annotations

import math
import pandas as pd


def to_number(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def round_half_up(value: float, digits: int = 0) -> float:
    factor = 10 ** digits
    return math.floor(value * factor + 0.5) / factor


def format_display_number(value: object) -> str:
    number = to_number(value, default=0.0)
    if abs(number - int(number)) < 1e-9:
        return f"{int(number):,}"
    return f"{number:,.2f}"


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
