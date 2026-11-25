"use client";
import React, { useState, useEffect, useCallback } from "react";
import { apiRequest } from "../../services/api-client";
import { ReportItem, ScheduledReportItem, GmailStatus, Dataset } from "../../types";
import { ReportModal } from "./ReportModal";
import { EmailComposerModal } from "./EmailComposerModal";

export const ReportsView: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [schedules, setSchedules] = useState<ScheduledReportItem[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"history" | "schedules">("history");

  // Modals
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [emailingReport, setEmailingReport] = useState<ReportItem | null>(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  // New Schedule Form state
  const [newScheduleDataset, setNewScheduleDataset] = useState("");
  const [newScheduleName, setNewScheduleName] = useState("");
  const [newScheduleFreq, setNewScheduleFreq] = useState<"weekly" | "monthly">("weekly");
  const [newScheduleFormat, setNewScheduleFormat] = useState<"pdf" | "excel" | "both">("pdf");
  const [newScheduleRecipients, setNewScheduleRecipients] = useState("");
  const [newScheduleSubject, setNewScheduleSubject] = useState("");
  const [newScheduleBody, setNewScheduleBody] = useState("");
  const [scheduleError, setScheduleError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [reps, scheds, dsets, gStatus] = await Promise.all([
        apiRequest<ReportItem[]>("/api/v1/reports").catch(() => []),
        apiRequest<ScheduledReportItem[]>("/api/v1/reports/schedules").catch(() => []),
        apiRequest<Dataset[]>("/api/v1/datasets").catch(() => []),
        apiRequest<GmailStatus>("/api/v1/integrations/gmail/status").catch(() => ({
          is_connected: false,
          provider: "google",
        })),
      ]);
      setReports(reps);
      setSchedules(scheds);
      setDatasets(dsets);
      setGmailStatus(gStatus);
      if (dsets.length > 0 && !newScheduleDataset) {
        setNewScheduleDataset(dsets[0].id);
      }
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  }, [newScheduleDataset]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDownload = (report: ReportItem) => {
    const ext = report.report_format === "pdf" ? "pdf" : report.report_format === "excel" ? "xlsx" : "csv";
    const token = typeof window !== "undefined" ? localStorage.getItem("inslight_token") : "";
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/reports/${report.id}/download`;

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `${report.name.replace(/\s+/g, "_")}.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      });
  };

  const handleDeleteReport = async (reportId: string) => {
    if (!confirm("Are you sure you want to delete this report?")) return;
    try {
      await apiRequest(`/api/v1/reports/${reportId}`, { method: "DELETE" });
      setReports((prev) => prev.filter((r) => r.id !== reportId));
    } catch (err: any) {
      alert(err?.message || "Failed to delete report.");
    }
  };

  const handleConnectGmail = async () => {
    try {
      const res = await apiRequest<{ authorization_url: string }>("/api/v1/integrations/gmail/authorize");
      if (res.authorization_url) {
        window.location.href = res.authorization_url;
      }
    } catch (err: any) {
      alert(err?.message || "Failed to initiate Gmail authorization.");
    }
  };

  const handleDisconnectGmail = async () => {
    if (!confirm("Disconnect Gmail? You won't be able to email reports until re-connected.")) return;
    try {
      await apiRequest("/api/v1/integrations/gmail/disconnect", { method: "POST" });
      setGmailStatus({ is_connected: false, provider: "google" });
    } catch (err: any) {
      alert(err?.message || "Failed to disconnect Gmail.");
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setScheduleError(null);
    const recs = newScheduleRecipients
      .split(",")
      .map((r) => r.trim())
      .filter((r) => r.length > 0);

    if (recs.length === 0) {
      setScheduleError("At least one recipient email address is required.");
      return;
    }

    try {
      const created = await apiRequest<ScheduledReportItem>("/api/v1/reports/schedules", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: newScheduleDataset,
          report_name: newScheduleName,
          frequency: newScheduleFreq,
          report_format: newScheduleFormat,
          recipients: recs,
          email_subject: newScheduleSubject,
          email_body: newScheduleBody,
          is_active: true,
        }),
      });
      setSchedules((prev) => [created, ...prev]);
      setShowScheduleModal(false);
      // Reset form
      setNewScheduleName("");
      setNewScheduleRecipients("");
      setNewScheduleSubject("");
      setNewScheduleBody("");
    } catch (err: any) {
      setScheduleError(err?.message || "Failed to create schedule.");
    }
  };

  const handleToggleSchedule = async (schedule: ScheduledReportItem) => {
    try {
      const updated = await apiRequest<ScheduledReportItem>(`/api/v1/reports/schedules/${schedule.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !schedule.is_active }),
      });
      setSchedules((prev) => prev.map((s) => (s.id === schedule.id ? updated : s)));
    } catch (err: any) {
      alert(err?.message || "Failed to update schedule status.");
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!confirm("Are you sure you want to delete this schedule?")) return;
    try {
      await apiRequest(`/api/v1/reports/schedules/${scheduleId}`, { method: "DELETE" });
      setSchedules((prev) => prev.filter((s) => s.id !== scheduleId));
    } catch (err: any) {
      alert(err?.message || "Failed to delete schedule.");
    }
  };

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "20px", color: "#f8fafc" }}>
      {/* Top Header & Gmail Integration Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "20px",
          paddingBottom: "16px",
          borderBottom: "1px solid var(--border-color, #334155)",
        }}
      >
        <div>
          <h2 style={{ margin: "0 0 4px 0", fontSize: "22px", fontWeight: 700 }}>
            📊 Business Reports & Automation
          </h2>
          <p style={{ margin: 0, fontSize: "12px", color: "#94a3b8" }}>
            Generate PDF & Excel reports, email via Gmail, and manage automated reporting schedules.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Gmail Status Pill */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "12px",
              padding: "6px 12px",
              borderRadius: "20px",
              background: gmailStatus?.is_connected ? "rgba(16, 185, 129, 0.15)" : "rgba(100, 116, 139, 0.15)",
              border: `1px solid ${gmailStatus?.is_connected ? "#059669" : "#475569"}`,
              color: gmailStatus?.is_connected ? "#6ee7b7" : "#94a3b8",
            }}
          >
            <span>{gmailStatus?.is_connected ? "🟢 Gmail Connected" : "⚪ Gmail Disconnected"}</span>
            {gmailStatus?.is_connected ? (
              <button
                onClick={handleDisconnectGmail}
                title="Disconnect Gmail"
                style={{ background: "none", border: "none", color: "#fca5a5", cursor: "pointer", fontSize: "11px", padding: 0, textDecoration: "underline" }}
              >
                (Disconnect)
              </button>
            ) : (
              <button
                onClick={handleConnectGmail}
                style={{
                  background: "#2563eb",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "12px",
                  padding: "2px 8px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Connect
              </button>
            )}
          </div>

          {/* Generate Report Button */}
          <button
            onClick={() => setShowGenerateModal(true)}
            style={{
              background: "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>+</span> Generate Report
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
        <button
          onClick={() => setActiveTab("history")}
          style={{
            padding: "8px 16px",
            background: activeTab === "history" ? "#1e293b" : "transparent",
            border: `1px solid ${activeTab === "history" ? "#3b82f6" : "#334155"}`,
            borderRadius: "6px",
            color: activeTab === "history" ? "#38bdf8" : "#94a3b8",
            fontSize: "13px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          📁 Report History ({reports.length})
        </button>
        <button
          onClick={() => setActiveTab("schedules")}
          style={{
            padding: "8px 16px",
            background: activeTab === "schedules" ? "#1e293b" : "transparent",
            border: `1px solid ${activeTab === "schedules" ? "#3b82f6" : "#334155"}`,
            borderRadius: "6px",
            color: activeTab === "schedules" ? "#38bdf8" : "#94a3b8",
            fontSize: "13px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          ⏰ Scheduled Reports ({schedules.length})
        </button>
      </div>

      {/* TAB 1: REPORT HISTORY */}
      {activeTab === "history" && (
        <div>
          {loading ? (
            <div style={{ padding: "30px", textAlign: "center", color: "#94a3b8" }}>Loading report history...</div>
          ) : reports.length === 0 ? (
            <div style={{ padding: "40px", textAlign: "center", background: "#1e293b", borderRadius: "10px", border: "1px solid #334155" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>📑</div>
              <h4 style={{ margin: "0 0 6px 0", color: "#f8fafc" }}>No reports generated yet</h4>
              <p style={{ margin: 0, fontSize: "12px", color: "#94a3b8" }}>
                Generate your first executive PDF or Excel report using the button above.
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto", background: "#1e293b", borderRadius: "10px", border: "1px solid #334155" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                <thead>
                  <tr style={{ background: "#0f172a", borderBottom: "1px solid #334155", textAlign: "left", color: "#94a3b8" }}>
                    <th style={{ padding: "10px 14px" }}>Report Title</th>
                    <th style={{ padding: "10px 14px" }}>Format</th>
                    <th style={{ padding: "10px 14px" }}>File Size</th>
                    <th style={{ padding: "10px 14px" }}>Generated Date</th>
                    <th style={{ padding: "10px 14px" }}>Delivery Status</th>
                    <th style={{ padding: "10px 14px", textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.id} style={{ borderBottom: "1px solid #334155" }}>
                      <td style={{ padding: "12px 14px", fontWeight: 600, color: "#f8fafc" }}>{r.name}</td>
                      <td style={{ padding: "12px 14px" }}>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "4px",
                            fontSize: "10px",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            background: r.report_format === "pdf" ? "#7f1d1d" : r.report_format === "excel" ? "#064e3b" : "#1e3a8a",
                            color: r.report_format === "pdf" ? "#fca5a5" : r.report_format === "excel" ? "#6ee7b7" : "#93c5fd",
                          }}
                        >
                          {r.report_format}
                        </span>
                      </td>
                      <td style={{ padding: "12px 14px", color: "#94a3b8" }}>{Math.round(r.file_size / 1024)} KB</td>
                      <td style={{ padding: "12px 14px", color: "#cbd5e1" }}>
                        {new Date(r.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        {r.status === "sent" ? (
                          <span style={{ color: "#10b981", fontSize: "11px" }}>✓ Sent via Gmail</span>
                        ) : r.status === "failed" ? (
                          <span style={{ color: "#ef4444", fontSize: "11px" }}>⚠️ Delivery Failed</span>
                        ) : (
                          <span style={{ color: "#94a3b8", fontSize: "11px" }}>Generated</span>
                        )}
                      </td>
                      <td style={{ padding: "12px 14px", textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "6px" }}>
                          <button
                            onClick={() => handleDownload(r)}
                            title="Download Report"
                            style={{ background: "#2563eb", color: "#ffffff", border: "none", borderRadius: "4px", padding: "4px 8px", cursor: "pointer", fontSize: "11px" }}
                          >
                            ⬇️
                          </button>
                          <button
                            onClick={() => setEmailingReport(r)}
                            title="Email via Gmail"
                            style={{ background: "#10b981", color: "#ffffff", border: "none", borderRadius: "4px", padding: "4px 8px", cursor: "pointer", fontSize: "11px" }}
                          >
                            📧
                          </button>
                          <button
                            onClick={() => handleDeleteReport(r.id)}
                            title="Delete Report"
                            style={{ background: "#dc2626", color: "#ffffff", border: "none", borderRadius: "4px", padding: "4px 8px", cursor: "pointer", fontSize: "11px" }}
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: SCHEDULED REPORTS */}
      {activeTab === "schedules" && (
        <div>
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "12px" }}>
            <button
              onClick={() => setShowScheduleModal(true)}
              style={{
                background: "#10b981",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                padding: "6px 14px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              + Create Scheduled Report
            </button>
          </div>

          {schedules.length === 0 ? (
            <div style={{ padding: "40px", textAlign: "center", background: "#1e293b", borderRadius: "10px", border: "1px solid #334155" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>⏰</div>
              <h4 style={{ margin: "0 0 6px 0", color: "#f8fafc" }}>No automated schedules configured</h4>
              <p style={{ margin: 0, fontSize: "12px", color: "#94a3b8" }}>
                Set up automated weekly or monthly reports that deliver directly to stakeholder inboxes.
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto", background: "#1e293b", borderRadius: "10px", border: "1px solid #334155" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                <thead>
                  <tr style={{ background: "#0f172a", borderBottom: "1px solid #334155", textAlign: "left", color: "#94a3b8" }}>
                    <th style={{ padding: "10px 14px" }}>Schedule Name</th>
                    <th style={{ padding: "10px 14px" }}>Frequency</th>
                    <th style={{ padding: "10px 14px" }}>Format</th>
                    <th style={{ padding: "10px 14px" }}>Recipients</th>
                    <th style={{ padding: "10px 14px" }}>Next Run</th>
                    <th style={{ padding: "10px 14px" }}>Status</th>
                    <th style={{ padding: "10px 14px", textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((s) => (
                    <tr key={s.id} style={{ borderBottom: "1px solid #334155" }}>
                      <td style={{ padding: "12px 14px", fontWeight: 600, color: "#f8fafc" }}>{s.report_name}</td>
                      <td style={{ padding: "12px 14px", textTransform: "capitalize", color: "#38bdf8" }}>{s.frequency}</td>
                      <td style={{ padding: "12px 14px", textTransform: "uppercase" }}>{s.report_format}</td>
                      <td style={{ padding: "12px 14px", color: "#cbd5e1" }}>{s.recipients}</td>
                      <td style={{ padding: "12px 14px", color: "#94a3b8" }}>
                        {new Date(s.next_run_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        <button
                          onClick={() => handleToggleSchedule(s)}
                          style={{
                            background: s.is_active ? "#064e3b" : "#451a03",
                            color: s.is_active ? "#6ee7b7" : "#fcd34d",
                            border: `1px solid ${s.is_active ? "#059669" : "#d97706"}`,
                            borderRadius: "12px",
                            padding: "2px 8px",
                            fontSize: "11px",
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          {s.is_active ? "Active" : "Paused"}
                        </button>
                      </td>
                      <td style={{ padding: "12px 14px", textAlign: "right" }}>
                        <button
                          onClick={() => handleDeleteSchedule(s.id)}
                          style={{ background: "#dc2626", color: "#ffffff", border: "none", borderRadius: "4px", padding: "4px 8px", cursor: "pointer", fontSize: "11px" }}
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* CREATE SCHEDULE MODAL */}
      {showScheduleModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, backdropFilter: "blur(4px)" }}>
          <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "12px", width: "90%", maxWidth: "500px", padding: "24px", color: "#f8fafc" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>⏰ Create Report Schedule</h3>
              <button onClick={() => setShowScheduleModal(false)} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "18px" }}>✕</button>
            </div>

            {scheduleError && (
              <div style={{ background: "#7f1d1d", color: "#fca5a5", padding: "8px 12px", borderRadius: "6px", fontSize: "12px", marginBottom: "12px" }}>
                {scheduleError}
              </div>
            )}

            <form onSubmit={handleCreateSchedule}>
              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Schedule Name *</label>
                <input
                  type="text"
                  required
                  value={newScheduleName}
                  onChange={(e) => setNewScheduleName(e.target.value)}
                  placeholder="e.g. Weekly Executive KPI Digest"
                  style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
                />
              </div>

              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Target Dataset *</label>
                <select
                  value={newScheduleDataset}
                  onChange={(e) => setNewScheduleDataset(e.target.value)}
                  required
                  style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>{d.original_filename} ({d.row_count} rows)</option>
                  ))}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Frequency *</label>
                  <select
                    value={newScheduleFreq}
                    onChange={(e) => setNewScheduleFreq(e.target.value as any)}
                    style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
                  >
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Format *</label>
                  <select
                    value={newScheduleFormat}
                    onChange={(e) => setNewScheduleFormat(e.target.value as any)}
                    style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
                  >
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                    <option value="both">Both</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Recipients (comma-separated) *</label>
                <input
                  type="text"
                  required
                  value={newScheduleRecipients}
                  onChange={(e) => setNewScheduleRecipients(e.target.value)}
                  placeholder="stakeholder@company.com"
                  style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
                />
              </div>

              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Email Subject *</label>
                <input
                  type="text"
                  required
                  value={newScheduleSubject}
                  onChange={(e) => setNewScheduleSubject(e.target.value)}
                  placeholder="Automated BI Performance Digest"
                  style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>Email Body *</label>
                <textarea
                  rows={3}
                  required
                  value={newScheduleBody}
                  onChange={(e) => setNewScheduleBody(e.target.value)}
                  placeholder="Attached is your scheduled business report from INSLIGHT."
                  style={{ width: "100%", padding: "6px 10px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px", fontFamily: "inherit" }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  style={{ background: "transparent", border: "1px solid #334155", color: "#94a3b8", borderRadius: "6px", padding: "6px 12px", fontSize: "12px", cursor: "pointer" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ background: "#10b981", border: "none", color: "#ffffff", borderRadius: "6px", padding: "6px 16px", fontSize: "12px", fontWeight: 600, cursor: "pointer" }}
                >
                  Save Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* GENERATE REPORT MODAL */}
      <ReportModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onReportGenerated={(newRep) => setReports((prev) => [newRep, ...prev])}
      />

      {/* EMAIL COMPOSER MODAL */}
      <EmailComposerModal
        isOpen={Boolean(emailingReport)}
        onClose={() => setEmailingReport(null)}
        report={emailingReport}
        onSent={loadData}
      />
    </div>
  );
};
