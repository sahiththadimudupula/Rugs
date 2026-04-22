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


def parse_packintqm(raw_df: pd.DataFrame):
    helper_cols=["Type","Line","Req/Day","Production Capacity","Reqd. Lines","TQM Capacity","TQM"]
    draft_cols=MASTER_COLUMNS
    helper_df=pd.DataFrame(columns=helper_cols+["row_order"])
    draft_df=pd.DataFrame(columns=MASTER_COLUMNS+["row_order","row_id"])
    if raw_df is None or raw_df.empty:
        return helper_df, draft_df
    helper_header=1
    helper_block=raw_df.iloc[helper_header:6,:7].copy()
    cols=[normalize_text(v) for v in helper_block.iloc[0].tolist()]
    helper_block.columns=cols
    helper_block=helper_block.iloc[1:].reset_index(drop=True)
    if cols[:7]==helper_cols:
        helper_df=helper_block[helper_cols].copy()
        for c in helper_cols[2:]:
            helper_df[c]=pd.to_numeric(helper_df[c], errors='coerce').fillna(0.0)
        helper_df["row_order"]=range(len(helper_df))
    draft_header=9
    draft_block=raw_df.iloc[draft_header:,:len(MASTER_COLUMNS)].copy()
    dcols=[normalize_text(v) for v in draft_block.iloc[0].tolist()]
    dcols=["N_shift" if c=="N_shifts" else c for c in dcols]
    draft_block.columns=dcols
    draft_block=draft_block.iloc[1:].reset_index(drop=True)
    if dcols==MASTER_COLUMNS:
        draft_df=draft_block.copy()
        text_cols=["Location","Business","Section","Dept_Machine_Name","Designation","Workload","Formulas","Operator_Type","Remarks"]
        for col in text_cols:
            draft_df[col]=draft_df[col].apply(normalize_text)
        for col in [c for c in draft_df.columns if c not in text_cols]:
            draft_df[col]=pd.to_numeric(draft_df[col], errors='coerce').fillna(0.0)
        draft_df["row_id"]=[build_row_id(r["Section"], r["Sr_No"]) for _, r in draft_df.iterrows()]
        draft_df["row_order"]=range(len(draft_df))
    return helper_df, draft_df
