import React, { useState } from "react";
import { BusinessAlert, AlertRuleItem } from "../../types";

interface AlertsPanelProps {
  alerts: BusinessAlert[];
  rules: AlertRuleItem[];
  loading: boolean;
  onScanAlerts: () => void;
  onMarkRead: (alertId: string) => void;
  onResolve: (alertId: string) => void;
  onCreateRule: (name: string, metric: string, cond: string, thresh: number) => void;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  alerts,
  rules,
  loading,
  onScanAlerts,
  onMarkRead,
  onResolve,
  onCreateRule
}) => {
  const [filter, setFilter] = useState<"all" | "unresolved" | "resolved">("unresolved");
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [newRuleName, setNewRuleName] = useState("");
  const [newRuleMetric, setNewRuleMetric] = useState("monthly_revenue_drop");
  const [newRuleCond, setNewRuleCond] = useState("greater_than");
  const [newRuleThresh, setNewRuleThresh] = useState(15.0);

  const filteredAlerts = alerts.filter((a) => {
    if (filter === "unresolved") return !a.is_resolved;
    if (filter === "resolved") return a.is_resolved;
    return true;
  });

  const handleSaveRule = () => {
    if (!newRuleName.trim()) return;
    onCreateRule(newRuleName, newRuleMetric, newRuleCond, newRuleThresh);
    setShowRuleModal(false);
    setNewRuleName("");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Top Controls */}
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
            onClick={() => setFilter("unresolved")}
            className={`chat-action-btn ${filter === "unresolved" ? "active" : ""}`}
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            Active Issues ({alerts.filter((a) => !a.is_resolved).length})
          </button>
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`chat-action-btn ${filter === "all" ? "active" : ""}`}
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            All Alerts ({alerts.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter("resolved")}
            className={`chat-action-btn ${filter === "resolved" ? "active" : ""}`}
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            Resolved ({alerts.filter((a) => a.is_resolved).length})
          </button>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            onClick={() => setShowRuleModal(true)}
            className="chat-action-btn"
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            ⚙️ Rules ({rules.length})
          </button>
          <button
            type="button"
            onClick={onScanAlerts}
            disabled={loading}
            className="chat-action-btn active"
            style={{ fontSize: 12, padding: "6px 16px" }}
          >
            {loading ? "Scanning..." : "🔍 Scan Dataset"}
          </button>
        </div>
      </div>

      {/* Alert Feed */}
      {filteredAlerts.length === 0 ? (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "#64748B" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🛡️</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#94A3B8", marginBottom: 6 }}>No Active Alerts</div>
          <p style={{ fontSize: 13, maxWidth: 440, margin: "0 auto" }}>
            All business guardrails and threshold conditions are currently operating within normal parameters.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filteredAlerts.map((alert) => {
            const isHigh = alert.severity === "high";
            const borderCol = isHigh ? "#EF4444" : alert.severity === "medium" ? "#F59E0B" : "#3B82F6";

            return (
              <div
                key={alert.id}
                style={{
                  background: alert.is_read ? "#111827" : "#1A2234",
                  border: `1px solid ${borderCol}40`,
                  borderLeft: `4px solid ${borderCol}`,
                  borderRadius: 10,
                  padding: 16,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: 16
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 800,
                        textTransform: "uppercase",
                        padding: "2px 6px",
                        borderRadius: 4,
                        background: `${borderCol}25`,
                        color: borderCol
                      }}
                    >
                      {alert.severity} SEVERITY
                    </span>
                    <span style={{ fontSize: 11, color: "#94A3B8" }}>
                      {alert.category.toUpperCase()} • {new Date(alert.created_at).toLocaleDateString()}
                    </span>
                    {alert.is_resolved && (
                      <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: "rgba(16, 185, 129, 0.2)", color: "#10B981", fontWeight: 700 }}>
                        RESOLVED
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#F8FAFC", marginBottom: 6 }}>
                    {alert.title}
                  </div>
                  <div style={{ fontSize: 13, color: "#CBD5E1", lineHeight: "20px" }}>
                    {alert.description}
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 90 }}>
                  {!alert.is_read && (
                    <button
                      type="button"
                      onClick={() => onMarkRead(alert.id)}
                      style={{ background: "#1F2937", border: "1px solid #374151", color: "#94A3B8", fontSize: 11, padding: "4px 8px", borderRadius: 4, cursor: "pointer" }}
                    >
                      Mark Read
                    </button>
                  )}
                  {!alert.is_resolved && (
                    <button
                      type="button"
                      onClick={() => onResolve(alert.id)}
                      style={{ background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#10B981", fontSize: 11, padding: "4px 8px", borderRadius: 4, cursor: "pointer", fontWeight: 600 }}
                    >
                      Resolve ✓
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal for Rule Configuration */}
      {showRuleModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <div style={{ background: "#111827", border: "1px solid #374151", borderRadius: 12, padding: 24, width: 440, maxWidth: "90%" }}>
            <h3 style={{ margin: "0 0 16px 0", color: "#F8FAFC", fontSize: 16 }}>Configure Business Alert Rule</h3>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, color: "#94A3B8", display: "block", marginBottom: 4 }}>Rule Name</label>
                <input
                  type="text"
                  placeholder="e.g. Sharp Revenue Contraction"
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  style={{ width: "100%", background: "#1F2937", border: "1px solid #374151", color: "#FFF", padding: "8px 12px", borderRadius: 6, fontSize: 13 }}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, color: "#94A3B8", display: "block", marginBottom: 4 }}>Monitored Metric</label>
                <select
                  value={newRuleMetric}
                  onChange={(e) => setNewRuleMetric(e.target.value)}
                  style={{ width: "100%", background: "#1F2937", border: "1px solid #374151", color: "#FFF", padding: "8px 12px", borderRadius: 6, fontSize: 13 }}
                >
                  <option value="monthly_revenue_drop">Monthly Revenue Drop (%)</option>
                  <option value="gross_margin_pct">Gross Profit Margin (%)</option>
                  <option value="regional_share_min">Minimum Territory Share (%)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, color: "#94A3B8", display: "block", marginBottom: 4 }}>Threshold Value</label>
                <input
                  type="number"
                  value={newRuleThresh}
                  onChange={(e) => setNewRuleThresh(Number(e.target.value))}
                  style={{ width: "100%", background: "#1F2937", border: "1px solid #374151", color: "#FFF", padding: "8px 12px", borderRadius: 6, fontSize: 13 }}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setShowRuleModal(false)}
                style={{ background: "#1F2937", border: "none", color: "#94A3B8", padding: "8px 16px", borderRadius: 6, cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveRule}
                className="chat-action-btn active"
                style={{ padding: "8px 18px" }}
              >
                Save Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
