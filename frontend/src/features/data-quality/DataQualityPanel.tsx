import React, { useState } from "react";
import { DataQualityReport } from "../../types";

interface DataQualityPanelProps {
  report: DataQualityReport | null;
  loading: boolean;
  onRunAudit: () => void;
  onPreviewCleaned: () => void;
  cleanedPreview?: Array<Record<string, any>> | null;
}

export const DataQualityPanel: React.FC<DataQualityPanelProps> = ({
  report,
  loading,
  onRunAudit,
  onPreviewCleaned,
  cleanedPreview
}) => {
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  const handleShowPreview = () => {
    onPreviewCleaned();
    setShowPreviewModal(true);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Header Banner */}
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
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#F8FAFC" }}>
            🛡️ Intelligent Data Quality Assistant
          </div>
          <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
            Automated schema hygiene audit, missing value checks, and non-destructive remediation.
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            onClick={handleShowPreview}
            className="chat-action-btn"
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            👁️ Cleaned Preview
          </button>
          <button
            type="button"
            onClick={onRunAudit}
            disabled={loading}
            className="chat-action-btn active"
            style={{ fontSize: 12, padding: "6px 16px" }}
          >
            {loading ? "Auditing Dataset..." : "🔍 Run Diagnostic Audit"}
          </button>
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "60px 20px" }}>
          <div style={{ fontSize: 24, marginBottom: 12 }}>🛡️</div>
          <div style={{ color: "#94A3B8", fontSize: 14 }}>Scanning table hygiene and calculating data quality score...</div>
        </div>
      )}

      {!loading && !report && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "#64748B" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📋</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#94A3B8", marginBottom: 6 }}>No Diagnostic Report Yet</div>
          <p style={{ fontSize: 13, maxWidth: 440, margin: "0 auto 20px auto" }}>
            Click &quot;Run Diagnostic Audit&quot; to inspect column completeness, duplicates, and category casing consistency.
          </p>
        </div>
      )}

      {!loading && report && (
        <>
          {/* Quality Score Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
            <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Data Quality Score</div>
              <div
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  color: report.overall_score >= 85 ? "#10B981" : report.overall_score >= 70 ? "#F59E0B" : "#EF4444",
                  marginTop: 4
                }}
              >
                {report.overall_score} / 100
              </div>
              <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                Hygiene Status: <strong style={{ color: "#E2E8F0" }}>{report.quality_grade}</strong>
              </div>
            </div>

            <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Issues Identified</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: "#F8FAFC", marginTop: 4 }}>
                {report.issues_count}
              </div>
              <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                Across {report.total_columns_analyzed} Columns &amp; {report.total_records_analyzed.toLocaleString()} Rows
              </div>
            </div>

            <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase" }}>Preservation Guarantee</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#38BDF8", marginTop: 4 }}>
                100% Non-Destructive
              </div>
              <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                Raw source dataset is never silently modified.
              </div>
            </div>
          </div>

          {/* Issue Register */}
          <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: 18 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>
              Detailed Hygiene Issue Register ({report.issues.length})
            </div>
            {report.issues.length === 0 ? (
              <div style={{ color: "#10B981", fontSize: 13, padding: "10px 0" }}>
                ✓ Clean bill of health: No missing values, duplicate records, or casing discrepancies found.
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #374151", color: "#94A3B8" }}>
                      <th style={{ padding: "8px 10px" }}>Column / Target</th>
                      <th style={{ padding: "8px 10px" }}>Issue Diagnostic</th>
                      <th style={{ padding: "8px 10px" }}>Affected Records</th>
                      <th style={{ padding: "8px 10px" }}>Severity</th>
                      <th style={{ padding: "8px 10px" }}>Actionable Remediation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.issues.map((iss, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #1F2937" }}>
                        <td style={{ padding: "10px", color: "#F8FAFC", fontWeight: 600 }}>{iss.column}</td>
                        <td style={{ padding: "10px", color: "#E2E8F0" }}>{iss.issue_type}</td>
                        <td style={{ padding: "10px", color: "#94A3B8" }}>
                          {iss.affected_records.toLocaleString()} {iss.affected_pct ? `(${iss.affected_pct}%)` : ""}
                        </td>
                        <td style={{ padding: "10px" }}>
                          <span
                            style={{
                              fontSize: 10,
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: 4,
                              background: iss.severity === "HIGH" ? "rgba(239, 68, 68, 0.2)" : "rgba(245, 158, 11, 0.2)",
                              color: iss.severity === "HIGH" ? "#EF4444" : "#F59E0B"
                            }}
                          >
                            {iss.severity}
                          </span>
                        </td>
                        <td style={{ padding: "10px", color: "#CBD5E1", fontSize: 12 }}>
                          {iss.recommendation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* Cleaned Preview Modal */}
      {showPreviewModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <div style={{ background: "#111827", border: "1px solid #374151", borderRadius: 12, padding: 24, width: 800, maxWidth: "90%", maxHeight: "85vh", display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <h3 style={{ margin: 0, color: "#F8FAFC", fontSize: 16 }}>
                Non-Destructive Cleaned Data Preview (Sample Partition)
              </h3>
              <button
                type="button"
                onClick={() => setShowPreviewModal(false)}
                style={{ background: "none", border: "none", color: "#94A3B8", fontSize: 18, cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ color: "#94A3B8", fontSize: 12, marginBottom: 12 }}>
              Demonstrates automatic trimming, casing standardization, and null imputation without modifying original disk storage.
            </div>

            <div style={{ flex: 1, overflow: "auto", border: "1px solid #1F2937", borderRadius: 8 }}>
              {cleanedPreview && cleanedPreview.length > 0 ? (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "#1F2937", color: "#94A3B8" }}>
                      {Object.keys(cleanedPreview[0]).map((k) => (
                        <th key={k} style={{ padding: "8px 10px" }}>{k}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cleanedPreview.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid #1F2937" }}>
                        {Object.values(row).map((v: any, cIdx) => (
                          <td key={cIdx} style={{ padding: "8px 10px", color: "#E2E8F0" }}>{String(v)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: 40, textAlign: "center", color: "#64748B" }}>Loading preview...</div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}>
              <button
                type="button"
                onClick={() => setShowPreviewModal(false)}
                className="chat-action-btn active"
                style={{ padding: "8px 20px" }}
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
