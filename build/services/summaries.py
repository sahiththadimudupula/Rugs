from __future__ import annotations
import pandas as pd

def build_summary(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {"visible_section_count": 0, "scientific_total": 0.0, "final_total": 0.0, "machine_total": 0.0}
    return {
        "visible_section_count": float(df["Section"].nunique()),
        "scientific_total": float(df["BE_Scientific_Manpower"].sum()),
        "final_total": float(df["BE_Final_Manpower"].sum()),
        "machine_total": float(df["Machine_Count"].sum()),
    }

def add_total_row(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    total = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            total[col] = df[col].sum()
        elif col == df.columns[0]:
            total[col] = "Total"
        else:
            total[col] = ""
    return pd.concat([df, pd.DataFrame([total])], ignore_index=True)
