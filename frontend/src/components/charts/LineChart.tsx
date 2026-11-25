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

interface LineChartProps {
  data: Array<Record<string, any>>;
  xKey: string;
  yKey: string;
  title: string;
}

export const LineChart: React.FC<LineChartProps> = React.memo(({ data, xKey, yKey, title }) => {
  if (!data?.length) return null;
  const vals = data.map((d) => Number(d[yKey]) || 0);
  const mx = Math.max(...vals, 1);
  const mn = Math.min(...vals, 0);
  const rng = mx - mn || 1;
  const w = 700;
  const h = 220;
  const pad = 42;
  const pw = w - pad * 2;
  const ph = h - pad * 2;

  const pts = data.map((d, i) => ({
    x: pad + (i / Math.max(data.length - 1, 1)) * pw,
    y: pad + ph - (((Number(d[yKey]) || 0) - mn) / rng) * ph,
  }));

  const pathD = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaD = `${pathD} L ${pts[pts.length - 1].x} ${pad + ph} L ${pts[0].x} ${pad + ph} Z`;
  const uid = `lg-${(title || "chart").replace(/\W/g, "")}`;

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div style={{ padding: "6px 0" }}>
        <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: "220px" }} preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id={uid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS[0]} stopOpacity="0.25" />
              <stop offset="100%" stopColor={COLORS[0]} stopOpacity="0.0" />
            </linearGradient>
          </defs>
          {[0, 0.33, 0.66, 1].map((f, i) => {
            const y = pad + ph * (1 - f);
            return (
              <g key={i}>
                <line x1={pad} y1={y} x2={w - pad} y2={y} stroke="rgba(255,255,255,.04)" />
                <text x={pad - 8} y={y + 3} textAnchor="end" fill="#505872" fontSize="9.5" fontWeight="600">
                  {fmt(mn + rng * f)}
                </text>
              </g>
            );
          })}
          <path d={areaD} fill={`url(#${uid})`} />
          <path d={pathD} fill="none" stroke={COLORS[0]} strokeWidth="2.5" strokeLinecap="round" />
          {pts.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="3" fill={COLORS[0]} stroke="#111520" strokeWidth="2">
              <title>{`${data[i][xKey]}: ${fmt(data[i][yKey], yKey)}`}</title>
            </circle>
          ))}
          {data.length <= 14 &&
            pts.map((p, i) => (
              <text key={`l${i}`} x={p.x} y={h - 6} textAnchor="middle" fill="#505872" fontSize="9">
                {String(data[i][xKey]).slice(0, 7)}
              </text>
            ))}
        </svg>
      </div>
    </div>
  );
});

LineChart.displayName = "LineChart";
