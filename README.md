# IFC BIM Analyzer

Extract, analyze, and visualize building data from IFC models using Python and React.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)
![License](https://img.shields.io/badge/license-MIT-green)

## What it does

Given any IFC file, this tool extracts and analyzes building data:

- **Materials inventory** — element count and cost per material
- **Room areas** — net floor area per space, grouped by storey
- **Cost estimation** — rough unit-cost model per IFC element type
- **Excel report** — 4 sheets: all elements, spaces, materials, cost by type
- **Interactive React dashboard** — charts built with Recharts + TypeScript

## Stack

| Layer | Technology |
|-------|-----------|
| Data extraction | Python + ifcopenshell |
| Data analysis | pandas |
| Excel export | openpyxl |
| Dashboard | React 18 + TypeScript + Vite |
| Charts | Recharts |

## Project structure
ifc-bim-analyzer/
├── analyze_ifc.py        # Python script — IFC extraction + Excel + JSON
├── requirements.txt      # Python dependencies
├── output/               # Generated reports (git-ignored)
│   ├── *.xlsx
│   └── dashboard_data.json
└── dashboard/            # React + TypeScript dashboard
├── src/
│   ├── App.tsx
│   ├── Dashboard.tsx
│   └── data/
│       └── dashboard_data.json
├── package.json
└── vite.config.ts

## How to run

**Step 1 — Python analysis**

```bash
pip install ifcopenshell pandas openpyxl
python analyze_ifc.py your_model.ifc
```

Output: `output/dashboard_data.json` and `output/report.xlsx`

**Step 2 — React dashboard**

```bash
cd dashboard
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Sample data

Tested on a real IFC model with 5178 building elements across 12 element types including walls, columns, beams, doors, windows, and slabs.

## Free IFC models to try

- [buildingSMART Community Sample Files](https://github.com/buildingsmart-community/Community-Sample-Test-Files)
- [openBIM.org](https://www.openbim.org)

## Author

[Zuzanna-Schleifer](https://github.com/Zuzanna-Schleifer)

## License

MIT