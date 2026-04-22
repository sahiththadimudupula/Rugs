from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

from config.constants import MASTER_COLUMNS
from core.paths import get_active_workbook_path, get_input_workbook_path, get_working_workbook_path


def load_workbook_tables() -> dict[str, pd.DataFrame]:
    workbook_path = get_active_workbook_path()
    if not workbook_path.exists():
        raise FileNotFoundError(
            f"Workbook not found. Please place the file at: {get_input_workbook_path()}"
        )

    return {
        "master_source_df": pd.read_excel(workbook_path, sheet_name="Rugs"),
        "packing_source_df": pd.read_excel(workbook_path, sheet_name="Packing"),
        "capacity_source_df": pd.read_excel(workbook_path, sheet_name="Capacity"),
        "coating_source_df": pd.read_excel(workbook_path, sheet_name="Coating"),
        "cs_source_df": pd.read_excel(workbook_path, sheet_name="CS"),
        "hydro_source_df": pd.read_excel(workbook_path, sheet_name="Hydro "),
        "dye_mc_source_df": pd.read_excel(workbook_path, sheet_name="Dye_Mc"),
        "packing_tfo_raw_df": pd.read_excel(workbook_path, sheet_name="packing&tfo", header=None),
    }



def _write_state_to_excel(writer: pd.ExcelWriter, state: dict) -> None:
    state["master_df"][MASTER_COLUMNS].to_excel(writer, sheet_name="Rugs", index=False)
    state["asking_rate_df"].drop(
        columns=[column for column in state["asking_rate_df"].columns if column in {"row_type", "display_order"}],
        errors="ignore",
    ).to_excel(writer, sheet_name="Packing", index=False)
    state["capacity_df"].to_excel(writer, sheet_name="Capacity", index=False)
    state["coating_df"].to_excel(writer, sheet_name="Coating", index=False)
    state["cs_df"].to_excel(writer, sheet_name="CS", index=False)
    state["hydro_df"].to_excel(writer, sheet_name="Hydro ", index=False)
    state["dyeing_result"]["summary_df"].to_excel(writer, sheet_name="Dye_Mc", index=False)
    state["packing_tqm_helper_df"].to_excel(writer, sheet_name="packing&tfo", index=False)



def save_workbook_tables(state: dict) -> Path:
    working_path = get_working_workbook_path()
    working_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(working_path, engine="openpyxl") as writer:
        _write_state_to_excel(writer, state)

    return working_path



def export_workbook_bytes(state: dict) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        _write_state_to_excel(writer, state)
    buffer.seek(0)
    return buffer.getvalue()



def reset_working_workbook() -> None:
    working_path = get_working_workbook_path()
    if working_path.exists():
        working_path.unlink()
