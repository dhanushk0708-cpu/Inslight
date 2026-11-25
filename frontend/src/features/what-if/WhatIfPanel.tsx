import React, { useState } from "react";
import { WhatIfData } from "../../types";
import { BarChart } from "../../components/charts/BarChart";
import { DataTable } from "../../components/common/DataTable";

function fmt(v: any): string {
  if (v == null || isNaN(v)) return "0";
  const n = Number(v);
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1e7) return `${sign}₹${(abs / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${sign}₹${(abs / 1e5).toFixed(2)} L`;
  if (abs >= 1e3) return `${sign}₹${(abs / 1e3).toFixed(1)} K`;
  return `${sign}₹${abs % 1 === 0 ? abs.toLocaleString("en-IN") : abs.toFixed(1)}`;
}

interface WhatIfPanelProps {
  data: WhatIfData | null;
  loading: boolean;
  onRunSimulation: (price: number, discount: number, units: number) => void;
}

export const WhatIfPanel: React.FC<WhatIfPanelProps> = ({ data, loading, onRunSimulation }) => {
  const [price, setPrice] = useState(0);
  const [discount, setDiscount] = useState(0);
  const [units, setUnits] = useState(0);

  const handleRun = () => {
    onRunSimulation(price, discount, units);
  };

  return (
    <div>
      <div className="whatif-panel">
        <div className="card-title">Scenario Parameters</div>
        <div className="slider-group">
          <div className="slider-header">
            <span className="slider-label">💰 Price Adjustment</span>
            <span className="slider-val">{price > 0 ? "+" : ""}{price}%</span>
          </div>
          <input
            className="slider-input"
            type="range"
            min={-50}
            max={50}
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
          />
        </div>

        <div className="slider-group">
          <div className="slider-header">
            <span className="slider-label">🏷️ Discount Adjustment</span>
            <span className="slider-val">{discount > 0 ? "+" : ""}{discount}%</span>
          </div>
          <input
            className="slider-input"
            type="range"
            min={-50}
            max={50}
            value={discount}
            onChange={(e) => setDiscount(Number(e.target.value))}
          />
        </div>

        <div className="slider-group">
          <div className="slider-header">
            <span className="slider-label">📦 Volume / Units Adjustment</span>
            <span className="slider-val">{units > 0 ? "+" : ""}{units}%</span>
          </div>
          <input
            className="slider-input"
            type="range"
            min={-50}
            max={50}
            value={units}
            onChange={(e) => setUnits(Number(e.target.value))}
          />
        </div>

        <button
          type="button"
          className="btn btn-primary"
          style={{ width: "100%", marginTop: 8 }}
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? "Simulating..." : "▶ Run Scenario"}
        </button>
      </div>

      {data && !data.error && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-header"><div className="kpi-label">Current Revenue</div><div className="kpi-icon">💰</div></div>
              <div className="kpi-value">{fmt(data.current?.revenue)}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-header"><div className="kpi-label">Projected Revenue</div><div className="kpi-icon">🎯</div></div>
              <div
                className="kpi-value"
                style={{ color: data.change?.revenue_diff >= 0 ? "var(--green)" : "var(--red)" }}
              >
                {fmt(data.projected?.revenue)}
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-header"><div className="kpi-label">Net Impact</div><div className="kpi-icon">📈</div></div>
              <div
                className="kpi-value"
                style={{ color: data.change?.revenue_pct_change >= 0 ? "var(--green)" : "var(--red)" }}
              >
                {data.change?.revenue_pct_change >= 0 ? "+" : ""}{data.change?.revenue_pct_change}%
              </div>
            </div>
          </div>

          {data.ai_commentary && <div className="narrative">{data.ai_commentary}</div>}

          {data.monthly_comparison?.length > 0 && (
            <BarChart
              data={data.monthly_comparison}
              xKey="month"
              yKey="projected_revenue"
              title="Projected Monthly Revenue"
            />
          )}

          {data.category_impact?.length > 0 && (
            <DataTable data={data.category_impact} title="Category Revenue Impact" />
          )}
        </>
      )}
    </div>
  );
};
