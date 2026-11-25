import React from "react";
import { AnomalyData } from "../../types";

interface AnomaliesPanelProps {
  data: AnomalyData | null;
}

export const AnomaliesPanel: React.FC<AnomaliesPanelProps> = ({ data }) => {
  if (!data) return null;

  return (
    <div>
      <div className="kpi-grid" style={{ marginBottom: 16 }}>
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-label">Anomalies Detected</div>
            <div className="kpi-icon">{data.count > 0 ? "⚠️" : "✅"}</div>
          </div>
          <div
            className="kpi-value"
            style={{ color: data.count > 0 ? "var(--amber)" : "var(--green)" }}
          >
            {data.count}
          </div>
        </div>
      </div>

      {data.ai_analysis?.map((a, i) => (
        <div className={`anomaly-card ${a.severity}`} key={i}>
          <div className="anomaly-metric">
            {a.severity === "high" ? "🔴" : a.severity === "medium" ? "🟡" : "🟢"} {a.metric}
          </div>
          <div className="anomaly-desc">{a.description}</div>
          <div className="anomaly-action">💡 {a.suggestion}</div>
        </div>
      ))}

      {data.count === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 36 }}>
          <div style={{ fontSize: 40, marginBottom: 10 }}>✅</div>
          <h3 style={{ fontSize: 16, marginBottom: 4 }}>All Clear</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No statistically significant anomalies detected.</p>
        </div>
      )}
    </div>
  );
};
