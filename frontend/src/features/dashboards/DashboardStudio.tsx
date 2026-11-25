import React, { useState } from "react";
import { SavedDashboardItem } from "../../types";

interface DashboardStudioProps {
  currentDashboard: any | null;
  savedDashboards: SavedDashboardItem[];
  loading: boolean;
  onGenerateFromPrompt: (prompt: string) => void;
  onSaveDashboard: (title: string, desc: string, layout: any) => void;
  onOpenDashboard: (dash: SavedDashboardItem) => void;
  onDeleteDashboard: (id: string) => void;
}

export const DashboardStudio: React.FC<DashboardStudioProps> = ({
  currentDashboard,
  savedDashboards,
  loading,
  onGenerateFromPrompt,
  onSaveDashboard,
  onOpenDashboard,
  onDeleteDashboard
}) => {
  const [prompt, setPrompt] = useState("Create a sales dashboard showing monthly revenue, top products, regional performance and profit margin.");
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [dashTitle, setDashTitle] = useState("");
  const [dashDesc, setDashDesc] = useState("");

  const handleSave = () => {
    if (!dashTitle.trim() || !currentDashboard) return;
    onSaveDashboard(dashTitle, dashDesc, currentDashboard);
    setShowSaveModal(false);
    setDashTitle("");
    setDashDesc("");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* AI Dashboard Creator Input */}
      <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: "18px 20px" }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#38BDF8", marginBottom: 6, textTransform: "uppercase" }}>
          ✨ AI Dashboard Studio
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your desired dashboard layout..."
            style={{ flex: 1, background: "#1F2937", border: "1px solid #374151", color: "#FFF", borderRadius: 8, padding: "10px 14px", fontSize: 13 }}
          />
          <button
            type="button"
            onClick={() => onGenerateFromPrompt(prompt)}
            disabled={loading || !prompt.trim()}
            className="chat-action-btn active"
            style={{ padding: "8px 20px" }}
          >
            {loading ? "Generating..." : "⚡ Build Dashboard"}
          </button>
        </div>
      </div>

      {/* Saved Dashboards Carousel / Bar */}
      {savedDashboards.length > 0 && (
        <div style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 12, padding: "14px 18px" }}>
          <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 700, marginBottom: 8, textTransform: "uppercase" }}>
            Saved Dashboards ({savedDashboards.length})
          </div>
          <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 4 }}>
            {savedDashboards.map((dash) => (
              <div
                key={dash.id}
                style={{
                  background: "#1F2937",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  padding: "8px 12px",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  minWidth: 180
                }}
              >
                <div style={{ flex: 1, cursor: "pointer" }} onClick={() => onOpenDashboard(dash)}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#F8FAFC" }}>{dash.title}</div>
                  <div style={{ fontSize: 10, color: "#94A3B8" }}>{new Date(dash.created_at).toLocaleDateString()}</div>
                </div>
                <button
                  type="button"
                  onClick={() => onDeleteDashboard(dash.id)}
                  style={{ background: "none", border: "none", color: "#EF4444", cursor: "pointer", fontSize: 14 }}
                  title="Delete Dashboard"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Render Active Dashboard Layout */}
      {currentDashboard && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: 18, color: "#F8FAFC", margin: 0 }}>{currentDashboard.title}</h2>
              <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>{currentDashboard.description}</div>
            </div>
            <button
              type="button"
              onClick={() => {
                setDashTitle(currentDashboard.title);
                setShowSaveModal(true);
              }}
              className="chat-action-btn"
              style={{ padding: "6px 14px", fontSize: 12 }}
            >
              💾 Save to Library
            </button>
          </div>

          {/* Grid of Widgets */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            {currentDashboard.widgets?.map((w: any, idx: number) => {
              if (w.type === "kpi") {
                return (
                  <div key={idx} style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 18 }}>
                    <div style={{ fontSize: 11, color: "#94A3B8", textTransform: "uppercase", fontWeight: 700 }}>{w.title}</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: "#38BDF8", marginTop: 4 }}>{w.formatted_value}</div>
                    <div style={{ fontSize: 12, color: "#64748B", marginTop: 2 }}>{w.description}</div>
                  </div>
                );
              }

              return (
                <div key={idx} style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 10, padding: 18, gridColumn: "span 1" }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#F8FAFC", marginBottom: 12 }}>{w.title}</div>
                  <div style={{ maxHeight: 180, overflowY: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
                      <thead>
                        <tr style={{ color: "#94A3B8", borderBottom: "1px solid #374151" }}>
                          <th style={{ padding: "6px 8px" }}>{w.x_axis}</th>
                          <th style={{ padding: "6px 8px" }}>{w.y_axis}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {w.data?.slice(0, 5).map((r: any, rIdx: number) => (
                          <tr key={rIdx} style={{ borderBottom: "1px solid #1F2937" }}>
                            <td style={{ padding: "6px 8px", color: "#E2E8F0" }}>{r[w.x_axis] || r.label || r.period}</td>
                            <td style={{ padding: "6px 8px", color: "#38BDF8", fontWeight: 600 }}>
                              ₹{Number(r[w.y_axis] || r.value || r.metric_val || 0).toLocaleString("en-IN")}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Save Modal */}
      {showSaveModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <div style={{ background: "#111827", border: "1px solid #374151", borderRadius: 12, padding: 24, width: 440, maxWidth: "90%" }}>
            <h3 style={{ margin: "0 0 16px 0", color: "#F8FAFC", fontSize: 16 }}>Save Dashboard to Library</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, color: "#94A3B8", display: "block", marginBottom: 4 }}>Dashboard Title</label>
                <input
                  type="text"
                  value={dashTitle}
                  onChange={(e) => setDashTitle(e.target.value)}
                  style={{ width: "100%", background: "#1F2937", border: "1px solid #374151", color: "#FFF", padding: "8px 12px", borderRadius: 6, fontSize: 13 }}
                />
              </div>
              <div>
                <label style={{ fontSize: 12, color: "#94A3B8", display: "block", marginBottom: 4 }}>Description</label>
                <textarea
                  value={dashDesc}
                  onChange={(e) => setDashDesc(e.target.value)}
                  rows={3}
                  style={{ width: "100%", background: "#1F2937", border: "1px solid #374151", color: "#FFF", padding: "8px 12px", borderRadius: 6, fontSize: 13 }}
                />
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setShowSaveModal(false)}
                style={{ background: "#1F2937", border: "none", color: "#94A3B8", padding: "8px 16px", borderRadius: 6, cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                className="chat-action-btn active"
                style={{ padding: "8px 18px" }}
              >
                Save Dashboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
