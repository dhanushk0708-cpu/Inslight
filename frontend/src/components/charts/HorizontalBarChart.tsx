"use client";
import React from "react";
import {
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

interface HorizontalBarChartProps {
  data: Array<Record<string, any>>;
  xKey: string;
  yKey: string;
  title?: string;
  color?: string;
}

export const HorizontalBarChart: React.FC<HorizontalBarChartProps> = ({
  data,
  xKey,
  yKey,
  title,
  color = "#6366f1",
}) => {
  if (!data?.length) return null;

  return (
    <div className="card" style={{ marginBottom: 0 }}>
      {title && <div className="card-title">{title}</div>}
      <div style={{ width: "100%", height: Math.max(210, data.length * 34) }}>
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart data={data} layout="vertical" margin={{ top: 6, right: 24, left: 10, bottom: 6 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: "#9aa4bc", fontSize: 10 }}
              tickFormatter={(v) => (v >= 100000 ? `₹${(v / 100000).toFixed(1)}L` : `₹${Number(v).toLocaleString("en-IN")}`)}
            />
            <YAxis
              type="category"
              dataKey={xKey}
              width={115}
              tick={{ fill: "#e2e8f0", fontSize: 11 }}
              tickFormatter={(v) => (String(v).length > 16 ? `${String(v).slice(0, 15)}…` : String(v))}
            />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid rgba(99,102,241,0.35)",
                borderRadius: 8,
                fontSize: 12,
                color: "#f8fafc",
              }}
              formatter={(value: any) => [`₹${Number(value).toLocaleString("en-IN")}`, yKey.replace("_", " ")]}
            />
            <Bar dataKey={yKey} radius={[0, 6, 6, 0]} barSize={18}>
              {data.map((_, idx) => (
                <Cell key={idx} fill={idx === 0 ? color : "rgba(99, 102, 241, 0.72)"} />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
