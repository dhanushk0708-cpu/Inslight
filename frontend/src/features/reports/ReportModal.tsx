"use client";
import React, { useState } from "react";
import { apiRequest } from "../../services/api-client";
import { ReportItem } from "../../types";

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  datasetId?: string;
  customQueryData?: any;
  onReportGenerated?: (report: ReportItem) => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  title: initialTitle,
  datasetId,
  customQueryData,
  onReportGenerated,
}) => {
  const [title, setTitle] = useState(initialTitle || "Executive Business Performance Report");
  const [reportType, setReportType] = useState<"executive" | "sales" | "financial" | "operational" | "detailed">("executive");
  const [format, setFormat] = useState<"pdf" | "excel" | "csv">("pdf");
  const [includeAnomalies, setIncludeAnomalies] = useState(true);
  const [loading, setLoading] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<ReportItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const REPORT_TYPE_CONFIG: Record<string, { label: string; defaultTitle: string; description: string }> = {
    executive: {
      label: "Executive Business Report",
      defaultTitle: "Executive Business Performance Report",
      description: "Comprehensive 6–10 page corporate report covering macro KPIs, revenue trends, regional share, SKU performance, analyst insights & recommendations.",
    },
    sales: {
      label: "Sales Performance Report",
      defaultTitle: "Sales & Regional Distribution Performance Report",
      description: "Focused on revenue growth, transaction volume, regional contribution, and SKU velocity rankings.",
    },
    financial: {
      label: "Financial Performance Report",
      defaultTitle: "Financial Margin & Profitability Analysis Report",
      description: "Evaluates gross turnover, cost of goods sold (COGS), operating margin ratios, and category profitability disparities.",
    },
    operational: {
      label: "Operational Performance Report",
      defaultTitle: "Operational Volume & Risk Assessment Report",
      description: "Concentrates on units sold, order frequency, capacity metrics, and multi-parameter anomaly indicators.",
    },
    detailed: {
      label: "Detailed Analytics Report",
      defaultTitle: "Comprehensive Enterprise Analytics & Governance Report",
      description: "Complete multidimensional breakdown including data completeness scores, ledger records, and metric definitions.",
    },
  };

  const handleTypeChange = (type: "executive" | "sales" | "financial" | "operational" | "detailed") => {
    setReportType(type);
    if (!initialTitle) {
      setTitle(REPORT_TYPE_CONFIG[type].defaultTitle);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: any = {
        title,
        report_format: format,
        report_type: reportType,
        include_anomalies: includeAnomalies,
      };
      if (datasetId) payload.dataset_id = datasetId;
      if (customQueryData) payload.custom_query_data = customQueryData;

      const res = await apiRequest<ReportItem>("/api/v1/reports/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setGeneratedReport(res);
      if (onReportGenerated) onReportGenerated(res);
    } catch (err: any) {
      setError(err?.message || "Failed to generate report.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (reportId: string, name: string, fmt: string) => {
    const ext = fmt === "pdf" ? "pdf" : fmt === "excel" ? "xlsx" : "csv";
    const token = typeof window !== "undefined" ? localStorage.getItem("inslight_token") : "";
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/reports/${reportId}/download`;

    // Fetch with authorization and trigger browser download
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `${name.replace(/\s+/g, "_")}.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch(() => setError("Failed to download file."));
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        backdropFilter: "blur(4px)",
      }}
    >
      <div
        style={{
          background: "var(--bg-card, #1e293b)",
          border: "1px solid var(--border-color, #334155)",
          borderRadius: "12px",
          width: "90%",
          maxWidth: "480px",
          padding: "24px",
          color: "#f8fafc",
          boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 600 }}>📄 Generate Business Report</h3>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "18px" }}
          >
            ✕
          </button>
        </div>

        {error && (
          <div style={{ background: "#7f1d1d", border: "1px solid #991b1b", color: "#fca5a5", padding: "8px 12px", borderRadius: "6px", fontSize: "12px", marginBottom: "14px" }}>
            {error}
          </div>
        )}

        {!generatedReport ? (
          <form onSubmit={handleGenerate}>
            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                Select BI Report Type
              </label>
              <select
                value={reportType}
                onChange={(e) => handleTypeChange(e.target.value as any)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  color: "#f8fafc",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                <option value="executive">👔 Executive Business Report (Full 6–10 Page Audit)</option>
                <option value="sales">📈 Sales & Territorial Performance Report</option>
                <option value="financial">💰 Financial Margin & Profitability Report</option>
                <option value="operational">📦 Operational Volume & Risk Assessment Report</option>
                <option value="detailed">📑 Comprehensive Detailed Analytics Report</option>
              </select>
              <div style={{ fontSize: "11px", color: "#38bdf8", marginTop: "5px", lineHeight: "1.4" }}>
                💡 {REPORT_TYPE_CONFIG[reportType].description}
              </div>
            </div>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                Report Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  color: "#f8fafc",
                  fontSize: "13px",
                }}
              />
            </div>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                Report Format
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
                {(["pdf", "excel", "csv"] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => setFormat(fmt)}
                    style={{
                      padding: "8px",
                      background: format === fmt ? "#2563eb" : "#0f172a",
                      border: `1px solid ${format === fmt ? "#3b82f6" : "#334155"}`,
                      borderRadius: "6px",
                      color: "#f8fafc",
                      fontSize: "12px",
                      fontWeight: 500,
                      cursor: "pointer",
                      textTransform: "uppercase",
                    }}
                  >
                    {fmt === "pdf" ? "📕 PDF" : fmt === "excel" ? "📊 Excel" : "📑 CSV"}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#cbd5e1", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={includeAnomalies}
                  onChange={(e) => setIncludeAnomalies(e.target.checked)}
                />
                Include detected outliers & risk indicators
              </label>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: "transparent",
                  border: "1px solid #334155",
                  color: "#94a3b8",
                  borderRadius: "6px",
                  padding: "8px 16px",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                style={{
                  background: "#2563eb",
                  border: "none",
                  color: "#ffffff",
                  borderRadius: "6px",
                  padding: "8px 18px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: loading ? "wait" : "pointer",
                }}
              >
                {loading ? "Synthesizing Report..." : "Generate Report"}
              </button>
            </div>
          </form>
        ) : (
          <div>
            <div style={{ background: "#064e3b", border: "1px solid #059669", color: "#6ee7b7", padding: "12px", borderRadius: "8px", marginBottom: "16px", fontSize: "13px" }}>
              ✓ Report generated successfully! ({Math.round(generatedReport.file_size / 1024)} KB)
            </div>

            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                type="button"
                onClick={() => handleDownload(generatedReport.id, generatedReport.name, generatedReport.report_format)}
                style={{
                  background: "#10b981",
                  border: "none",
                  color: "#ffffff",
                  borderRadius: "6px",
                  padding: "8px 16px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                ⬇️ Download Now
              </button>
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: "#1e293b",
                  border: "1px solid #475569",
                  color: "#f8fafc",
                  borderRadius: "6px",
                  padding: "8px 16px",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
