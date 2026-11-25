import React from "react";
import { RootCauseData } from "../../types";

interface RootCausePanelProps {
  data: RootCauseData | null;
  loading: boolean;
  onRefresh: () => void;
}

export const RootCausePanel: React.FC<RootCausePanelProps> = ({ data, loading, onRefresh }) => {
  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px 20px" }}>
        <div style={{ fontSize: 24, marginBottom: 12 }}>🔬</div>
        <div style={{ color: "#94A3B8", fontSize: 14 }}>Decomposing metric variance across dimensions...</div>
      </div>
    );
  }

  if (!data || data.status !== "success") {
    return (
      <div style={{ textAlign: "center", padding: "60px 20px", color: "#64748B" }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
        <div style={{ fontSize: 16, fontWeight: 600, color: "#94A3B8", marginBottom: 6 }}>No Active Root Cause Investigation</div>
        <p style={{ fontSize: 13, maxWidth: 440, margin: "0 auto 20px auto" }}>
          {data?.message || "Select a dataset and run Root Cause Analysis to explain why key business metrics shifted."}
        </p>
        <button
          type="button"
          onClick={onRefresh}
          className="chat-action-btn active"
          style={{ padding: "8px 20px" }}
        >
          🔬 Run Root Cause Analysis
        </button>
      </div>
    );
  }

  const isDecline = data.direction === "decline";
  const badgeColor = isDecline ? "#EF4444" : "#10B981";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Overview Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)",
          border: "1px solid rgba(148, 163, 184, 0.15)",
          borderRadius: 12,
          padding: "20px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16
        }}
      >
        <div>
          <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 1, color: "#94A3B8", fontWeight: 700 }}>
            Identified Business Variance ({data.period_label})
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#F8FAFC", marginTop: 4 }}>
            {data.metric.toUpperCase()}: <span style={{ color: badgeColor }}>{data.formatted_change} ({data.percentage_change > 0 ? "+" : ""}{data.percentage_change}%)</span>
          </div>
          <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 4 }}>
            Baseline: <strong style={{ color: "#E2E8F0" }}>{data.formatted_baseline}</strong> ➔ Current: <strong style={{ color: "#E2E8F0" }}>{data.formatted_current}</strong>
          </div>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          className="chat-action-btn"
          style={{ padding: "8px 16px", fontSize: 12 }}
        >
          🔄 Re-Analyze
        </button>
      </div>

      {/* Structural Price-Volume Decomposition */}
      {data.price_volume_decomposition && (
        <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 18 }}>
          <div className="card-title" style={{ marginBottom: 12 }}>
            Structural Driver Decomposition (Price vs Volume)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
            <div style={{ background: "#1F2937", padding: 14, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Primary Driver</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#38BDF8", marginTop: 4 }}>
                {data.price_volume_decomposition.primary_driver}
              </div>
            </div>
            <div style={{ background: "#1F2937", padding: 14, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Volume Effect</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: data.price_volume_decomposition.volume_effect < 0 ? "#EF4444" : "#10B981", marginTop: 4 }}>
                {data.price_volume_decomposition.volume_effect_share_pct}% of total shift
              </div>
              <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>
                Orders: {data.price_volume_decomposition.baseline_volume.toLocaleString()} ➔ {data.price_volume_decomposition.current_volume.toLocaleString()}
              </div>
            </div>
            <div style={{ background: "#1F2937", padding: 14, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>ASP / Price Effect</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: data.price_volume_decomposition.price_effect < 0 ? "#EF4444" : "#10B981", marginTop: 4 }}>
                {data.price_volume_decomposition.price_effect_share_pct}% of total shift
              </div>
              <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>
                Mean Price: ₹{data.price_volume_decomposition.baseline_asp} ➔ ₹{data.price_volume_decomposition.current_asp}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Contributing Segments */}
      <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 18 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>
          Top Contributing Segments ({data.top_contributors.length} Drivers)
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #374151", color: "#94A3B8" }}>
                <th style={{ padding: "8px 10px" }}>Dimension</th>
                <th style={{ padding: "8px 10px" }}>Segment</th>
                <th style={{ padding: "8px 10px" }}>Baseline</th>
                <th style={{ padding: "8px 10px" }}>Current</th>
                <th style={{ padding: "8px 10px" }}>Variance</th>
                <th style={{ padding: "8px 10px" }}>Contribution Share</th>
              </tr>
            </thead>
            <tbody>
              {data.top_contributors.map((c, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #1F2937" }}>
                  <td style={{ padding: "10px", color: "#94A3B8" }}>{c.dimension}</td>
                  <td style={{ padding: "10px", color: "#F8FAFC", fontWeight: 600 }}>{c.segment}</td>
                  <td style={{ padding: "10px", color: "#94A3B8" }}>₹{c.baseline_val.toLocaleString("en-IN")}</td>
                  <td style={{ padding: "10px", color: "#E2E8F0" }}>₹{c.current_val.toLocaleString("en-IN")}</td>
                  <td style={{ padding: "10px", color: c.delta < 0 ? "#EF4444" : "#10B981", fontWeight: 700 }}>
                    {c.formatted_delta}
                  </td>
                  <td style={{ padding: "10px" }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 700,
                        background: Math.abs(c.contribution_pct) >= 30 ? "rgba(239, 68, 68, 0.2)" : "rgba(59, 130, 246, 0.2)",
                        color: Math.abs(c.contribution_pct) >= 30 ? "#FCA5A5" : "#93C5FD"
                      }}
                    >
                      {Math.abs(c.contribution_pct)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grounded Hypotheses & Correlation Caveat */}
      <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 18 }}>
        <div className="card-title" style={{ marginBottom: 10 }}>Evidence-Backed Explanations</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {data.hypotheses.map((h, i) => (
            <div key={i} style={{ background: "#1F2937", padding: 12, borderRadius: 8, borderLeft: `3px solid ${h.confidence === "HIGH" ? "#10B981" : "#F59E0B"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, color: "#F8FAFC", fontSize: 13 }}>{h.factor}</span>
                <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: "#374151", color: "#94A3B8", fontWeight: 700 }}>
                  CONFIDENCE: {h.confidence}
                </span>
              </div>
              <div style={{ color: "#CBD5E1", fontSize: 12, marginTop: 4 }}>{h.evidence}</div>
              <div style={{ color: "#94A3B8", fontSize: 11, marginTop: 2, fontStyle: "italic" }}>
                {h.relationship} (Distinguishing correlation from causation)
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Actionable Follow-Ups */}
      <div style={{ background: "#0F172A", border: "1px solid #1E293B", borderRadius: 12, padding: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "#38BDF8", marginBottom: 8, textTransform: "uppercase" }}>
          Recommended Operations Audit
        </div>
        <ul style={{ margin: 0, paddingLeft: 18, color: "#CBD5E1", fontSize: 13, lineHeight: "22px" }}>
          {data.recommended_investigations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
