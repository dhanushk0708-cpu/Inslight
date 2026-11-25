import BarChart from "../Charts/BarChart";
import DataTable from "../Common/DataTable";
import { fmt } from "../../utils/formatters";

export default function WhatIfResults({
  loading,
  runWhatIf,
  setWiDiscount,
  setWiPrice,
  setWiUnits,
  viewData,
  wiDiscount,
  wiPrice,
  wiUnits,
}) {
  return (
    <div className="slide-up">
      <div className="whatif-panel">
        <div className="card-title">Scenario Parameters</div>
        <form id="whatif-form" name="whatif-form" onSubmit={(event) => event.preventDefault()}>
          <div className="slider-group">
            <div className="slider-header">
              <label className="slider-label" htmlFor="wi-price">
                💰 Price
              </label>
              <span className="slider-val">
                {wiPrice > 0 ? "+" : ""}
                {wiPrice}%
              </span>
            </div>
            <input
              id="wi-price"
              name="wi-price"
              className="slider-input"
              type="range"
              min={-50}
              max={50}
              value={wiPrice}
              onChange={(event) => setWiPrice(Number(event.target.value))}
              aria-label="Price"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <label className="slider-label" htmlFor="wi-disc">
                🏷️ Discount
              </label>
              <span className="slider-val">
                {wiDiscount > 0 ? "+" : ""}
                {wiDiscount}%
              </span>
            </div>
            <input
              id="wi-disc"
              name="wi-disc"
              className="slider-input"
              type="range"
              min={-50}
              max={50}
              value={wiDiscount}
              onChange={(event) => setWiDiscount(Number(event.target.value))}
              aria-label="Discount"
            />
          </div>

          <div className="slider-group">
            <div className="slider-header">
              <label className="slider-label" htmlFor="wi-units">
                📦 Volume
              </label>
              <span className="slider-val">
                {wiUnits > 0 ? "+" : ""}
                {wiUnits}%
              </span>
            </div>
            <input
              id="wi-units"
              name="wi-units"
              className="slider-input"
              type="range"
              min={-50}
              max={50}
              value={wiUnits}
              onChange={(event) => setWiUnits(Number(event.target.value))}
              aria-label="Volume"
            />
          </div>

          <button
            id="btn-run-whatif"
            name="btn-run-whatif"
            className="btn btn-primary"
            type="button"
            onClick={runWhatIf}
            disabled={loading}
            style={{ marginTop: 8, width: "100%" }}
          >
            ▶ Run Scenario
          </button>
        </form>
      </div>

      {viewData && !viewData.error && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-header">
                <div className="kpi-label">Current</div>
                <div className="kpi-icon revenue">💰</div>
              </div>
              <div className="kpi-value">{fmt(viewData.current?.revenue)}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-header">
                <div className="kpi-label">Projected</div>
                <div className="kpi-icon revenue">🎯</div>
              </div>
              <div
                className="kpi-value"
                style={{
                  color:
                    viewData.change?.revenue_diff >= 0
                      ? "var(--green)"
                      : "var(--red)",
                }}
              >
                {fmt(viewData.projected?.revenue)}
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-header">
                <div className="kpi-label">Impact</div>
                <div
                  className={`kpi-icon ${
                    viewData.change?.revenue_pct_change >= 0 ? "units" : "orders"
                  }`}
                >
                  {viewData.change?.revenue_pct_change >= 0 ? "📈" : "📉"}
                </div>
              </div>
              <div
                className="kpi-value"
                style={{
                  color:
                    viewData.change?.revenue_pct_change >= 0
                      ? "var(--green)"
                      : "var(--red)",
                }}
              >
                {viewData.change?.revenue_pct_change >= 0 ? "+" : ""}
                {viewData.change?.revenue_pct_change}%
              </div>
            </div>
          </div>

          {viewData.ai_commentary && (
            <div className="narrative">{viewData.ai_commentary}</div>
          )}
          {viewData.monthly_comparison?.length > 0 && (
            <BarChart
              data={viewData.monthly_comparison}
              xKey="month"
              yKey="projected_revenue"
              title="Projected Monthly Revenue"
            />
          )}
          {viewData.category_impact?.length > 0 && (
            <DataTable data={viewData.category_impact} title="Category Impact" />
          )}
        </>
      )}
    </div>
  );
}
