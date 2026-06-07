"""
IFC BIM Analyzer
================
Extracts and analyzes building data from IFC files.

Outputs:
    - Excel report (.xlsx) with 4 sheets
    - JSON file for the React dashboard

Usage:
    python analyze_ifc.py model.ifc
    python analyze_ifc.py model.ifc --output results/

Requirements:
    pip install ifcopenshell pandas openpyxl
"""

import sys
import json
import argparse
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as ifc_util
import pandas as pd

# ---------------------------------------------------------------------------
# Cost estimates per IFC element type (EUR per element)
# Adjust these values to match your region and project type
# ---------------------------------------------------------------------------

COST_PER_TYPE: dict[str, int] = {
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

DEFAULT_COST: int = 200  # fallback for unrecognised element types


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_material(element) -> str:
    """
    Return a human-readable material name for an IFC element.

    Tries to read from IfcMaterial, IfcMaterialLayerSet,
    and IfcMaterialConstituentSet. Returns 'Unknown' if nothing found.
    """
    try:
        material = ifc_util.get_material(element)

        if material is None:
            return "Unknown"

        if hasattr(material, "Name"):
            return material.Name or "Unknown"

        if hasattr(material, "MaterialLayers"):
            names = [
                layer.Material.Name
                for layer in material.MaterialLayers
                if layer.Material
            ]
            return " + ".join(names) if names else "Unknown"

        if hasattr(material, "Materials"):
            names = [m.Name for m in material.Materials if m]
            return " + ".join(names) if names else "Unknown"

        return str(material)

    except Exception:
        return "Unknown"


def get_quantity(element, quantity_set_name: str, quantity_name: str) -> float | None:
    """
    Read a named quantity from an element's IfcElementQuantity.

    Args:
        element: IFC building element
        quantity_set_name: name of the quantity set (e.g. 'Qto_SpaceBaseQuantities')
        quantity_name: name of the quantity (e.g. 'NetFloorArea')

    Returns:
        Float value if found, None otherwise.
    """
    try:
        for relationship in element.IsDefinedBy:
            if not relationship.is_a("IfcRelDefinesByProperties"):
                continue

            property_set = relationship.RelatingPropertyDefinition

            if not property_set.is_a("IfcElementQuantity"):
                continue

            if property_set.Name != quantity_set_name:
                continue

            for quantity in property_set.Quantities:
                if quantity.Name != quantity_name:
                    continue

                for attribute in (
                    "LengthValue",
                    "AreaValue",
                    "VolumeValue",
                    "WeightValue",
                    "CountValue",
                ):
                    value = getattr(quantity, attribute, None)
                    if value is not None:
                        return float(value)

    except Exception:
        pass

    return None


def get_storey(element) -> str:
    """Return the building storey name for an element, or 'Unknown'."""
    try:
        for relationship in element.ContainedInStructure:
            container = relationship.RelatingStructure
            if container.is_a("IfcBuildingStorey"):
                return container.Name or "Unknown"
    except Exception:
        pass
    return "Unknown"


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


def extract_elements(model: ifcopenshell.file) -> pd.DataFrame:
    """
    Extract all building elements from the IFC model.

    Returns a DataFrame with columns:
        IFC_Type, Name, Material, Storey, Unit_Cost
    """
    rows = []

    for element in model.by_type("IfcBuildingElement"):
        ifc_type = element.is_a()
        rows.append(
            {
                "IFC_Type": ifc_type,
                "Name": element.Name or "—",
                "Material": get_material(element),
                "Storey": get_storey(element),
                "Unit_Cost": COST_PER_TYPE.get(ifc_type, DEFAULT_COST),
            }
        )

    return pd.DataFrame(rows)


def extract_spaces(model: ifcopenshell.file) -> pd.DataFrame:
    """
    Extract all spaces/rooms from the IFC model.

    Returns a DataFrame with columns:
        Space_Name, Storey, Area_m2
    """
    rows = []

    for space in model.by_type("IfcSpace"):
        name = space.Name or space.LongName or "Space"
        storey = "Unknown"

        try:
            for relationship in space.Decomposes:
                parent = relationship.RelatingObject
                if parent.is_a("IfcBuildingStorey"):
                    storey = parent.Name or "Unknown"
        except Exception:
            pass

        area = (
            get_quantity(space, "Qto_SpaceBaseQuantities", "NetFloorArea")
            or get_quantity(space, "BaseQuantities", "NetFloorArea")
            or get_quantity(space, "Qto_SpaceBaseQuantities", "GrossFloorArea")
        )

        rows.append(
            {
                "Space_Name": name,
                "Storey": storey,
                "Area_m2": round(area, 2) if area else None,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def summarize_by_material(elements_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate element count and total cost grouped by material."""
    return (
        elements_df.groupby("Material")
        .agg(
            Element_Count=("IFC_Type", "count"),
            Total_Cost=("Unit_Cost", "sum"),
        )
        .reset_index()
        .sort_values("Total_Cost", ascending=False)
    )


def summarize_by_type(elements_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate element count and total cost grouped by IFC type."""
    return (
        elements_df.groupby("IFC_Type")
        .agg(
            Count=("Name", "count"),
            Total_Cost=("Unit_Cost", "sum"),
        )
        .reset_index()
        .sort_values("Total_Cost", ascending=False)
    )


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze an IFC file and export reports."
    )
    parser.add_argument("ifc_file", help="Path to the .ifc file")
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: ./output)",
    )
    args = parser.parse_args()

    ifc_path = Path(args.ifc_file)
    if not ifc_path.exists():
        print(f"Error: file not found — {ifc_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_name = ifc_path.stem

    print(f"\n📂  Loading {ifc_path.name} …")
    model = ifcopenshell.open(str(ifc_path))
    print(f"    Schema: {model.schema}")

    print("\n🔍  Extracting data …")
    elements_df = extract_elements(model)
    spaces_df = extract_spaces(model)
    print(f"    Elements : {len(elements_df)}")
    print(f"    Spaces   : {len(spaces_df)}")

    print("\n💾  Exporting …")
    export_excel(elements_df, spaces_df, output_dir, model_name)
    export_json(elements_df, spaces_df, output_dir, model_name)

    print(f"\n✅  Done!\n")


if __name__ == "__main__":
    main()
