SHEET_PPC = "Packing"
SHEET_CAPACITY = "Capacity"
SHEET_COATING = "Coating"
SHEET_CS = "CS"
SHEET_HYDRO = "Hydro "
SHEET_DYE_MC = "Dye_Mc"
SHEET_MASTER = "Rugs"
SHEET_PACKING_TQM = "Packing&TQM"

APP_TITLE = "Vapi Rugs Manpower Engine"
OPERATOR_TYPE_OPTIONS = ["Direct", "Indirect"]

MASTER_COLUMNS = [
    "Location","Business","Section","Sr_No","Dept_Machine_Name","Designation",
    "Machine_Count","Workload","Formulas","BE_Scientific_Manpower","Operator_Type",
    "Contractors","Company_Associate","BE_Final_Manpower","N_shift","General_Shift",
    "Shift_A","Shift_B","Shift_C","Reliever","Remarks"
]

EDITABLE_MASTER_COLUMNS = [
    "Machine_Count","Operator_Type","Contractors","Company_Associate",
    "BE_Final_Manpower","General_Shift","Shift_A","Shift_B","Shift_C","Reliever","Remarks"
]

PRE_PROCESSING_SECTIONS = [
    "CHENILLE","Yarn Warehouse","Table Tufting","Machine Tufting","Roll Receiving"
]

FINAL_SECTIONS = [
    "Store- Trims","Store- Carton","Store- Dyes & Camical","Sub-Stores",
    "Dispatch & Warehouse","PPC","T&D","P & IR","ADMINISTRATION","SECURITY",
    "Grey","PD","Engneering"
]

COATING_SECTION = "Coating"
CUT_AND_SEW_SECTION = "Cut & Sew"
DYEING_SECTION = "Dyeing"
PACKING_TQM_SECTIONS = ["Packing  Line MP", "Packing Support MP", "TQM", "TQM Other Support"]

SQUARE_METER_DIVISOR = 3.9
DAYS_PER_MONTH = 30
CS_DAYS_PER_MONTH = 25
COATING_BUFFER = 1.05
COATING_CAPACITY_BASE = 1400.0
HYDRO_PCS_CONVERSION = 0.98

TAB_ORDER = [
    "PPC data",
    "Pre Processing",
    "Coating",
    "Cut & Sew",
    "Dyeing",
    "Packin&TQM",
    "Final Sections",
    "Final Master Sheet",
]
