"use client";
import React, { useState } from "react";
import { Maximize2, ChevronDown, ChevronRight, RefreshCw, FileText } from "lucide-react";
import { DeepDiveData, ChartConfig } from "../../types";
import { KPIGrid } from "./KPIGrid";
import { ChartRenderer } from "../../components/charts/ChartRenderer";
import { DataTable } from "../../components/common/DataTable";
import { MarkdownRenderer } from "../../components/common/MarkdownRenderer";

interface DeepDiveViewProps {
  data: DeepDiveData | null;
  highlightedSection?: string | null;
  onRefresh?: () => void;
  onExportPdf?: () => void;
  onAskFollowUp?: (question: string) => void;
}

const SECTIONS = [
  { id: "dd-overview", label: "1. Overview" },
  { id: "dd-revenue", label: "2. Revenue" },
  { id: "dd-profitability", label: "3. Profitability" },
  { id: "dd-products", label: "4. Products" },
  { id: "dd-regions", label: "5. Regions" },
  { id: "dd-customers", label: "6. Customers" },
  { id: "dd-trends", label: "7. Trends & Forecast" },
  { id: "dd-risks", label: "8. Risks & Anomalies" },
  { id: "dd-opportunities", label: "9. Opportunities" },
  { id: "dd-actions", label: "10. Action Plan" },
];

