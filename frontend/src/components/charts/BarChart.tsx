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

interface BarChartProps {
  data: Array<Record<string, any>>;
  xKey: string;
  yKey: string;
  title: string;
}

export const BarChart: React.FC<BarChartProps> = React.memo(({ data, xKey, yKey, title }) => {
  if (!data?.length) return null;
  const vals = data.map((d) => Number(d[yKey]) || 0);
  const mx = Math.max(...vals, 1);

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="bar-chart">
        {data.slice(0, 20).map((d, i) => {
          const v = Number(d[yKey]) || 0;
          const h = Math.max((v / mx) * 100, 3);
          const color = COLORS[i % COLORS.length];

          return (
            <div className="bar-group" key={i}>
              <div className="bar-value">{fmt(v, yKey)}</div>
              <div
                className="bar"
                style={{
                  height: `${h}%`,
                  background: `linear-gradient(180deg, ${color}, ${color}55)`,
                  boxShadow: `0 0 10px ${color}22`,
                }}
                title={`${d[xKey]}: ${fmt(v, yKey)}`}
              />
              <div className="bar-label" title={String(d[xKey])}>
                {String(d[xKey]).slice(0, 12)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

BarChart.displayName = "BarChart";
