"""
IFC Building Model Analyzer
Outputs: Excel report + JSON for React dashboard
pip install ifcopenshell pandas openpyxl
python analyze_ifc.py model.ifc
"""

import sys, json, argparse
from pathlib import Path
import ifcopenshell
import ifcopenshell.util.element as ifc_util
import pandas as pd

COST_PER_TYPE = {
    "IfcWall": 350,
    "IfcWallStandardCase": 350,
    "IfcSlab": 280,
    "IfcBeam": 420,
    "IfcColumn": 510,
    "IfcDoor": 650,
    "IfcWindow": 480,
    "IfcStair": 1200,
    "IfcRoof": 390,
    "IfcFurnishingElement": 220,
    "IfcFlowTerminal": 310,
    "IfcBuildingElementProxy": 150,
}
DEFAULT_COST = 200


def get_material(el):
    try:
        m = ifc_util.get_material(el)
        if m is None:
            return "Unknown"
        if hasattr(m, "Name"):
            return m.Name or "Unknown"
        if hasattr(m, "MaterialLayers"):
            return (
                " + ".join(ml.Material.Name for ml in m.MaterialLayers if ml.Material)
                or "Unknown"
            )
        if hasattr(m, "Materials"):
            return " + ".join(x.Name for x in m.Materials if x) or "Unknown"
        return str(m)
    except:
        return "Unknown"


def get_qty(el, qs, qn):
    try:
        for r in el.IsDefinedBy:
            if r.is_a("IfcRelDefinesByProperties"):
                p = r.RelatingPropertyDefinition
                if p.is_a("IfcElementQuantity") and p.Name == qs:
                    for q in p.Quantities:
                        if q.Name == qn:
                            for a in (
                                "LengthValue",
                                "AreaValue",
                                "VolumeValue",
                                "WeightValue",
                                "CountValue",
                            ):
                                v = getattr(q, a, None)
                                if v is not None:
                                    return float(v)
    except:
        pass
    return None


def extract_elements(model):
    rows = []
    for el in model.by_type("IfcBuildingElement"):
        t = el.is_a()
        storey = "Unknown"
        try:
            for r in el.ContainedInStructure:
                c = r.RelatingStructure
                if c.is_a("IfcBuildingStorey"):
                    storey = c.Name or "Unknown"
        except:
            pass
        rows.append(
            {
                "IFC_Type": t,
                "Name": el.Name or "—",
                "Material": get_material(el),
                "Storey": storey,
                "Unit_Cost": COST_PER_TYPE.get(t, DEFAULT_COST),
            }
        )
    return pd.DataFrame(rows)


def extract_spaces(model):
    rows = []
    for s in model.by_type("IfcSpace"):
        name = s.Name or s.LongName or "Space"
        storey = "Unknown"
        try:
            for r in s.Decomposes:
                p = r.RelatingObject
                if p.is_a("IfcBuildingStorey"):
                    storey = p.Name or "Unknown"
        except:
            pass
        area = (
            get_qty(s, "Qto_SpaceBaseQuantities", "NetFloorArea")
            or get_qty(s, "BaseQuantities", "NetFloorArea")
            or get_qty(s, "Qto_SpaceBaseQuantities", "GrossFloorArea")
        )
        rows.append(
            {
                "Space_Name": name,
                "Storey": storey,
                "Area_m2": round(area, 2) if area else None,
            }
        )
    return pd.DataFrame(rows)


def export_excel(el_df, sp_df, out_dir, name):
    mat = (
        el_df.groupby("Material")
        .agg(Count=("IFC_Type", "count"), Cost=("Unit_Cost", "sum"))
        .reset_index()
    )
    typ = (
        el_df.groupby("IFC_Type")
        .agg(Count=("Name", "count"), Cost=("Unit_Cost", "sum"))
        .reset_index()
    )
    p = out_dir / f"{name}_report.xlsx"
    with pd.ExcelWriter(p, engine="openpyxl") as w:
        el_df.to_excel(w, sheet_name="All Elements", index=False)
        sp_df.to_excel(w, sheet_name="Rooms & Spaces", index=False)
        mat.to_excel(w, sheet_name="Materials", index=False)
        typ.to_excel(w, sheet_name="Cost by Type", index=False)
    print(f"  ✔  Excel → {p}")


def export_json(el_df, sp_df, out_dir, name):
    type_df = (
        el_df.groupby("IFC_Type")
        .agg(count=("Name", "count"), total_cost=("Unit_Cost", "sum"))
        .reset_index()
        .sort_values("total_cost", ascending=False)
        .head(12)
    )
    mat_df = (
        el_df.groupby("Material")
        .agg(count=("IFC_Type", "count"), total_cost=("Unit_Cost", "sum"))
        .reset_index()
        .sort_values("count", ascending=False)
        .head(10)
    )
    storey = el_df.groupby(["Storey", "IFC_Type"]).size().reset_index(name="count")
    sp_c = sp_df.dropna(subset=["Area_m2"]).sort_values("Area_m2", ascending=False)
    payload = {
        "model_name": name,
        "total_elements": int(len(el_df)),
        "total_rooms": int(len(sp_df)),
        "total_area": (
            round(float(sp_df["Area_m2"].sum()), 1)
            if sp_df["Area_m2"].notna().any()
            else 0
        ),
        "total_cost": int(el_df["Unit_Cost"].sum()),
        "cost_by_type": type_df.rename(columns={"IFC_Type": "name"}).to_dict(
            orient="records"
        ),
        "materials": mat_df.rename(columns={"Material": "name"}).to_dict(
            orient="records"
        ),
        "spaces": sp_c.rename(
            columns={"Space_Name": "name", "Area_m2": "area"}
        ).to_dict(orient="records"),
        "storey_dist": storey.to_dict(orient="records"),
    }
    p = out_dir / "dashboard_data.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✔  JSON  → {p}  (copy to dashboard/src/data/)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ifc_file")
    ap.add_argument("--output", default="output")
    args = ap.parse_args()
    ifc_path = Path(args.ifc_file)
    if not ifc_path.exists():
        print(f"Not found: {ifc_path}")
        sys.exit(1)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    mn = ifc_path.stem
    print(f"\n📂  Loading {ifc_path.name} …")
    model = ifcopenshell.open(str(ifc_path))
    print(f"    Schema: {model.schema}")
    print("\n🔍  Extracting …")
    el_df = extract_elements(model)
    sp_df = extract_spaces(model)
    print(f"    Elements: {len(el_df)}  Spaces: {len(sp_df)}")
    print("\n💾  Exporting …")
    export_excel(el_df, sp_df, out, mn)
    export_json(el_df, sp_df, out, mn)
    print("\n✅  Done!\n")


if __name__ == "__main__":
    main()
