import React, { useState, useCallback, useRef } from "react";
import { Send } from "lucide-react";
import { VoiceInput } from "../voice/VoiceInput";
import { VoiceControls } from "../voice/VoiceControls";

interface ChatInputProps {
  onSend: (text: string) => void;
  loading: boolean;
  lastAiText?: string;
}

export const ChatInput: React.FC<ChatInputProps> = React.memo(({ onSend, loading, lastAiText }) => {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submitText = () => {
    if (!text.trim() || loading) return;
    onSend(text.trim());
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitText();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitText();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };

  const handleVoiceTranscript = useCallback((transcript: string) => {
    setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
  }, []);

  return (
    <div className="chat-input-area" style={{ background: "rgba(7, 11, 20, 0.96)" }}>
      <div
        style={{
          marginBottom: 8,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 6,
          flexWrap: "wrap",
        }}
      >
        <VoiceInput onTranscript={handleVoiceTranscript} disabled={loading} />
        <VoiceControls lastAiText={lastAiText} />
      </div>

      <form onSubmit={handleSubmit} autoComplete="off">
        <div className="chat-input-wrap" style={{ alignItems: "flex-end", padding: "6px 6px 6px 12px" }}>
          <textarea
            ref={textareaRef}
            rows={1}
            className="chat-input"
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a follow-up question... (Enter to send, Shift+Enter for new line)"
            disabled={loading}
            aria-label="Ask business intelligence question"
            style={{
              resize: "none",
              minHeight: 24,
              maxHeight: 120,
              lineHeight: 1.45,
              fontFamily: "inherit",
            }}
          />
          <button
            className="chat-send-btn"
            type="submit"
            disabled={loading || !text.trim()}
            aria-label="Send query"
            title="Send (Enter)"
          >
            <Send size={15} />
          </button>
        </div>
      </form>
    </div>
  );
});

ChatInput.displayName = "ChatInput";
