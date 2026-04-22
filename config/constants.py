from __future__ import annotations

APP_TITLE = "Vapi Rugs Manpower Engine"

INPUT_WORKBOOK_PATH = "input/Rugs.xlsx"
WORKING_WORKBOOK_PATH = "output/Rugs_working.xlsx"

WHITE = "#FFFFFF"
BLUE = "#0B5ED7"
DARK_TEXT = "#111111"
BORDER = "#D9E2F3"
LIGHT_BLUE = "#EAF2FF"

EDITABLE_MASTER_COLUMNS = [
    "Operator_Type",
    "Contractors",
    "Company_Associate",
    "BE_Final_Manpower",
    "General_Shift",
    "Shift_A",
    "Shift_B",
    "Shift_C",
    "Reliever",
    "Remarks",
]

OPERATOR_TYPE_OPTIONS = ["Direct", "Indirect"]

PRE_PROCESSING_SECTIONS = [
    "CHENILLE",
    "Yarn Warehouse",
    "Table Tufting",
    "Machine Tufting",
    "Roll Receiving",
]

PACKING_TQM_SECTIONS = [
    "Production Line MP",
    "Support MP",
    "TQM",
    "Other Support",
]

FINAL_SECTION_GROUP = [
    "Store- Trims",
    "Store- Carton",
    "Store- Dyes & Camical",
    "Sub-Stores",
    "Dispatch & Warehouse",
    "PPC",
    "T&D",
    "P & IR",
    "ADMINISTRATION",
    "SECURITY",
    "Grey",
    "PD",
    "Engneering",
]

COMPACT_SECTION_COLUMNS = [
    "Section",
    "Dept_Machine_Name",
    "Designation",
    "BE_Final_Manpower",
]

SUMMARY_COLUMNS = ["Section", "Machine_Count", "sum(BE_Final_Manpower)"]

MASTER_COLUMNS = [
    "Location",
    "Business",
    "Section",
    "Sr_No",
    "Dept_Machine_Name",
    "Designation",
    "Machine_Count",
    "Workload",
    "Formulas",
    "BE_Scientific_Manpower",
    "Operator_Type",
    "Contractors",
    "Company_Associate",
    "BE_Final_Manpower",
    "N_shift",
    "General_Shift",
    "Shift_A",
    "Shift_B",
    "Shift_C",
    "Reliever",
    "Remarks",
]
