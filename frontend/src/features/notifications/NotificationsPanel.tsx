"use client";
import React, { useState } from "react";
import { NotificationItem } from "../../types";

interface NotificationsPanelProps {
  notifications: NotificationItem[];
  loading: boolean;
  onRefresh: () => void;
  onMarkRead: (id: string) => void;
  onMarkAllRead: () => void;
  onDelete: (id: string) => void;
}

const CATEGORIES = ["all", "alert", "report", "schedule", "email", "system"];

export const NotificationsPanel: React.FC<NotificationsPanelProps> = ({
  notifications,
  loading,
  onRefresh,
  onMarkRead,
  onMarkAllRead,
  onDelete,
}) => {
  const [filterCat, setFilterCat] = useState("all");
  const filtered = filterCat === "all"
    ? notifications
    : notifications.filter((n) => n.category === filterCat);
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: "#f3f4f6", margin: 0 }}>
            🔔 Notification Center
          </h3>
          <p style={{ fontSize: 12.5, color: "#9ca3af", margin: "4px 0 0 0" }}>
            {unreadCount} unread notification{unreadCount === 1 ? "" : "s"} across alerts, reports, and schedules.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onRefresh}
            disabled={loading}
            style={{ fontSize: 12 }}
          >
            ↻ Refresh
          </button>
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={onMarkAllRead}
              style={{
                background: "#2563eb",
                color: "#fff",
                border: "none",
                borderRadius: 6,
                padding: "6px 12px",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              ✓ Mark All Read
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setFilterCat(cat)}
            className={`chat-action-btn ${filterCat === cat ? "active" : ""}`}
            style={{ fontSize: 11, padding: "4px 10px", textTransform: "capitalize" }}
          >
            {cat}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={{ textAlign: "center", padding: "48px 20px", background: "rgba(15,23,42,0.5)", borderRadius: 10, border: "1px solid #1f2937" }}>
          <div style={{ fontSize: 34, marginBottom: 8 }}>📭</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#e5e7eb" }}>No notifications</div>
          <div style={{ fontSize: 12.5, color: "#9ca3af", marginTop: 4 }}>
            Notifications from business alerts, reports, and scheduled jobs will appear here.
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {filtered.map((n) => (
            <div
              key={n.id}
              style={{
                background: n.is_read ? "rgba(15, 23, 42, 0.45)" : "rgba(37, 99, 235, 0.08)",
                border: n.is_read ? "1px solid #1f2937" : "1px solid rgba(59, 130, 246, 0.35)",
                borderRadius: 10,
                padding: "12px 14px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: 12,
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", padding: "2px 6px", borderRadius: 4, background: "rgba(255,255,255,0.08)", color: "#93c5fd" }}>
                    {n.category}
                  </span>
                  {!n.is_read && (
                    <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#3b82f6", display: "inline-block" }} />
                  )}
                  <span style={{ fontSize: 11, color: "#6b7280" }}>
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{ fontSize: 13.5, fontWeight: 700, color: "#f3f4f6" }}>{n.title}</div>
                <div style={{ fontSize: 12.5, color: "#9ca3af", marginTop: 3, lineHeight: 1.5 }}>{n.message}</div>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                {!n.is_read && (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ fontSize: 11, padding: "4px 8px" }}
                    onClick={() => onMarkRead(n.id)}
                  >
                    Read
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-ghost"
                  style={{ fontSize: 11, padding: "4px 8px", color: "#f87171" }}
                  onClick={() => onDelete(n.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
