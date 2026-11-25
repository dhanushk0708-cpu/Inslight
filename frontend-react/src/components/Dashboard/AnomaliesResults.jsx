export default function AnomaliesResults({ viewData }) {
  return (
    <div className="slide-up">
      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <div className="kpi-card">
          <div className="kpi-header">
            <div className="kpi-label">Found</div>
            <div className={`kpi-icon ${viewData.count > 0 ? "rating" : "units"}`}>
              {viewData.count > 0 ? "⚠️" : "✅"}
            </div>
          </div>
          <div
            className="kpi-value"
            style={{
              color: viewData.count > 0 ? "var(--amber)" : "var(--green)",
            }}
          >
            {viewData.count}
          </div>
        </div>
      </div>

      {viewData.ai_analysis?.map((analysis, index) => (
        <div className={`anomaly-card ${analysis.severity}`} key={`${analysis.metric}-${index}`}>
          <div className="anomaly-metric">
            {analysis.severity === "high"
              ? "🔴"
              : analysis.severity === "medium"
              ? "🟡"
              : "🟢"}{" "}
            {analysis.metric}
          </div>
          <div className="anomaly-desc">{analysis.description}</div>
          <div className="anomaly-action">💡 {analysis.suggestion}</div>
        </div>
      ))}

      {viewData.count === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 36 }}>
          <div style={{ fontSize: 44, marginBottom: 10 }}>✅</div>
          <h3 style={{ fontSize: 16, marginBottom: 4 }}>All Clear</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
            No anomalies detected.
          </p>
        </div>
      )}
    </div>
  );
}
