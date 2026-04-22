from __future__ import annotations
import re
import pandas as pd
from config.constants import MASTER_COLUMNS

def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()

def slugify(value: str) -> str:
    value = normalize_text(value).lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")

def build_row_id(section: str, sr_no) -> str:
    try:
        sr = int(float(sr_no))
    except Exception:
        sr = 0
    return f"master.{slugify(section)}.sr_{sr}"

def parse_ppc(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    for col in ["Main_Group","Sub_Group","Category","Subcategory"]:
        df[col] = df[col].apply(normalize_text)
    df["Asking_Rate_Per_Day"] = pd.to_numeric(df["Asking_Rate_Per_Day"], errors="coerce").fillna(0.0)
    df["row_type"] = df["Subcategory"].apply(lambda x: "calculated" if x in {"Grand Total","Overedging Total","Union Total","MT (PC/Day)","TT (PC/Day)"} else "input")
    df["row_order"] = range(len(df))
    return df

def parse_capacity(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.iloc[:, :8].copy()
    df.columns = [
        "location","avg_area_per_piece","reference_pcs_per_day","reference_mtr_per_day",
        "reference_lac_sqm_per_month","actual_pcs_per_day","actual_mtr_per_day","actual_lac_sqm_per_month"
    ]
    df["location"] = df["location"].apply(normalize_text).replace({"":"Total"})
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["row_order"] = range(len(df))
    return df

def parse_coating(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["Parameter"] = df["Parameter"].apply(normalize_text)
    df["Material"] = df["Material"].apply(normalize_text)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0.0)
    df["row_type"] = df["Parameter"].apply(lambda x: "input" if x in {"Speed","Efficiency","Utilisation"} else "calculated")
    df["row_order"] = range(len(df))
    return df

def parse_cs(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    for col in ["Section","Process","Metric"]:
        df[col] = df[col].apply(normalize_text)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0.0)
    df["row_order"] = range(len(df))
    return df

def parse_hydro(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["row_order"] = range(len(df))
    return df

def parse_master(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df[[c for c in MASTER_COLUMNS if c in raw_df.columns]].copy()
    text_cols = ["Location","Business","Section","Dept_Machine_Name","Designation","Workload","Formulas","Operator_Type","Remarks"]
    for col in text_cols:
        df[col] = df[col].apply(normalize_text)
    for col in [c for c in df.columns if c not in text_cols]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["row_id"] = [build_row_id(r["Section"], r["Sr_No"]) for _, r in df.iterrows()]
    df["row_order"] = range(len(df))
    return df