export const DeepDiveView: React.FC<DeepDiveViewProps> = ({
  data,
  highlightedSection,
  onRefresh,
  onExportPdf,
  onAskFollowUp,
}) => {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [enlargedChart, setEnlargedChart] = useState<(ChartConfig & { interpretation?: string }) | null>(null);

  if (!data) {
    return (
      <div className="empty-state-card">
        <div className="empty-state-icon">🔬</div>
        <h4 className="empty-state-title">Deep Dive Research Workspace</h4>
        <p className="empty-state-desc">
          Run a Deep Dive Business Analysis to generate a 10-section executive report with KPIs, revenue/profitability breakdowns, product &amp; regional intelligence, forecasts, and prioritized actions.
        </p>
        {onRefresh && (
          <button type="button" className="btn btn-primary" onClick={onRefresh} style={{ marginTop: 14 }}>
            🔬 Run Deep Dive Analysis
          </button>
        )}
      </div>
    );
  }

  const toggleSection = (id: string) => {
    setCollapsed((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const setAllCollapsed = (val: boolean) => {
    const next: Record<string, boolean> = {};
    SECTIONS.forEach((s) => {
      next[s.id] = val;
    });
    setCollapsed(next);
  };

  const jumpTo = (id: string) => {
    setCollapsed((prev) => ({ ...prev, [id]: false }));
    setTimeout(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

  const charts = data.charts || {};
  const meta = data.dataset_metadata;
  const exec = data.executive_summary;
  const rev = data.revenue_analysis;
  const prof = data.profitability_analysis;
  const prod = data.product_analysis;
  const reg = data.regional_analysis;
  const cust = data.customer_analysis;
  const trendFc = data.trend_and_forecast;
  const risks = data.anomalies_and_risks?.risks || [];
  const anomalies = data.anomalies_and_risks?.anomalies;
  const opps = data.opportunities || [];
  const plan = data.strategic_action_plan;

  const renderChartCard = (key: string) => {
    const cfg = charts[key];
    if (!cfg || !cfg.data?.length) return null;
    return (
      <div key={key} style={{ position: "relative" }}>
        <button
          type="button"
          onClick={() => setEnlargedChart(cfg)}
          title="Enlarge chart"
          style={{
            position: "absolute",
            top: 14,
            right: 14,
            zIndex: 4,
            background: "rgba(15, 23, 42, 0.85)",
            border: "1px solid var(--border)",
            color: "#9aa4bc",
            borderRadius: 6,
            padding: "4px 7px",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
            fontSize: 10.5,
          }}
        >
          <Maximize2 size={11} />
          <span>Enlarge</span>
        </button>
        <ChartRenderer config={cfg} />
        {cfg.interpretation && (
          <div style={{ fontSize: 11.5, color: "#9aa4bc", marginTop: 6, padding: "0 4px", lineHeight: 1.45 }}>
            💡 {cfg.interpretation}
          </div>
        )}
      </div>
    );
  };

  const SectionShell: React.FC<{ id: string; title: string; badge?: string; children: React.ReactNode }> = ({
    id,
    title,
    badge,
    children,
  }) => {
    const isCollapsed = !!collapsed[id];
    const isHighlighted = highlightedSection === id;
    return (
      <section
        id={id}
        className="card"
        style={{
          borderColor: isHighlighted ? "rgba(56, 189, 248, 0.65)" : undefined,
          boxShadow: isHighlighted ? "0 0 24px rgba(56, 189, 248, 0.15)" : undefined,
          scrollMarginTop: 70,
        }}
      >
        <div
          onClick={() => toggleSection(id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && toggleSection(id)}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            cursor: "pointer",
            marginBottom: isCollapsed ? 0 : 14,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {isCollapsed ? <ChevronRight size={16} color="#818cf8" /> : <ChevronDown size={16} color="#818cf8" />}
            <h3 style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc", margin: 0 }}>{title}</h3>
            {badge && <span className="results-badge">{badge}</span>}
          </div>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{isCollapsed ? "Expand" : "Collapse"}</span>
        </div>
        {!isCollapsed && <div>{children}</div>}
      </section>
    );
  };

  return (
    <div className="view-enter" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Sticky Toolbar & Section Navigation */}
      <div
        style={{
          position: "sticky",
          top: -22,
          zIndex: 12,
          background: "rgba(9, 13, 24, 0.92)",
          backdropFilter: "blur(12px)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "10px 12px",
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            {meta && (
              <span className="results-chip">
                📁 {meta.filename} • {meta.row_count.toLocaleString()} rows • Quality {meta.data_quality_score}%
              </span>
            )}
            {meta?.date_coverage && (
              <span className="results-chip">
                📅 {meta.date_coverage.start} → {meta.date_coverage.end}
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <button type="button" className="btn btn-ghost" onClick={() => setAllCollapsed(false)} style={{ fontSize: 11 }}>
              Expand All
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setAllCollapsed(true)} style={{ fontSize: 11 }}>
              Collapse All
            </button>
            {onRefresh && (
              <button type="button" className="btn btn-ghost" onClick={onRefresh} style={{ fontSize: 11 }}>
                <RefreshCw size={12} /> Refresh
              </button>
            )}
            {onExportPdf && (
              <button type="button" className="btn btn-primary" onClick={onExportPdf} style={{ fontSize: 11, padding: "5px 12px" }}>
                <FileText size={12} /> Export PDF / Excel
              </button>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: 5, overflowX: "auto", paddingBottom: 2 }}>
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => jumpTo(s.id)}
              className={`chat-action-btn ${highlightedSection === s.id ? "active" : ""}`}
              style={{ fontSize: 10.5, padding: "4px 9px" }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* SECTION 1 — EXECUTIVE OVERVIEW */}
      <SectionShell id="dd-overview" title="1. Executive Overview" badge="Summary">
        {exec?.kpi_cards?.length ? <KPIGrid cards={exec.kpi_cards} /> : null}
        {(exec?.health_summary || data.root_cause_analysis) && (
          <div className="narrative">
            <MarkdownRenderer content={exec?.health_summary || data.root_cause_analysis} />
          </div>
        )}
        {exec?.key_findings && exec.key_findings.length > 0 && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10, marginBottom: 12 }}>
            {exec.key_findings.map((f, idx) => (
              <div key={idx} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", fontSize: 12.5, color: "#e2e8f0" }}>
                <strong style={{ color: "var(--accent-light)" }}>Finding #{idx + 1}:</strong> {f}
              </div>
            ))}
          </div>
        )}
        {exec?.warnings && exec.warnings.length > 0 && (
          <div style={{ background: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.25)", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#fcd34d" }}>
            <strong>Data Coverage &amp; Limitations:</strong>
            <ul style={{ margin: "4px 0 0 18px" }}>
              {exec.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </SectionShell>

      {/* SECTION 2 — REVENUE PERFORMANCE */}
      <SectionShell id="dd-revenue" title="2. Revenue Performance" badge={rev?.mom_growth_pct != null ? `MoM ${rev.mom_growth_pct >= 0 ? "+" : ""}${rev.mom_growth_pct}%` : undefined}>
        <div className="chart-grid">
          {renderChartCard("revenue_trend")}
          {renderChartCard("monthly_growth")}
          {renderChartCard("revenue_by_category")}
          {renderChartCard("revenue_share")}
        </div>
        {rev?.by_category?.length > 0 && (
          <DataTable data={rev.by_category} title="Category Revenue Contribution" />
        )}
      </SectionShell>

      {/* SECTION 3 — PROFITABILITY */}
      <SectionShell id="dd-profitability" title="3. Profitability & Margin Analysis" badge={prof?.available ? `${prof.gross_margin_pct}% Margin` : "Unavailable"}>
        {!prof?.available ? (
          <div style={{ padding: 14, background: "rgba(255,255,255,0.02)", borderRadius: 8, fontSize: 12.5, color: "var(--text-muted)" }}>
            ℹ️ {prof?.reason || "Profitability analysis unavailable because cost/profit columns are not present in this dataset."}
          </div>
        ) : (
          <>
            <div className="chart-grid">
              {renderChartCard("profit_trend")}
              {renderChartCard("profit_by_category")}
              {renderChartCard("product_margins")}
              {renderChartCard("revenue_vs_profit_scatter")}
            </div>
          </>
        )}
      </SectionShell>

      {/* SECTION 4 — PRODUCT INTELLIGENCE */}
      <SectionShell id="dd-products" title="4. Product Intelligence" badge={prod?.available ? `${prod.total_products} Products` : "N/A"}>
        {!prod?.available ? (
          <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>No product dimension column detected in this dataset.</div>
        ) : (
          <>
            {prod.inventory_note && (
              <div style={{ fontSize: 12, color: "#93c5fd", marginBottom: 12, background: "rgba(59,130,246,0.08)", padding: "8px 12px", borderRadius: 8 }}>
                ℹ️ {prod.inventory_note}
              </div>
            )}
            <div className="chart-grid">
              {renderChartCard("top_products")}
              {renderChartCard("bottom_products")}
            </div>
            {prod.top_products?.length > 0 && <DataTable data={prod.top_products} title="Top Products Breakdown" />}
          </>
        )}
      </SectionShell>

      {/* SECTION 5 — REGIONAL INTELLIGENCE */}
      <SectionShell id="dd-regions" title="5. Regional Intelligence" badge={reg?.available ? `${reg.regions.length} Regions` : "N/A"}>
        {!reg?.available ? (
          <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>No regional/geography column detected in this dataset.</div>
        ) : (
          <>
            <div className="chart-grid single">{renderChartCard("regional_performance")}</div>
            {reg.regions?.length > 0 && <DataTable data={reg.regions} title="Regional Performance Ranking" />}
          </>
        )}
      </SectionShell>

      {/* SECTION 6 — CUSTOMER INTELLIGENCE */}
      <SectionShell id="dd-customers" title="6. Customer Intelligence" badge={cust?.available ? `${cust.unique_customers} Customers` : "Unavailable"}>
        {!cust?.available ? (
          <div style={{ padding: 14, background: "rgba(255,255,255,0.02)", borderRadius: 8, fontSize: 12.5, color: "var(--text-muted)" }}>
            ℹ️ {cust?.reason || "No customer identifier column detected in this dataset."}
          </div>
        ) : (
          <>
            <div className="chart-grid single">{renderChartCard("customer_concentration")}</div>
            {cust.top_customers?.length > 0 && <DataTable data={cust.top_customers} title="Top Customers by Revenue" />}
          </>
        )}
      </SectionShell>

      {/* SECTION 7 — TRENDS & FORECASTS */}
      <SectionShell id="dd-trends" title="7. Trends & Predictive Forecast" badge={trendFc?.forecast?.status === "success" ? trendFc.forecast.method_used : "Notice"}>
        {trendFc?.forecast?.status === "success" ? (
          <>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
              <span className="results-chip">Model: {trendFc.forecast.method_used}</span>
              <span className="results-chip">Projected 30d Total: {trendFc.forecast.formatted_forecast_total}</span>
              <span className="results-chip">MAPE: {trendFc.forecast.metrics?.mape ?? "N/A"}%</span>
            </div>
            <div className="chart-grid single">{renderChartCard("forecast_vs_actual")}</div>
          </>
        ) : (
          <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
            ℹ️ {trendFc?.forecast?.message || "Insufficient historical date points for forecasting."}
          </div>
        )}
      </SectionShell>

      {/* SECTION 8 — RISKS & ANOMALIES */}
      <SectionShell id="dd-risks" title="8. Risks & Statistical Anomalies" badge={`${risks.length} Risks`}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12, marginBottom: 14 }}>
          {risks.map((r: any, idx: number) => (
            <div key={idx} className={`anomaly-card ${r.severity === "critical" ? "high" : r.severity === "info" ? "low" : ""}`} style={{ marginBottom: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 700, fontSize: 13, color: "#f8fafc" }}>{r.title}</span>
                <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>{r.severity}</span>
              </div>
              <div style={{ fontSize: 12, color: "#d1d5db", marginBottom: 6 }}>{r.business_interpretation || r.impact}</div>
              <div style={{ fontSize: 11, color: "#9aa4bc" }}>
                <strong>Metric:</strong> {r.supporting_metric} ({r.actual_value})
              </div>
              <div style={{ fontSize: 11.5, color: "#fca5a5", marginTop: 6 }}>
                🛡️ <strong>Mitigation:</strong> {r.mitigation}
              </div>
            </div>
          ))}
        </div>
        {anomalies?.anomalies?.length > 0 && (
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Detected {anomalies.total_anomalies} statistical anomaly points across monitored metrics.
          </div>
        )}
      </SectionShell>

      {/* SECTION 9 — OPPORTUNITIES */}
      <SectionShell id="dd-opportunities" title="9. Growth Opportunities" badge={`${opps.length} Identified`}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
          {opps.map((o: any, idx: number) => (
            <div
              key={idx}
              style={{
                background: "rgba(16, 185, 129, 0.05)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                borderRadius: 10,
                padding: 14,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 6, marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: "#10b981" }}>Opportunity #{o.rank || idx + 1}</span>
                {o.is_hypothesis && (
                  <span style={{ fontSize: 9.5, fontWeight: 700, color: "#fbbf24", background: "rgba(251,191,36,0.12)", padding: "2px 6px", borderRadius: 4 }}>
                    HYPOTHESIS
                  </span>
                )}
              </div>
              <h5 style={{ fontSize: 13.5, fontWeight: 700, color: "#f8fafc", margin: "0 0 6px 0" }}>{o.title}</h5>
              <p style={{ fontSize: 12, color: "#9ca3af", margin: "0 0 8px 0" }}>{o.business_interpretation || o.impact}</p>
              <div style={{ fontSize: 11, color: "#d1d5db", marginBottom: 8 }}>
                <strong>Metric:</strong> {o.supporting_metric} — {o.actual_value}
              </div>
              <div style={{ fontSize: 11.5, color: "#6ee7b7" }}>💡 {o.recommendation}</div>
            </div>
          ))}
        </div>
      </SectionShell>

      {/* SECTION 10 — STRATEGIC ACTION PLAN */}
      <SectionShell id="dd-actions" title="10. Strategic Action Plan" badge="Prioritized">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 14 }}>
          <div>
            <h5 style={{ fontSize: 12.5, fontWeight: 700, color: "#f87171", marginBottom: 8, textTransform: "uppercase" }}>
              Short-Term Priorities (Immediate)
            </h5>
            {(plan?.short_term || []).map((item: any, idx: number) => (
              <div key={idx} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: 12, marginBottom: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>{item.problem}</div>
                <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 4 }}>{item.action}</div>
                <div style={{ fontSize: 11, color: "#818cf8", marginTop: 6 }}>
                  Monitor: {item.metric_to_monitor} • Difficulty: {item.difficulty}
                </div>
              </div>
            ))}
          </div>
          <div>
            <h5 style={{ fontSize: 12.5, fontWeight: 700, color: "#34d399", marginBottom: 8, textTransform: "uppercase" }}>
              Medium-Term Growth Initiatives
            </h5>
            {(plan?.medium_term || []).map((item: any, idx: number) => (
              <div key={idx} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: 12, marginBottom: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>{item.problem}</div>
                <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 4 }}>{item.action}</div>
                <div style={{ fontSize: 11, color: "#818cf8", marginTop: 6 }}>
                  Monitor: {item.metric_to_monitor} • Difficulty: {item.difficulty}
                </div>
              </div>
            ))}
          </div>
        </div>
        {onAskFollowUp && (
          <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" className="chat-suggestion-chip" onClick={() => onAskFollowUp("Which products generate the highest profit?")}>
              Ask: Highest-profit products?
            </button>
            <button type="button" className="chat-suggestion-chip" onClick={() => onAskFollowUp("Why is our top category concentrated?")}>
              Ask: Category concentration?
            </button>
          </div>
        )}
      </SectionShell>

      {/* Chart Enlargement Modal */}
      {enlargedChart && (
        <div
          onClick={() => setEnlargedChart(null)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(3, 7, 18, 0.85)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ width: "100%", maxWidth: 920, background: "#0f1524", border: "1px solid var(--border-active)", borderRadius: 16, padding: 20 }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{enlargedChart.title}</h4>
              <button type="button" className="btn btn-ghost" onClick={() => setEnlargedChart(null)}>
                ✕ Close
              </button>
            </div>
            <ChartRenderer config={enlargedChart} />
            {enlargedChart.interpretation && (
              <p style={{ fontSize: 12.5, color: "#9aa4bc", marginTop: 10 }}>{enlargedChart.interpretation}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
