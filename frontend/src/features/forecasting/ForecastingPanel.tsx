import React, { useState } from "react";
import { ForecastData } from "../../types";
import { LineChart } from "../../components/charts/LineChart";

interface ForecastingPanelProps {
  data: ForecastData | null;
  loading: boolean;
  onRunForecast: (horizon: number, method: string) => void;
}

export const ForecastingPanel: React.FC<ForecastingPanelProps> = ({ data, loading, onRunForecast }) => {
  const [horizon, setHorizon] = useState(30);
  const [method, setMethod] = useState("auto");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Parameter Controls Bar */}
      <div
        style={{
          background: "#111827",
          border: "1px solid #1F2937",
          borderRadius: 12,
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 14
        }}
      >
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <label style={{ fontSize: 11, color: "#94A3B8", display: "block", marginBottom: 4, textTransform: "uppercase", fontWeight: 700 }}>
              Forecast Horizon
            </label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              style={{ background: "#1F2937", border: "1px solid #374151", color: "#F8FAFC", borderRadius: 6, padding: "6px 12px", fontSize: 13 }}
            >
              <option value={7}>Next 7 Periods (Short-Term)</option>
              <option value={30}>Next 30 Periods (Standard)</option>
              <option value={90}>Next 90 Periods (Quarterly)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: 11, color: "#94A3B8", display: "block", marginBottom: 4, textTransform: "uppercase", fontWeight: 700 }}>
              Algorithm Model
            </label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              style={{ background: "#1F2937", border: "1px solid #374151", color: "#F8FAFC", borderRadius: 6, padding: "6px 12px", fontSize: 13 }}
            >
              <option value="auto">Auto (Best Fit ML / Statistical)</option>
              <option value="random_forest">Random Forest Regression</option>
              <option value="linear_regression">Linear Trend Extrapolation</option>
              <option value="exponential_smoothing">Holt Exponential Smoothing</option>
              <option value="moving_average">Simple Moving Average</option>
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onRunForecast(horizon, method)}
          disabled={loading}
          className="chat-action-btn active"
          style={{ padding: "8px 22px" }}
        >
          {loading ? "Generating Forecast..." : "📈 Run Forecast Model"}
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "60px 20px" }}>
          <div style={{ fontSize: 24, marginBottom: 12 }}>📈</div>
          <div style={{ color: "#94A3B8", fontSize: 14 }}>Training predictive model and computing interval bounds...</div>
        </div>
      )}

      {!loading && (!data || data.status !== "success") && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "#64748B" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📊</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#94A3B8", marginBottom: 6 }}>Ready for Time-Series Prediction</div>
          <p style={{ fontSize: 13, maxWidth: 440, margin: "0 auto 20px auto" }}>
            {data?.message || "Select a time horizon and predictive method to project future revenue and order trends."}
          </p>
        </div>
      )}

      {!loading && data && data.status === "success" && (
        <>
          {/* Key Forecast Summary Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
            <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Projected Total ({data.horizon_label})</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#38BDF8", marginTop: 4 }}>
                {data.formatted_forecast_total}
              </div>
              <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                Model: <strong style={{ color: "#E2E8F0" }}>{data.method_used}</strong>
              </div>
            </div>

            <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Projected Trend Direction</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: data.projected_growth_pct >= 0 ? "#10B981" : "#EF4444", marginTop: 4 }}>
                {data.trend_direction} ({data.projected_growth_pct > 0 ? "+" : ""}{data.projected_growth_pct}%)
              </div>
              <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                Velocity: {data.granularity} Aggregation
              </div>
            </div>

            {data.evaluation_metrics && (
              <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
                <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Backtest Accuracy</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#A78BFA", marginTop: 4 }}>
                  {100 - data.evaluation_metrics.mape_pct > 0 ? `${(100 - data.evaluation_metrics.mape_pct).toFixed(1)}%` : "Fair"}
                </div>
                <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                  MAE: ₹{data.evaluation_metrics.mae.toLocaleString()} | RMSE: ₹{data.evaluation_metrics.rmse.toLocaleString()}
                </div>
              </div>
            )}
          </div>

          {/* Historical vs Forecast Timeline Table */}
          <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 18 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>
              Projected Trajectory & Prediction Intervals (95% CI)
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #374151", color: "#94A3B8" }}>
                    <th style={{ padding: "8px 10px" }}>Period</th>
                    <th style={{ padding: "8px 10px" }}>Status</th>
                    <th style={{ padding: "8px 10px" }}>Expected Value</th>
                    <th style={{ padding: "8px 10px" }}>Lower Bound (95%)</th>
                    <th style={{ padding: "8px 10px" }}>Upper Bound (95%)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.forecast_data.map((f, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #1F2937" }}>
                      <td style={{ padding: "9px 10px", color: "#F8FAFC", fontWeight: 600 }}>{f.date}</td>
                      <td style={{ padding: "9px 10px" }}>
                        <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: "rgba(56, 189, 248, 0.2)", color: "#38BDF8", fontWeight: 700 }}>
                          FORECAST
                        </span>
                      </td>
                      <td style={{ padding: "9px 10px", color: "#38BDF8", fontWeight: 700 }}>
                        ₹{f.predicted?.toLocaleString("en-IN")}
                      </td>
                      <td style={{ padding: "9px 10px", color: "#94A3B8" }}>
                        ₹{f.lower_bound?.toLocaleString("en-IN")}
                      </td>
                      <td style={{ padding: "9px 10px", color: "#94A3B8" }}>
                        ₹{f.upper_bound?.toLocaleString("en-IN")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Limitations Banner */}
          <div style={{ background: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.25)", borderRadius: 8, padding: "12px 16px", color: "#FDE68A", fontSize: 12 }}>
            <strong>Predictive Model Disclaimer:</strong> {data.limitations}
          </div>
        </>
      )}
    </div>
  );
};
