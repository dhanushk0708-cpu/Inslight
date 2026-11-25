"use client";
import React, { useState, useEffect, useRef } from "react";

interface VoiceControlsProps {
  lastAiText?: string;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({ lastAiText }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      setIsSupported(true);
      const saved = localStorage.getItem("inslight_voice_response");
      if (saved === "true") {
        setEnabled(true);
      }
    }
  }, []);

  const toggleEnabled = () => {
    const next = !enabled;
    setEnabled(next);
    localStorage.setItem("inslight_voice_response", String(next));
    if (!next && isSpeaking) {
      stopSpeaking();
    }
  };

  const cleanTextForSpeech = (rawText: string): string => {
    // Strip markdown formatting, code blocks, tables, and raw SQL queries
    return rawText
      .replace(/```[\s\S]*?```/g, "Code block omitted.")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/[*#_~]/g, "")
      .replace(/https?:\/\/\S+/g, "link")
      .slice(0, 350); // Keep summary concise for voice
  };

  const speakText = (text: string) => {
    if (!isSupported || !text) return;

    window.speechSynthesis.cancel();
    const clean = cleanTextForSpeech(text);
    if (!clean.trim()) return;

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (isSupported) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // Auto-play when enabled and new AI message arrives
  useEffect(() => {
    if (enabled && lastAiText && isSupported) {
      speakText(lastAiText);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastAiText]);

  if (!isSupported) return null;

  return (
    <div
      className="voice-controls-bar"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        fontSize: "11px",
        color: "var(--text-muted, #94a3b8)",
        background: "rgba(30, 41, 59, 0.6)",
        padding: "3px 8px",
        borderRadius: "6px",
        border: "1px solid var(--border-color, #334155)",
      }}
    >
      <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
        <input
          type="checkbox"
          checked={enabled}
          onChange={toggleEnabled}
          style={{ cursor: "pointer" }}
        />
        <span>AI Voice Response</span>
      </label>

      {lastAiText && (
        <div style={{ display: "inline-flex", gap: "4px", marginLeft: "4px" }}>
          {isSpeaking ? (
            <button
              onClick={stopSpeaking}
              title="Stop audio narration"
              style={{
                background: "#dc2626",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "2px 6px",
                cursor: "pointer",
                fontSize: "10px",
              }}
            >
              ⏹️ Stop
            </button>
          ) : (
            <button
              onClick={() => speakText(lastAiText)}
              title="Read AI explanation aloud"
              style={{
                background: "#2563eb",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "2px 6px",
                cursor: "pointer",
                fontSize: "10px",
              }}
            >
              🔊 Read Aloud
            </button>
          )}
        </div>
      )}
    </div>
  );
};
