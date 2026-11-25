import React from "react";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#3b82f6", "#a78bfa"];

function fmt(v: any, key?: string): string {
  if (v == null || isNaN(v)) return "0";
  const n = Number(v);
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  const isCount = key && /unit|qty|count|item|row|id/i.test(key);
  const pfx = isCount ? "" : "₹";
  if (abs >= 1e7) return `${sign}${pfx}${(abs / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${sign}${pfx}${(abs / 1e5).toFixed(2)} L`;
  if (abs >= 1e3) return `${sign}${pfx}${(abs / 1e3).toFixed(1)} K`;
  return `${sign}${pfx}${abs % 1 === 0 ? abs.toLocaleString("en-IN") : abs.toFixed(1)}`;
}

interface PieChartProps {
  data: Array<Record<string, any>>;
  xKey: string;
  yKey: string;
  title: string;
}

export const PieChart: React.FC<PieChartProps> = React.memo(({ data, xKey, yKey, title }) => {
  if (!data?.length) return null;
  const slices = data.slice(0, 8);
  const total = slices.reduce((s, d) => s + (Number(d[yKey]) || 0), 0) || 1;
  let cum = 0;

  const paths = slices.map((d, i) => {
    const v = Number(d[yKey]) || 0;
    const ang = (v / total) * 360;
    const sa = cum;
    cum += ang;
    const r = 76;
    const cx = 95;
    const cy = 95;
    const s = ((sa - 90) * Math.PI) / 180;
    const e = ((cum - 90) * Math.PI) / 180;
    return {
      d: `M ${cx} ${cy} L ${cx + r * Math.cos(s)} ${cy + r * Math.sin(s)} A ${r} ${r} 0 ${ang > 180 ? 1 : 0} 1 ${cx + r * Math.cos(e)} ${cy + r * Math.sin(e)} Z`,
      color: COLORS[i % COLORS.length],
      label: String(d[xKey]),
      pct: ((v / total) * 100).toFixed(1),
      val: v,
    };
  });

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 24, padding: "10px 0" }}>
        <svg viewBox="0 0 190 190" style={{ width: 160, height: 160, flexShrink: 0 }}>
          {paths.map((p, i) => (
            <path key={i} d={p.d} fill={p.color} stroke="#111520" strokeWidth="2">
              <title>{`${p.label}: ${fmt(p.val, yKey)} (${p.pct}%)`}</title>
            </path>
          ))}
          <circle cx="95" cy="95" r="38" fill="#111520" />
          <text x="95" y="92" textAnchor="middle" fill="#f1f3f9" fontSize="11" fontWeight="800">
            {fmt(total, yKey)}
          </text>
          <text x="95" y="104" textAnchor="middle" fill="#505872" fontSize="7.5" fontWeight="600">
            TOTAL
          </text>
        </svg>
        <div style={{ display: "flex", flexDirection: "column", gap: 7, maxWidth: 170 }}>
          {paths.map((p, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--text-secondary)" }}>
              <div style={{ width: 8, height: 8, borderRadius: 3, background: p.color, flexShrink: 0 }} />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.label}</span>
              <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--text-muted)", fontWeight: 700 }}>{p.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

PieChart.displayName = "PieChart";
