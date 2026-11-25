"use client";
import React, { useState } from "react";
import { AuditLogItem, User } from "../../types";
import { apiRequest } from "../../services/api-client";

interface AdminPanelProps {
  currentUser: User | null;
  users: User[];
  auditLogs: AuditLogItem[];
  systemStatus: any;
  onRefresh: () => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({
  currentUser,
  users,
  auditLogs,
  systemStatus,
  onRefresh,
}) => {
  const [tab, setTab] = useState<"users" | "audit" | "health">("users");
  const [error, setError] = useState<string | null>(null);

  if (currentUser?.role !== "admin") {
    return (
      <div style={{ padding: 32, textAlign: "center", color: "#f87171" }}>
        🔒 Administrator privileges required to access this view.
      </div>
    );
  }

  const handleRoleChange = async (userId: string, role: string) => {
    setError(null);
    try {
      await apiRequest(`/api/v1/admin/users/${userId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      onRefresh();
    } catch (e: any) {
      setError(e.message || "Failed to update role.");
    }
  };

  const handleStatusToggle = async (userId: string, is_active: boolean) => {
    setError(null);
    try {
      await apiRequest(`/api/v1/admin/users/${userId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ is_active }),
      });
      onRefresh();
    } catch (e: any) {
      setError(e.message || "Failed to update account status.");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: "#f3f4f6", margin: 0 }}>
            🛡️ Administration, RBAC & Audit Logs
          </h3>
          <p style={{ fontSize: 12.5, color: "#9ca3af", margin: "4px 0 0 0" }}>
            Manage user roles, review security audit logs, and inspect system readiness.
          </p>
        </div>
        <button type="button" className="btn btn-ghost" onClick={onRefresh} style={{ fontSize: 12 }}>
          ↻ Refresh
        </button>
      </div>

      {error && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: 8, padding: "10px 14px", color: "#fca5a5", fontSize: 12.5 }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button type="button" className={`chat-action-btn ${tab === "users" ? "active" : ""}`} onClick={() => setTab("users")}>
          👥 Users & Roles ({users.length})
        </button>
        <button type="button" className={`chat-action-btn ${tab === "audit" ? "active" : ""}`} onClick={() => setTab("audit")}>
          📜 Audit Logs ({auditLogs.length})
        </button>
        <button type="button" className={`chat-action-btn ${tab === "health" ? "active" : ""}`} onClick={() => setTab("health")}>
          🩺 System Status
        </button>
      </div>

      {tab === "users" && (
        <div style={{ overflowX: "auto", background: "rgba(15, 23, 42, 0.6)", borderRadius: 10, border: "1px solid #1f2937" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #1f2937", color: "#9ca3af", textAlign: "left" }}>
                <th style={{ padding: "10px 12px" }}>Name</th>
                <th style={{ padding: "10px 12px" }}>Email</th>
                <th style={{ padding: "10px 12px" }}>Role</th>
                <th style={{ padding: "10px 12px" }}>Status</th>
                <th style={{ padding: "10px 12px" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", color: "#e5e7eb" }}>
                  <td style={{ padding: "10px 12px", fontWeight: 600 }}>{u.name}</td>
                  <td style={{ padding: "10px 12px", color: "#9ca3af" }}>{u.email}</td>
                  <td style={{ padding: "10px 12px" }}>
                    <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700, background: u.role === "admin" ? "rgba(99, 102, 241, 0.2)" : "rgba(16, 185, 129, 0.15)", color: u.role === "admin" ? "#a5b4fc" : "#6ee7b7" }}>
                      {u.role || "analyst"}
                    </span>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    {u.is_active ? "Active" : "Inactive"}
                  </td>
                  <td style={{ padding: "10px 12px", display: "flex", gap: 6 }}>
                    <select
                      value={u.role || "analyst"}
                      disabled={u.id === currentUser.id}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      style={{ background: "#0b1120", color: "#f3f4f6", border: "1px solid #334155", borderRadius: 4, padding: "3px 6px", fontSize: 11.5 }}
                    >
                      <option value="analyst">analyst</option>
                      <option value="admin">admin</option>
                    </select>
                    <button
                      type="button"
                      disabled={u.id === currentUser.id}
                      onClick={() => handleStatusToggle(u.id, !u.is_active)}
                      className="btn btn-ghost"
                      style={{ fontSize: 11, padding: "3px 8px" }}
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "audit" && (
        <div style={{ overflowX: "auto", background: "rgba(15, 23, 42, 0.6)", borderRadius: 10, border: "1px solid #1f2937" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #1f2937", color: "#9ca3af", textAlign: "left" }}>
                <th style={{ padding: "9px 12px" }}>Timestamp</th>
                <th style={{ padding: "9px 12px" }}>Action</th>
                <th style={{ padding: "9px 12px" }}>Resource</th>
                <th style={{ padding: "9px 12px" }}>Status</th>
                <th style={{ padding: "9px 12px" }}>Request ID</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", color: "#d1d5db" }}>
                  <td style={{ padding: "8px 12px", whiteSpace: "nowrap" }}>{new Date(log.created_at).toLocaleString()}</td>
                  <td style={{ padding: "8px 12px", fontWeight: 600 }}>{log.action}</td>
                  <td style={{ padding: "8px 12px" }}>{log.resource_type}</td>
                  <td style={{ padding: "8px 12px", color: log.status === "success" ? "#34d399" : "#f87171" }}>{log.status}</td>
                  <td style={{ padding: "8px 12px", fontFamily: "monospace", color: "#9ca3af" }}>{log.request_id || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "health" && systemStatus && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 12 }}>
          <div style={{ background: "rgba(15,23,42,0.65)", border: "1px solid #1f2937", borderRadius: 10, padding: 14 }}>
            <div style={{ fontSize: 11, color: "#9ca3af" }}>DATABASE DIALECT</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#10b981", marginTop: 4 }}>{systemStatus.database_dialect}</div>
          </div>
          {Object.entries(systemStatus.counts || {}).map(([k, v]) => (
            <div key={k} style={{ background: "rgba(15,23,42,0.65)", border: "1px solid #1f2937", borderRadius: 10, padding: 14 }}>
              <div style={{ fontSize: 11, color: "#9ca3af", textTransform: "uppercase" }}>{k.replace("_", " ")}</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#f3f4f6", marginTop: 4 }}>{String(v)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
