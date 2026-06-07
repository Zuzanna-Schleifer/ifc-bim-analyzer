import { useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from "recharts";

// ─── types ───────────────────────────────────────────────────────────────────

interface CostByType {
  name: string;
  count: number;
  total_cost: number;
}

interface Material {
  name: string;
  count: number;
  total_cost: number;
}

interface Space {
  name: string;
  storey: string;
  area: number;
}

interface StoreyEntry {
  Storey: string;
  IFC_Type: string;
  count: number;
}

export interface DashboardData {
  model_name: string;
  total_elements: number;
  total_rooms: number;
  total_area: number;
  total_cost: number;
  cost_by_type: CostByType[];
  materials: Material[];
  spaces: Space[];
  storey_dist: StoreyEntry[];
}

// ─── constants ───────────────────────────────────────────────────────────────

const PALETTE = [
  "#378ADD", "#1D9E75", "#D85A30", "#BA7517", "#533AB7",
  "#D4537E", "#639922", "#E24B4A", "#888780", "#0F6E56",
];

const TOOLTIP_STYLE = {
  contentStyle: {
    background: "#0d1117",
    border: "1px solid #30363d",
    borderRadius: 6,
    fontSize: 12,
  },
  labelStyle: { color: "#e6edf3" },
  itemStyle: { color: "#58a6ff" },
};

const MAX_COST_TYPES = 12;
const MAX_MATERIALS = 10;
const MAX_ROOMS_VISIBLE = 15;
const MAX_STOREY_TYPES = 8;

// ─── helpers ─────────────────────────────────────────────────────────────────

const formatNumber = (n: number): string =>
  new Intl.NumberFormat("de-DE").format(n);

const formatEuro = (n: number): string => `€${formatNumber(n)}`;

const formatArea = (n: number): string => `${n} m²`;

// ─── sub-components ──────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: "blue" | "green";
}

function KpiCard({ label, value, sub, accent = "blue" }: KpiCardProps) {
  const color = accent === "green" ? "#3fb950" : "#58a6ff";
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "1.25rem 1.5rem" }}>
      <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#8b949e", marginBottom: 8 }}>
        {label}
      </p>
      <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 28, fontWeight: 600, color, margin: 0 }}>
        {value}
      </p>
      {sub && <p style={{ fontSize: 12, color: "#8b949e", marginTop: 4 }}>{sub}</p>}
    </div>
  );
}

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
}

function ChartCard({ title, children }: ChartCardProps) {
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "1.25rem 1.5rem" }}>
      <p style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#8b949e", margin: "0 0 1rem" }}>
        {title}
      </p>
      {children}
    </div>
  );
}

interface StoreyFilterProps {
  storeys: string[];
  active: string | null;
  onChange: (storey: string | null) => void;
}

function StoreyFilter({ storeys, active, onChange }: StoreyFilterProps) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
      {["All", ...storeys].map((s) => {
        const isActive = s === "All" ? active === null : active === s;
        return (
          <button
            key={s}
            onClick={() => onChange(s === "All" ? null : s)}
            style={{
              fontSize: 11,
              padding: "3px 10px",
              borderRadius: 4,
              cursor: "pointer",
              background: isActive ? (s === "All" ? "#58a6ff" : "#1D9E75") : "transparent",
              color: isActive ? (s === "All" ? "#0d1117" : "#fff") : "#8b949e",
              border: "1px solid #30363d",
              fontFamily: "inherit",
            }}
          >
            {s}
          </button>
        );
      })}
    </div>
  );
}

// ─── main component ──────────────────────────────────────────────────────────

interface DashboardProps {
  data: DashboardData;
}

