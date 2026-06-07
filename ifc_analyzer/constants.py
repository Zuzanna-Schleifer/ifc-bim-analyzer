"""
Constants for the IFC BIM Analyzer.

Adjust COST_PER_TYPE to match your region and project type.
All costs are in EUR per element.
"""

# ---------------------------------------------------------------------------
# Cost estimates per IFC element type (EUR per element)
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

# Fallback cost for element types not listed above
DEFAULT_COST: int = 200
