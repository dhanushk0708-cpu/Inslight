"use client";
import React, { useState, useEffect, useRef } from "react";
import { VoiceLanguage } from "../../types";

interface VoiceInputProps {
  onTranscript: (transcript: string) => void;
  disabled?: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, disabled }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [language, setLanguage] = useState<VoiceLanguage>("en-IN");
  const [statusText, setStatusText] = useState<string>("");
  const [showPrivacyNotice, setShowPrivacyNotice] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check Web Speech API browser support
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
        setStatusText("Listening... Speak your business question");
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript.trim()) {
          onTranscript(finalTranscript.trim());
          setStatusText("Speech captured! Review before sending.");
        }
      };

      recognition.onerror = (event: any) => {
        setIsListening(false);
        if (event.error === "not-allowed") {
          setStatusText("Microphone permission denied. Enable microphone in browser.");
        } else if (event.error === "no-speech") {
          setStatusText("No speech detected. Please try speaking again.");
        } else if (event.error === "network") {
          setStatusText("Network error during speech recognition.");
        } else {
          setStatusText(`Recognition error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
      setStatusText("Web Speech API not supported in this browser. (Use Chrome or Edge)");
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
    };
  }, [onTranscript]);

  const toggleListening = () => {
    if (!isSupported || disabled) return;

    if (isListening) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsListening(false);
      setStatusText("");
    } else {
      try {
        recognitionRef.current.lang = language;
        recognitionRef.current.start();
      } catch (err) {
        setStatusText("Could not access microphone.");
      }
    }
  };

  return (
    <div className="voice-input-container" style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
      {/* Language Selector */}
      <select
        className="voice-lang-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value as VoiceLanguage)}
        disabled={isListening || disabled}
        aria-label="Speech Recognition Language"
        style={{
          fontSize: "11px",
          background: "var(--bg-card, #1e293b)",
          color: "var(--text-muted, #94a3b8)",
          border: "1px solid var(--border-color, #334155)",
          borderRadius: "6px",
          padding: "3px 6px",
          cursor: "pointer",
        }}
      >
        <option value="en-IN">English (India)</option>
        <option value="hi-IN">हिन्दी (Hindi)</option>
        <option value="kn-IN">ಕನ್ನಡ (Kannada)</option>
      </select>

      {/* Microphone Toggle Button */}
      <button
        type="button"
        onClick={toggleListening}
        disabled={!isSupported || disabled}
        className={`voice-mic-btn ${isListening ? "listening" : ""}`}
        title={
          !isSupported
            ? "Speech Recognition unsupported in this browser"
            : isListening
            ? "Click to stop listening"
            : "Click to speak your query"
        }
        aria-label="Voice input"
        style={{
          background: isListening ? "#dc2626" : "transparent",
          color: isListening ? "#ffffff" : isSupported ? "#3b82f6" : "#64748b",
          border: isListening ? "1px solid #ef4444" : "1px solid var(--border-color, #334155)",
          borderRadius: "6px",
          padding: "4px 8px",
          cursor: isSupported && !disabled ? "pointer" : "not-allowed",
          display: "flex",
          alignItems: "center",
          gap: "4px",
          fontSize: "12px",
          transition: "all 0.2s ease",
          animation: isListening ? "pulse 1.5s infinite" : "none",
        }}
      >
        <span>{isListening ? "🔴" : "🎙️"}</span>
        <span style={{ fontSize: "11px", fontWeight: 500 }}>
          {isListening ? "Listening..." : "Voice"}
        </span>
      </button>

      {/* Privacy Notice Info Pill */}
      <button
        type="button"
        onClick={() => setShowPrivacyNotice(!showPrivacyNotice)}
        style={{
          background: "none",
          border: "none",
          color: "var(--text-muted, #64748b)",
          cursor: "pointer",
          fontSize: "11px",
          padding: "0 2px",
        }}
        title="Voice Privacy Notice"
      >
        ℹ️
      </button>

      {/* Privacy Notice Tooltip / Popover */}
      {showPrivacyNotice && (
        <div
          style={{
            position: "absolute",
            bottom: "50px",
            right: "20px",
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "8px",
            padding: "12px",
            maxWidth: "320px",
            fontSize: "11px",
            color: "#cbd5e1",
            boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
            zIndex: 100,
          }}
        >
          <div style={{ fontWeight: 600, color: "#38bdf8", marginBottom: "4px" }}>
            🎙️ Voice Privacy & Security
          </div>
          <p style={{ margin: 0, lineHeight: 1.4 }}>
            Speech recognition runs directly through your browser's Web Speech API. Audio is never
            recorded or stored on our servers. The converted text is placed in the chat input for you
            to review and edit before sending.
          </p>
          <button
            onClick={() => setShowPrivacyNotice(false)}
            style={{
              marginTop: "8px",
              background: "#1e293b",
              border: "1px solid #475569",
              color: "#f8fafc",
              borderRadius: "4px",
              padding: "2px 8px",
              cursor: "pointer",
              fontSize: "10px",
            }}
          >
            Got it
          </button>
        </div>
      )}

      {/* Status feedback bar */}
      {statusText && (
        <span
          style={{
            fontSize: "11px",
            color: isListening ? "#ef4444" : "#94a3b8",
            marginLeft: "4px",
            fontStyle: "italic",
          }}
        >
          {statusText}
        </span>
      )}
    </div>
  );
};
