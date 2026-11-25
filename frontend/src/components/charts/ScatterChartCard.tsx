"use client";
import React from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ZAxis,
} from "recharts";

interface ScatterChartCardProps {
  data: Array<Record<string, any>>;
  xKey: string;
  yKey: string;
  title?: string;
}

export const ScatterChartCard: React.FC<ScatterChartCardProps> = ({
  data,
  xKey,
  yKey,
  title,
}) => {
  if (!data?.length) return null;

  return (
    <div className="card" style={{ marginBottom: 0 }}>
      {title && <div className="card-title">{title}</div>}
      <div style={{ width: "100%", height: 250 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              type="number"
              dataKey={xKey}
              name="Revenue"
              tick={{ fill: "#9aa4bc", fontSize: 10 }}
              tickFormatter={(v) => (v >= 100000 ? `₹${(v / 100000).toFixed(1)}L` : `₹${Number(v).toLocaleString("en-IN")}`)}
            />
            <YAxis
              type="number"
              dataKey={yKey}
              name="Profit"
              tick={{ fill: "#9aa4bc", fontSize: 10 }}
              tickFormatter={(v) => (v >= 100000 ? `₹${(v / 100000).toFixed(1)}L` : `₹${Number(v).toLocaleString("en-IN")}`)}
            />
            <ZAxis range={[70, 200]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{
                background: "#0f172a",
                border: "1px solid rgba(56,189,248,0.35)",
                borderRadius: 8,
                fontSize: 12,
                color: "#f8fafc",
              }}
              formatter={(value: any, name: string) => [`₹${Number(value).toLocaleString("en-IN")}`, name]}
              labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ""}
            />
            <Scatter name="Products" data={data} fill="#38bdf8" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
