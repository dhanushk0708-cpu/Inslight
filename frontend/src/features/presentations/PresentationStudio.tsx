"use client";
import React, { useState } from "react";
import { PresentationItem, PresentationOutline, SlideOutlineItem } from "../../types";
import { apiRequest } from "../../services/api-client";
import { AuthService } from "../../services/auth-service";

interface PresentationStudioProps {
  presentations: PresentationItem[];
  onRefresh: () => void;
  onNotifyUser: (msg: string) => void;
}

const PRESENTATION_TYPES = [
  "Executive Business Review",
  "Monthly Sales Report",
  "Revenue Performance",
  "Regional Performance",
  "Product Performance",
  "Business Opportunities and Risks",
  "Forecasting Report",
  "Custom Business Presentation",
];

export const PresentationStudio: React.FC<PresentationStudioProps> = ({
  presentations,
  onRefresh,
  onNotifyUser,
}) => {
  const [presType, setPresType] = useState(PRESENTATION_TYPES[0]);
  const [prompt, setPrompt] = useState("Analyze overall revenue performance, top segments, opportunities, and risks.");
  const [outline, setOutline] = useState<PresentationOutline | null>(null);
  const [editableSlides, setEditableSlides] = useState<SlideOutlineItem[]>([]);
  const [deckTitle, setDeckTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateOutline = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await apiRequest<PresentationOutline>("/api/v1/presentations/outline", {
        method: "POST",
        body: JSON.stringify({ prompt, presentation_type: presType }),
      });
      setOutline(res);
      setDeckTitle(res.title);
      setEditableSlides(res.slides);
    } catch (e: any) {
      setError(e.message || "Failed to generate slide outline.");
    } finally {
      setBusy(false);
    }
  };

  const handleSlideTitleChange = (idx: number, title: string) => {
    setEditableSlides((prev) => prev.map((s, i) => (i === idx ? { ...s, title } : s)));
  };

  const handleSlideBulletsChange = (idx: number, rawBullets: string) => {
    const bullets = rawBullets.split("\n").map((b) => b.trim()).filter(Boolean);
    setEditableSlides((prev) => prev.map((s, i) => (i === idx ? { ...s, bullets } : s)));
  };

  const handleRemoveSlide = (idx: number) => {
    setEditableSlides((prev) =>
      prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, slide_number: i + 1 }))
    );
  };

  const handleBuildPptx = async () => {
    if (!outline || editableSlides.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const created = await apiRequest<PresentationItem>("/api/v1/presentations/generate", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: outline.dataset_id,
          title: deckTitle || outline.title,
          presentation_type: outline.presentation_type,
          slides: editableSlides,
        }),
      });
      onNotifyUser(`📽️ PowerPoint deck "${created.title}" (${created.slide_count} slides) generated.`);
      setOutline(null);
      setEditableSlides([]);
      onRefresh();
    } catch (e: any) {
      setError(e.message || "Failed to generate PowerPoint file.");
    } finally {
      setBusy(false);
    }
  };

  const handleDownload = async (item: PresentationItem) => {
    const token = AuthService.getToken();
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const resp = await fetch(`${apiBase}/api/v1/presentations/${item.id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!resp.ok) {
      setError("Failed to download PowerPoint file.");
      return;
    }
    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${item.title.replace(/\s+/g, "_")}.pptx`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleDelete = async (id: string) => {
    await apiRequest(`/api/v1/presentations/${id}`, { method: "DELETE" });
    onRefresh();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: "#f3f4f6", margin: 0 }}>
          📽️ AI PowerPoint Presentation Studio
        </h3>
        <p style={{ fontSize: 12.5, color: "#9ca3af", margin: "4px 0 0 0" }}>
          Generate executive `.pptx` slide decks grounded in your active dataset, preview and edit the outline, and export.
        </p>
      </div>

      {error && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.35)", borderRadius: 8, padding: "10px 14px", color: "#fca5a5", fontSize: 12.5 }}>
          ⚠️ {error}
        </div>
      )}

      {/* Generator Controls */}
      <div style={{ background: "rgba(15, 23, 42, 0.65)", border: "1px solid #1f2937", borderRadius: 10, padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 12 }}>
          <div>
            <label style={{ display: "block", fontSize: 11.5, color: "#9ca3af", marginBottom: 4 }}>Presentation Type</label>
            <select
              value={presType}
              onChange={(e) => setPresType(e.target.value)}
              style={{ width: "100%", padding: "8px 10px", borderRadius: 6, background: "#0b1120", border: "1px solid #334155", color: "#f3f4f6", fontSize: 12.5 }}
            >
              {PRESENTATION_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: 11.5, color: "#9ca3af", marginBottom: 4 }}>Presentation Focus / Prompt</label>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the focus of your presentation..."
              style={{ width: "100%", padding: "8px 10px", borderRadius: 6, background: "#0b1120", border: "1px solid #334155", color: "#f3f4f6", fontSize: 12.5 }}
            />
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={handleGenerateOutline}
            disabled={busy || !prompt.trim()}
            style={{ background: "#6366f1", color: "#fff", border: "none", borderRadius: 6, padding: "8px 16px", fontSize: 12.5, fontWeight: 600, cursor: "pointer" }}
          >
            {busy ? "Analyzing Dataset..." : "✨ Preview Slide Outline"}
          </button>
        </div>
      </div>

      {/* Editable Outline Preview */}
      {outline && (
        <div style={{ background: "rgba(15, 23, 42, 0.75)", border: "1px solid rgba(99, 102, 241, 0.35)", borderRadius: 10, padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <input
              type="text"
              value={deckTitle}
              onChange={(e) => setDeckTitle(e.target.value)}
              style={{ flex: 1, minWidth: 260, padding: "7px 10px", borderRadius: 6, background: "#0b1120", border: "1px solid #334155", color: "#f3f4f6", fontSize: 14, fontWeight: 700 }}
            />
            <button
              type="button"
              onClick={handleBuildPptx}
              disabled={busy || editableSlides.length === 0}
              style={{ background: "#10b981", color: "#fff", border: "none", borderRadius: 6, padding: "8px 16px", fontSize: 12.5, fontWeight: 700, cursor: "pointer" }}
            >
              {busy ? "Building .pptx..." : `📥 Confirm & Generate .pptx (${editableSlides.length} Slides)`}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(290px, 1fr))", gap: 12 }}>
            {editableSlides.map((s, idx) => (
              <div key={idx} style={{ background: "#0b1120", border: "1px solid #1f2937", borderRadius: 8, padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "#818cf8" }}>
                    Slide {idx + 1} • {s.layout}
                  </span>
                  {editableSlides.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveSlide(idx)}
                      style={{ background: "transparent", border: "none", color: "#f87171", fontSize: 11, cursor: "pointer" }}
                    >
                      Remove
                    </button>
                  )}
                </div>
                <input
                  type="text"
                  value={s.title}
                  onChange={(e) => handleSlideTitleChange(idx, e.target.value)}
                  style={{ width: "100%", padding: "6px 8px", borderRadius: 5, background: "#111827", border: "1px solid #374151", color: "#f3f4f6", fontSize: 12.5, fontWeight: 600 }}
                />
                <textarea
                  rows={4}
                  value={s.bullets.join("\n")}
                  onChange={(e) => handleSlideBulletsChange(idx, e.target.value)}
                  style={{ width: "100%", padding: "6px 8px", borderRadius: 5, background: "#111827", border: "1px solid #374151", color: "#d1d5db", fontSize: 11.5, resize: "vertical" }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Saved Presentations History */}
      <div style={{ background: "rgba(15, 23, 42, 0.5)", border: "1px solid #1f2937", borderRadius: 10, padding: 16 }}>
        <h4 style={{ fontSize: 14, fontWeight: 700, color: "#f3f4f6", margin: "0 0 10px 0" }}>
          Generated Presentations ({presentations.length})
        </h4>
        {presentations.length === 0 ? (
          <p style={{ fontSize: 12.5, color: "#9ca3af", margin: 0 }}>No presentations generated yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {presentations.map((p) => (
              <div key={p.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", background: "#0b1120", borderRadius: 8, border: "1px solid #1f2937" }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#f3f4f6" }}>{p.title}</div>
                  <div style={{ fontSize: 11.5, color: "#9ca3af" }}>
                    {p.presentation_type} • {p.slide_count} slides • {new Date(p.created_at).toLocaleString()}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    type="button"
                    onClick={() => handleDownload(p)}
                    style={{ background: "#2563eb", color: "#fff", border: "none", borderRadius: 6, padding: "5px 10px", fontSize: 11.5, fontWeight: 600, cursor: "pointer" }}
                  >
                    ⬇ Download .pptx
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ fontSize: 11.5, color: "#f87171" }}
                    onClick={() => handleDelete(p.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
