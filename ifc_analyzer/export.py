"""
Export functions for generating Excel and JSON reports.
"""

import json
from pathlib import Path

import pandas as pd

from .extract import summarize_by_material, summarize_by_type


def export_excel(
    elements_df: pd.DataFrame,
    spaces_df: pd.DataFrame,
    output_dir: Path,
    model_name: str,
) -> None:
    """Export all data to a multi-sheet Excel file."""
    materials_df = summarize_by_material(elements_df)
    type_df = summarize_by_type(elements_df)

    output_path = output_dir / f"{model_name}_report.xlsx"

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        elements_df.to_excel(writer, sheet_name="All Elements", index=False)
        spaces_df.to_excel(writer, sheet_name="Rooms & Spaces", index=False)
        materials_df.to_excel(writer, sheet_name="Materials", index=False)
        type_df.to_excel(writer, sheet_name="Cost by Type", index=False)

    print(f"  ✔  Excel → {output_path}")


def export_json(
    elements_df: pd.DataFrame,
    spaces_df: pd.DataFrame,
    output_dir: Path,
    model_name: str,
) -> None:
    """Export aggregated data as JSON for the React dashboard."""
    type_df = summarize_by_type(elements_df).head(12)
    materials_df = summarize_by_material(elements_df).head(10)

    storey_dist = (
        elements_df.groupby(["Storey", "IFC_Type"]).size().reset_index(name="count")
    )

    spaces_clean = spaces_df.dropna(subset=["Area_m2"]).sort_values(
        "Area_m2", ascending=False
    )

    total_area = spaces_df["Area_m2"].sum()
    has_area_data = spaces_df["Area_m2"].notna().any()

    payload = {
        "model_name": model_name,
        "total_elements": int(len(elements_df)),
        "total_rooms": int(len(spaces_df)),
        "total_area": round(float(total_area), 1) if has_area_data else 0,
        "total_cost": int(elements_df["Unit_Cost"].sum()),
        "cost_by_type": type_df.rename(columns={"IFC_Type": "name"}).to_dict(
            orient="records"
        ),
        "materials": materials_df.rename(columns={"Material": "name"}).to_dict(
            orient="records"
        ),
        "spaces": spaces_clean.rename(
            columns={"Space_Name": "name", "Area_m2": "area"}
        ).to_dict(orient="records"),
        "storey_dist": storey_dist.to_dict(orient="records"),
    }

    output_path = output_dir / "dashboard_data.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  ✔  JSON  → {output_path}")
    print(f"     Copy to: dashboard/src/data/")
