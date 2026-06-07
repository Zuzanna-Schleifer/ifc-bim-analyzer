import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, CartesianGrid,
} from "recharts";

// ─── types ───────────────────────────────────────────────────────────────────

interface DashboardData {
  model_name:     string;
  total_elements: number;
  total_rooms:    number;
  total_area:     number;
  total_cost:     number;
  cost_by_type:   { name: string; count: number; total_cost: number }[];
  materials:      { name: string; count: number; total_cost: number }[];
  spaces:         { name: string; storey: string; area: number }[];
  storey_dist:    { Storey: string; IFC_Type: string; count: number }[];
}

// ─── palette ─────────────────────────────────────────────────────────────────

const PALETTE = ["#378ADD", "#1D9E75", "#D85A30", "#BA7517", "#533AB7",
                 "#D4537E", "#639922", "#E24B4A", "#888780", "#0F6E56"];

// ─── sub-components ──────────────────────────────────────────────────────────

function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{
      background: "#161b22", border: "1px solid #30363d",
      borderRadius: 8, padding: "1.25rem 1.5rem",
    }}>
      <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                  color: "#8b949e", marginBottom: 8 }}>{label}</p>
      <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 28,
                  fontWeight: 600, color: "#58a6ff", margin: 0 }}>{value}</p>
      {sub && <p style={{ fontSize: 12, color: "#8b949e", marginTop: 4 }}>{sub}</p>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: "#161b22", border: "1px solid #30363d",
      borderRadius: 8, padding: "1.25rem 1.5rem",
    }}>
      <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                  color: "#8b949e", marginBottom: 16, margin: "0 0 1rem" }}>{title}</p>
      {children}
    </div>
  );
}

const tooltipStyle = {
  contentStyle: { background: "#0d1117", border: "1px solid #30363d",
                  borderRadius: 6, fontSize: 12 },
  labelStyle:   { color: "#e6edf3" },
  itemStyle:    { color: "#58a6ff" },
};

// ─── main ────────────────────────────────────────────────────────────────────