export default function Dashboard({ data }: DashboardProps) {
  const [activeStorey, setActiveStorey] = useState<string | null>(null);

  const handleStoreyChange = useCallback(
    (storey: string | null) => setActiveStorey(storey),
    []
  );

  const storeys = [...new Set(data.storey_dist.map((d) => d.Storey))].sort();
  const types = [...new Set(data.storey_dist.map((d) => d.IFC_Type))];

  const storeyPivot = storeys.map((s) => {
    const row: Record<string, string | number> = { storey: s };
    types.forEach((t) => {
      row[t] = data.storey_dist
        .filter((d) => d.Storey === s && d.IFC_Type === t)
        .reduce((acc, d) => acc + d.count, 0);
    });
    return row;
  });

  const filteredSpaces = activeStorey
    ? data.spaces.filter((s) => s.storey === activeStorey)
    : data.spaces.slice(0, MAX_ROOMS_VISIBLE);

  const areaDisplay = data.total_area > 0
    ? `${formatNumber(data.total_area)} m²`
    : "N/A";

  return (
    <div style={{ minHeight: "100vh", background: "#0d1117", color: "#e6edf3", fontFamily: "'IBM Plex Sans', sans-serif" }}>

      <header style={{ borderBottom: "1px solid #30363d", padding: "2rem 2.5rem 1.5rem", display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#58a6ff", marginBottom: 6, fontFamily: "'IBM Plex Mono', monospace" }}>
            IFC BIM Analyzer
          </p>
          <h1 style={{ fontSize: 22, fontWeight: 600, margin: 0 }}>{data.model_name}</h1>
        </div>
        <span style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 4, padding: "0.25rem 0.75rem", fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, color: "#8b949e" }}>
          ifcopenshell · recharts · typescript
        </span>
      </header>

      <main style={{ padding: "2rem 2.5rem", maxWidth: 1400, margin: "0 auto" }}>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: "2rem" }}>
          <KpiCard label="Total elements" value={formatNumber(data.total_elements)} />
          <KpiCard label="Rooms / spaces" value={String(data.total_rooms)} accent="green" />
          <KpiCard label="Total floor area" value={areaDisplay} />
          <KpiCard label="Estimated cost" value={formatEuro(data.total_cost)} sub="rough unit-cost model" />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))", gap: 16, marginBottom: "2rem" }}>

          <ChartCard title="Estimated cost by element type">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.cost_by_type.slice(0, MAX_COST_TYPES)} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 140 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#8b949e", fontSize: 11 }} tickFormatter={(v: number) => `€${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#e6edf3", fontSize: 11 }} width={140} />
                <Tooltip {...TOOLTIP_STYLE} formatter={(v: number) => [formatEuro(v), "Total cost"]} />
                <Bar dataKey="total_cost" fill="#378ADD" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Element count by material">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={data.materials.slice(0, MAX_MATERIALS)}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }: { name: string; percent: number }) =>
                    `${name.length > 14 ? name.slice(0, 14) + "…" : name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={{ stroke: "#30363d" }}
                  fontSize={11}
                >
                  {data.materials.slice(0, MAX_MATERIALS).map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip {...TOOLTIP_STYLE} formatter={(v: number) => [v, "Elements"]} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Element distribution per storey">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={storeyPivot} margin={{ top: 0, right: 16, bottom: 40, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
                <XAxis dataKey="storey" tick={{ fill: "#8b949e", fontSize: 10 }} angle={-35} textAnchor="end" />
                <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} />
                <Tooltip {...TOOLTIP_STYLE} />
                {types.slice(0, MAX_STOREY_TYPES).map((t, i) => (
                  <Bar key={t} dataKey={t} stackId="a" fill={PALETTE[i % PALETTE.length]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Room areas by storey">
            <StoreyFilter storeys={storeys} active={activeStorey} onChange={handleStoreyChange} />
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={filteredSpaces} margin={{ top: 0, right: 16, bottom: 50, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#8b949e", fontSize: 9 }} angle={-40} textAnchor="end" />
                <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} tickFormatter={(v: number) => `${v}m²`} />
                <Tooltip {...TOOLTIP_STYLE} formatter={(v: number) => [formatArea(v), "Net floor area"]} />
                <Bar dataKey="area" fill="#1D9E75" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

        </div>

        <ChartCard title="Top elements by cost">
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #30363d" }}>
                  {["Type", "Count", "Unit cost", "Total cost"].map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: "8px 12px", color: "#8b949e", fontWeight: 500, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.cost_by_type.map((row, i) => (
                  <tr
                    key={row.name}
                    style={{ borderBottom: "1px solid #21262d" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "#161b22")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <td style={{ padding: "10px 12px", display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ width: 8, height: 8, borderRadius: "50%", background: PALETTE[i % PALETTE.length], flexShrink: 0 }} />
                      <code style={{ fontSize: 12, color: "#e6edf3", fontFamily: "'IBM Plex Mono', monospace" }}>
                        {row.name}
                      </code>
                    </td>
                    <td style={{ padding: "10px 12px", color: "#8b949e" }}>{row.count}</td>
                    <td style={{ padding: "10px 12px", color: "#8b949e" }}>
                      {formatEuro(Math.round(row.total_cost / row.count))}
                    </td>
                    <td style={{ padding: "10px 12px", color: "#3fb950", fontFamily: "'IBM Plex Mono', monospace" }}>
                      {formatEuro(row.total_cost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>

      </main>

      <footer style={{ borderTop: "1px solid #30363d", padding: "1.5rem 2.5rem", fontSize: 12, color: "#8b949e", fontFamily: "'IBM Plex Mono', monospace" }}>
        <a href="https://github.com/Zuzanna-Schleifer/ifc-bim-analyzer" style={{ color: "#58a6ff", textDecoration: "none" }}>
          ifc-bim-analyzer
        </a>
        {" · open source · MIT"}
      </footer>

    </div>
  );
}