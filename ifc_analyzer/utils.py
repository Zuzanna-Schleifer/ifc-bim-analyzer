"""
Utility functions for reading material and quantity data from IFC elements.
"""

import ifcopenshell.util.element as ifc_util


def get_material(element) -> str:
    """
    Return a human-readable material name for an IFC element.

    Tries IfcMaterial, IfcMaterialLayerSet, and IfcMaterialConstituentSet.
    Returns 'Unknown' if nothing is found.
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
        quantity_set_name: name of the quantity set
        quantity_name: name of the quantity

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
