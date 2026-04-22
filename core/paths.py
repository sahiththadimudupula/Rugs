from __future__ import annotations

from pathlib import Path

from config.constants import INPUT_WORKBOOK_PATH, WORKING_WORKBOOK_PATH


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_input_workbook_path() -> Path:
    return get_project_root() / INPUT_WORKBOOK_PATH


def get_working_workbook_path() -> Path:
    return get_project_root() / WORKING_WORKBOOK_PATH


def get_active_workbook_path() -> Path:
    working_path = get_working_workbook_path()
    if working_path.exists():
        return working_path
    return get_input_workbook_path()
