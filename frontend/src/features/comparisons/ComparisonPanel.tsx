import React, { useState } from "react";
import { ComparisonData } from "../../types";

interface ComparisonPanelProps {
  data: ComparisonData | null;
  loading: boolean;
  onRunComparison: (mode: string, metric?: string, dim?: string) => void;
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({ data, loading, onRunComparison }) => {
  const [mode, setMode] = useState<"period" | "segment">("period");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Top Selector Bar */}
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
          gap: 12
        }}
      >
        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            onClick={() => {
              setMode("period");
              onRunComparison("period");
            }}
            className={`chat-action-btn ${mode === "period" ? "active" : ""}`}
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            📅 Period Comparison (MoM)
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("segment");
              onRunComparison("segment");
            }}
            className={`chat-action-btn ${mode === "segment" ? "active" : ""}`}
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            🏢 Segment Benchmark
          </button>
        </div>

        <button
          type="button"
          onClick={() => onRunComparison(mode)}
          disabled={loading}
          className="chat-action-btn active"
          style={{ fontSize: 12, padding: "6px 16px" }}
        >
          {loading ? "Computing..." : "🔄 Refresh Benchmark"}
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "60px 20px" }}>
          <div style={{ fontSize: 24, marginBottom: 12 }}>⚖️</div>
          <div style={{ color: "#94A3B8", fontSize: 14 }}>Executing comparative delta and share calculations...</div>
        </div>
      )}

      {!loading && !data && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "#64748B" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>⚖️</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#94A3B8", marginBottom: 6 }}>Comparative Business Analytics</div>
          <p style={{ fontSize: 13, maxWidth: 440, margin: "0 auto" }}>
            Select a comparison mode to contrast performance across periods or dimensional segments.
          </p>
        </div>
      )}

      {!loading && data && data.status === "success" && (
        <>
          {/* Latest Metric Shift Card */}
          {data.latest_comparison && (
            <div style={{ background: "linear-gradient(135deg, #1E293B 0%, #0F172A 100%)", border: "1px solid rgba(148, 163, 184, 0.2)", borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 1, color: "#94A3B8", fontWeight: 700 }}>
                {data.comparison_type} ({data.latest_comparison.period_label})
              </div>
              <div style={{ fontSize: 24, fontWeight: 800, color: data.latest_comparison.percentage_change >= 0 ? "#10B981" : "#EF4444", marginTop: 4 }}>
                {data.latest_comparison.formatted_change}
              </div>
              <div style={{ fontSize: 13, color: "#CBD5E1", marginTop: 4 }}>
                Current: <strong>₹{data.latest_comparison.current_value.toLocaleString("en-IN")}</strong> vs Baseline: <strong>₹{data.latest_comparison.baseline_value.toLocaleString("en-IN")}</strong>
              </div>
            </div>
          )}

          {data.segment_a && data.segment_b && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
                <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Lead Segment</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#38BDF8", marginTop: 4 }}>
                  {data.segment_a.name}
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginTop: 2 }}>
                  ₹{data.segment_a.value.toLocaleString("en-IN")}
                </div>
              </div>
              <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
                <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Trailing Segment</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#94A3B8", marginTop: 4 }}>
                  {data.segment_b.name}
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginTop: 2 }}>
                  ₹{data.segment_b.value.toLocaleString("en-IN")}
                </div>
              </div>
            </div>
          )}

          {/* Timeline Table */}
          {data.timeline && (
            <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 18 }}>
              <div className="card-title" style={{ marginBottom: 12 }}>
                Sequential Period Comparison Trajectory
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #374151", color: "#94A3B8" }}>
                      <th style={{ padding: "8px 10px" }}>Period Comparison</th>
                      <th style={{ padding: "8px 10px" }}>Current Period</th>
                      <th style={{ padding: "8px 10px" }}>Baseline Period</th>
                      <th style={{ padding: "8px 10px" }}>Absolute Delta</th>
                      <th style={{ padding: "8px 10px" }}>Percentage Shift</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.timeline.map((row, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #1F2937" }}>
                        <td style={{ padding: "9px 10px", color: "#F8FAFC", fontWeight: 600 }}>{row.period_label}</td>
                        <td style={{ padding: "9px 10px", color: "#E2E8F0" }}>₹{row.current_value.toLocaleString("en-IN")}</td>
                        <td style={{ padding: "9px 10px", color: "#94A3B8" }}>₹{row.baseline_value.toLocaleString("en-IN")}</td>
                        <td style={{ padding: "9px 10px", color: row.absolute_difference >= 0 ? "#10B981" : "#EF4444", fontWeight: 700 }}>
                          ₹{row.absolute_difference.toLocaleString("en-IN")}
                        </td>
                        <td style={{ padding: "9px 10px" }}>
                          <span
                            style={{
                              padding: "2px 6px",
                              borderRadius: 4,
                              fontSize: 11,
                              fontWeight: 700,
                              background: row.percentage_change >= 0 ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                              color: row.percentage_change >= 0 ? "#10B981" : "#EF4444"
                            }}
                          >
                            {row.formatted_change}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
