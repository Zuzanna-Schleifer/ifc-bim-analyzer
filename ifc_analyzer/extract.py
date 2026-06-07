"""
Data extraction functions for IFC building elements and spaces.
"""

import ifcopenshell
import pandas as pd

from .constants import COST_PER_TYPE, DEFAULT_COST
from .utils import get_material, get_quantity, get_storey


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
