import React from "react";
import { Sparkles, User as UserIcon, ArrowUpRight } from "lucide-react";
import { ChatMessage } from "../../types";
import { MarkdownRenderer } from "../../components/common/MarkdownRenderer";

interface ChatMessagesProps {
  messages: ChatMessage[];
  loading: boolean;
  loadingStage?: string;
  onSelectSuggestion: (suggestion: string) => void;
  onJumpToSection?: (sectionId: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

function detectSectionLinks(text: string): Array<{ id: string; label: string }> {
  const t = text.toLowerCase();
  const links: Array<{ id: string; label: string }> = [];
  if (t.includes("revenue") || t.includes("category")) links.push({ id: "dd-revenue", label: "Revenue Performance" });
  if (t.includes("profit") || t.includes("margin")) links.push({ id: "dd-profitability", label: "Profitability" });
  if (t.includes("product")) links.push({ id: "dd-products", label: "Product Intelligence" });
  if (t.includes("region")) links.push({ id: "dd-regions", label: "Regional Intelligence" });
  if (t.includes("risk") || t.includes("anomal") || t.includes("concentration")) links.push({ id: "dd-risks", label: "Risks & Anomalies" });
  if (t.includes("opportunit")) links.push({ id: "dd-opportunities", label: "Opportunities" });
  if (t.includes("forecast") || t.includes("trend")) links.push({ id: "dd-trends", label: "Trends & Forecasts" });
  return links.slice(0, 3);
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  loading,
  loadingStage,
  onSelectSuggestion,
  onJumpToSection,
  messagesEndRef,
}) => {
  return (
    <div className="chat-messages">
      {messages.map((msg, i) => {
        const sectionLinks = msg.role === "ai" && onJumpToSection ? detectSectionLinks(msg.text) : [];
        return (
          <div key={i} className={`msg ${msg.role}`}>
            <div className="msg-avatar" aria-hidden="true">
              {msg.role === "user" ? <UserIcon size={14} /> : <Sparkles size={14} />}
            </div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div className="msg-bubble">
                {msg.role === "ai" ? (
                  <MarkdownRenderer content={msg.text} />
                ) : (
                  <span style={{ whiteSpace: "pre-wrap" }}>{msg.text}</span>
                )}
              </div>

              {sectionLinks.length > 0 && onJumpToSection && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 6 }}>
                  {sectionLinks.map((lnk) => (
                    <button
                      key={lnk.id}
                      type="button"
                      onClick={() => onJumpToSection(lnk.id)}
                      style={{
                        background: "rgba(56, 189, 248, 0.08)",
                        border: "1px solid rgba(56, 189, 248, 0.25)",
                        color: "#7dd3fc",
                        borderRadius: 999,
                        padding: "3px 9px",
                        fontSize: 10.5,
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 3,
                      }}
                    >
                      <span>View {lnk.label}</span>
                      <ArrowUpRight size={11} />
                    </button>
                  ))}
                </div>
              )}

              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="chat-suggestions">
                  {msg.suggestions.map((s, j) => (
                    <button
                      key={j}
                      type="button"
                      className="chat-suggestion-chip"
                      onClick={() => onSelectSuggestion(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <div className="msg-time">{msg.time}</div>
            </div>
          </div>
        );
      })}

      {loading && (
        <div className="msg ai">
          <div className="msg-avatar thinking" aria-hidden="true">
            <Sparkles size={14} />
          </div>
          <div className="msg-bubble" style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px" }}>
            <div className="ai-typing-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
              {loadingStage || "Analyzing dataset & computing insights..."}
            </span>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