export default function Dashboard({ data }: { data: DashboardData }) {
  const [activeStorey, setActiveStorey] = useState<string | null>(null);

  // build storey distribution pivot
  const storeys = [...new Set(data.storey_dist.map(d => d.Storey))].sort();
  const types   = [...new Set(data.storey_dist.map(d => d.IFC_Type))];

  const storeyPivot = storeys.map(s => {
    const row: Record<string, string | number> = { storey: s };
    types.forEach(t => {
      row[t] = data.storey_dist
        .filter(d => d.Storey === s && d.IFC_Type === t)
        .reduce((a, d) => a + d.count, 0);
    });
    return row;
  });

  const filteredSpaces = activeStorey
    ? data.spaces.filter(s => s.storey === activeStorey)
    : data.spaces.slice(0, 15);

  const fmt = (n: number) => new Intl.NumberFormat("de-DE").format(n);

  return (
    <div style={{
      minHeight: "100vh", background: "#0d1117", color: "#e6edf3",
      fontFamily: "'IBM Plex Sans', sans-serif",
    }}>
      {/* header */}
      <header style={{
        borderBottom: "1px solid #30363d",
        padding: "2rem 2.5rem 1.5rem",
        display: "flex", alignItems: "flex-end",
        justifyContent: "space-between", flexWrap: "wrap", gap: "1rem",
      }}>
        <div>
          <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                      color: "#58a6ff", marginBottom: 6, fontFamily: "'IBM Plex Mono', monospace" }}>
            IFC BIM Analyzer
          </p>
          <h1 style={{ fontSize: 22, fontWeight: 600, margin: 0 }}>{data.model_name}</h1>
        </div>
        <span style={{
          background: "#161b22", border: "1px solid #30363d", borderRadius: 4,
          padding: "0.25rem 0.75rem", fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 12, color: "#8b949e",
        }}>
          ifcopenshell · recharts · typescript
        </span>
      </header>

      <main style={{ padding: "2rem 2.5rem", maxWidth: 1400, margin: "0 auto" }}>

        {/* KPI row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                      gap: 12, marginBottom: "2rem" }}>
          <KpiCard label="Total elements" value={fmt(data.total_elements)} />
          <KpiCard label="Rooms / spaces" value={String(data.total_rooms)} />
          <KpiCard label="Total floor area" value={data.total_area > 0 ? `${fmt(data.total_area)} m²` : "N/A"} />
          <KpiCard label="Estimated cost" value={`€${fmt(data.total_cost)}`} sub="rough unit-cost model" />
        </div>

        {/* charts grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
                      gap: 16, marginBottom: "2rem" }}>

          {/* cost by type */}
          <ChartCard title="Estimated cost by element type">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.cost_by_type} layout="vertical"
                        margin={{ top: 0, right: 16, bottom: 0, left: 140 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#8b949e", fontSize: 11 }}
                       tickFormatter={v => `€${(v/1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#e6edf3", fontSize: 11 }}
                       width={140} />
                <Tooltip {...tooltipStyle}
                         formatter={(v: number) => [`€${fmt(v)}`, "Total cost"]} />
                <Bar dataKey="total_cost" fill="#378ADD" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* material pie */}
          <ChartCard title="Element count by material">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={data.materials} dataKey="count" nameKey="name"
                     cx="50%" cy="50%" outerRadius={100}
                     label={({ name, percent }) =>
                       `${name.length > 14 ? name.slice(0,14)+"…" : name} ${(percent*100).toFixed(0)}%`}
                     labelLine={{ stroke: "#30363d" }}
                     fontSize={11}>
                  {data.materials.map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle}
                         formatter={(v: number) => [v, "Elements"]} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* storey distribution */}
          <ChartCard title="Element distribution per storey">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={storeyPivot} margin={{ top: 0, right: 16, bottom: 40, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
                <XAxis dataKey="storey" tick={{ fill: "#8b949e", fontSize: 10 }}
                       angle={-35} textAnchor="end" />
                <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} />
                <Tooltip {...tooltipStyle} />
                {types.slice(0, 8).map((t, i) => (
                  <Bar key={t} dataKey={t} stackId="a"
                       fill={PALETTE[i % PALETTE.length]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* room areas */}
          <ChartCard title="Room areas by storey">
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
              <button
                onClick={() => setActiveStorey(null)}
                style={{
                  fontSize: 11, padding: "3px 10px", borderRadius: 4, cursor: "pointer",
                  background: activeStorey === null ? "#58a6ff" : "transparent",
                  color:      activeStorey === null ? "#0d1117"  : "#8b949e",
                  border: "1px solid #30363d",
                }}>
                All
              </button>
              {[...new Set(data.spaces.map(s => s.storey))].sort().map(st => (
                <button key={st} onClick={() => setActiveStorey(st === activeStorey ? null : st)}
                  style={{
                    fontSize: 11, padding: "3px 10px", borderRadius: 4, cursor: "pointer",
                    background: activeStorey === st ? "#1D9E75" : "transparent",
                    color:      activeStorey === st ? "#fff"    : "#8b949e",
                    border: "1px solid #30363d",
                  }}>
                  {st}
                </button>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={filteredSpaces} margin={{ top: 0, right: 16, bottom: 50, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#8b949e", fontSize: 9 }}
                       angle={-40} textAnchor="end" />
                <YAxis tick={{ fill: "#8b949e", fontSize: 11 }}
                       tickFormatter={v => `${v}m²`} />
                <Tooltip {...tooltipStyle}
                         formatter={(v: number) => [`${v} m²`, "Net floor area"]} />
                <Bar dataKey="area" fill="#1D9E75" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* data table */}
        <ChartCard title="Top elements by cost">
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #30363d" }}>
                  {["Type", "Count", "Unit cost", "Total cost"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "8px 12px",
                                        color: "#8b949e", fontWeight: 500, fontSize: 11,
                                        textTransform: "uppercase", letterSpacing: "0.08em" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.cost_by_type.map((row, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #21262d" }}
                      onMouseEnter={e => (e.currentTarget.style.background = "#161b22")}
                      onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
                    <td style={{ padding: "10px 12px", display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ width: 8, height: 8, borderRadius: "50%",
                                     background: PALETTE[i % PALETTE.length], flexShrink: 0 }} />
                      <code style={{ fontSize: 12, color: "#e6edf3", fontFamily: "'IBM Plex Mono', monospace" }}>
                        {row.name}
                      </code>
                    </td>
                    <td style={{ padding: "10px 12px", color: "#8b949e" }}>{row.count}</td>
                    <td style={{ padding: "10px 12px", color: "#8b949e" }}>
                      €{fmt(Math.round(row.total_cost / row.count))}
                    </td>
                    <td style={{ padding: "10px 12px", color: "#3fb950",
                                 fontFamily: "'IBM Plex Mono', monospace" }}>
                      €{fmt(row.total_cost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </main>

      <footer style={{
        borderTop: "1px solid #30363d", padding: "1.5rem 2.5rem",
        fontSize: 12, color: "#8b949e", fontFamily: "'IBM Plex Mono', monospace",
      }}>
        <a href="https://github.com/YOUR_USERNAME/ifc-bim-analyzer"
           style={{ color: "#58a6ff", textDecoration: "none" }}>
          ifc-bim-analyzer
        </a>
        {" "}· open source · MIT
      </footer>
    </div>
  );
}
