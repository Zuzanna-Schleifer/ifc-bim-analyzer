"""
IFC BIM Analyzer — entry point
================================
Analyzes an IFC file and exports an Excel report and JSON dashboard data.

Usage:
    python analyze_ifc.py model.ifc
    python analyze_ifc.py model.ifc --output results/

Requirements:
    pip install ifcopenshell pandas openpyxl
"""

import sys
import argparse
from pathlib import Path

import ifcopenshell

from ifc_analyzer import extract_elements, extract_spaces, export_excel, export_json


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
