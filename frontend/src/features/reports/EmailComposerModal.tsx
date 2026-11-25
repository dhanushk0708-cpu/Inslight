"use client";
import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api-client";
import { ReportItem, GmailStatus } from "../../types";

interface EmailComposerModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: ReportItem | null;
  onSent?: () => void;
}

export const EmailComposerModal: React.FC<EmailComposerModalProps> = ({
  isOpen,
  onClose,
  report,
  onSent,
}) => {
  const [recipients, setRecipients] = useState("");
  const [ccRecipients, setCcRecipients] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Check Gmail connection status
      apiRequest<GmailStatus>("/api/v1/integrations/gmail/status")
        .then((s) => setGmailStatus(s))
        .catch(() => setGmailStatus({ is_connected: false, provider: "google" }));

      if (report) {
        setSubject(`INSLIGHT Report: ${report.name}`);
        setBody(
          `Hello,\n\nPlease find attached the latest business intelligence report generated from INSLIGHT: "${report.name}".\n\nFormat: ${report.report_format.toUpperCase()}\nGenerated: ${new Date(report.created_at).toLocaleDateString()}\n\nBest regards,\nINSLIGHT Analytics Platform`
        );
      }
    }
  }, [isOpen, report]);

  if (!isOpen || !report) return null;

  const handleConnectGmail = async () => {
    try {
      const res = await apiRequest<{ authorization_url: string }>("/api/v1/integrations/gmail/authorize");
      if (res.authorization_url) {
        window.location.href = res.authorization_url;
      }
    } catch (err: any) {
      setError(err?.message || "Failed to initiate Gmail authorization.");
    }
  };

  const handleSend = async () => {
    const recipientList = recipients
      .split(",")
      .map((r) => r.trim())
      .filter((r) => r.length > 0);

    const ccList = ccRecipients
      .split(",")
      .map((r) => r.trim())
      .filter((r) => r.length > 0);

    if (recipientList.length === 0) {
      setError("Please specify at least one recipient email address.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiRequest("/api/v1/reports/email", {
        method: "POST",
        body: JSON.stringify({
          report_id: report.id,
          recipients: recipientList,
          cc_recipients: ccList.length > 0 ? ccList : undefined,
          subject,
          body,
        }),
      });

      setSuccess("Report successfully delivered via Gmail API!");
      setIsConfirming(false);
      if (onSent) onSent();
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err?.message || "Failed to email report via Gmail.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.75)",
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
          maxWidth: "520px",
          padding: "24px",
          color: "#f8fafc",
          boxShadow: "0 25px 50px rgba(0,0,0,0.6)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0, fontSize: "17px", fontWeight: 600 }}>📧 Email Business Report</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "18px" }}>
            ✕
          </button>
        </div>

        {/* Gmail Connection Status Banner */}
        {gmailStatus && (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              marginBottom: "16px",
              fontSize: "12px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: gmailStatus.is_connected ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
              border: `1px solid ${gmailStatus.is_connected ? "#059669" : "#dc2626"}`,
              color: gmailStatus.is_connected ? "#6ee7b7" : "#fca5a5",
            }}
          >
            <div>
              {gmailStatus.is_connected ? (
                <span>✓ Connected to Gmail as <b>{gmailStatus.email}</b></span>
              ) : (
                <span>⚠️ Gmail not connected. You must authorize Google to send reports.</span>
              )}
            </div>
            {!gmailStatus.is_connected && (
              <button
                type="button"
                onClick={handleConnectGmail}
                style={{
                  background: "#dc2626",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "4px",
                  padding: "4px 8px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Connect Gmail
              </button>
            )}
          </div>
        )}

        {error && (
          <div style={{ background: "#7f1d1d", border: "1px solid #991b1b", color: "#fca5a5", padding: "8px 12px", borderRadius: "6px", fontSize: "12px", marginBottom: "14px" }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{ background: "#064e3b", border: "1px solid #059669", color: "#6ee7b7", padding: "8px 12px", borderRadius: "6px", fontSize: "12px", marginBottom: "14px" }}>
            {success}
          </div>
        )}

        {/* Attachment Card */}
        <div
          style={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "6px",
            padding: "8px 12px",
            marginBottom: "14px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "12px",
          }}
        >
          <div>
            <span style={{ fontWeight: 600, color: "#38bdf8" }}>📎 Attachment: </span>
            <span>{report.name}.{report.report_format === "excel" ? "xlsx" : report.report_format}</span>
          </div>
          <span style={{ color: "#94a3b8" }}>{Math.round(report.file_size / 1024)} KB</span>
        </div>

        {!isConfirming ? (
          <div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                Recipients (comma-separated emails) *
              </label>
              <input
                type="text"
                value={recipients}
                onChange={(e) => setRecipients(e.target.value)}
                placeholder="cfo@company.com, manager@company.com"
                style={{ width: "100%", padding: "8px 12px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
              />
            </div>

            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                CC (optional)
              </label>
              <input
                type="text"
                value={ccRecipients}
                onChange={(e) => setCcRecipients(e.target.value)}
                placeholder="analyst@company.com"
                style={{ width: "100%", padding: "8px 12px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
              />
            </div>

            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                Subject *
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                style={{ width: "100%", padding: "8px 12px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px" }}
              />
            </div>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                Email Body *
              </label>
              <textarea
                rows={4}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                style={{ width: "100%", padding: "8px 12px", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#f8fafc", fontSize: "12px", fontFamily: "inherit" }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                type="button"
                onClick={onClose}
                style={{ background: "transparent", border: "1px solid #334155", color: "#94a3b8", borderRadius: "6px", padding: "8px 16px", fontSize: "12px", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => setIsConfirming(true)}
                disabled={!gmailStatus?.is_connected || !recipients.trim() || !subject.trim()}
                style={{
                  background: !gmailStatus?.is_connected ? "#475569" : "#2563eb",
                  border: "none",
                  color: "#ffffff",
                  borderRadius: "6px",
                  padding: "8px 18px",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: !gmailStatus?.is_connected ? "not-allowed" : "pointer",
                }}
              >
                Review & Confirm
              </button>
            </div>
          </div>
        ) : (
          /* Explicit Confirmation View */
          <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "8px", padding: "16px", fontSize: "12px" }}>
            <h4 style={{ margin: "0 0 10px 0", color: "#38bdf8", fontSize: "14px" }}>Confirm Outgoing Email Delivery</h4>
            <p style={{ margin: "4px 0" }}><b>To:</b> {recipients}</p>
            {ccRecipients && <p style={{ margin: "4px 0" }}><b>CC:</b> {ccRecipients}</p>}
            <p style={{ margin: "4px 0" }}><b>Subject:</b> {subject}</p>
            <p style={{ margin: "4px 0" }}><b>Attached:</b> {report.name} ({Math.round(report.file_size / 1024)} KB)</p>
            <p style={{ color: "#94a3b8", marginTop: "10px", fontSize: "11px", fontStyle: "italic" }}>
              This email will be dispatched directly through your connected Gmail account via the official Gmail API.
            </p>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
              <button
                type="button"
                onClick={() => setIsConfirming(false)}
                disabled={loading}
                style={{ background: "transparent", border: "1px solid #475569", color: "#cbd5e1", borderRadius: "6px", padding: "6px 14px", cursor: "pointer" }}
              >
                Back to Edit
              </button>
              <button
                type="button"
                onClick={handleSend}
                disabled={loading}
                style={{
                  background: "#10b981",
                  border: "none",
                  color: "#ffffff",
                  borderRadius: "6px",
                  padding: "6px 18px",
                  fontWeight: 600,
                  cursor: loading ? "wait" : "pointer",
                }}
              >
                {loading ? "Sending via Gmail..." : "🚀 Send Report Now"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
