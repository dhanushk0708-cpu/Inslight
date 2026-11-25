import React from "react";

interface LoadingProps {
  text?: string;
}

export const Loading: React.FC<LoadingProps> = ({ text = "Analyzing business data..." }) => {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 20px", gap: 12 }}>
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          border: "3px solid rgba(255, 255, 255, 0.1)",
          borderTopColor: "#6366f1",
          animation: "spin 0.8s linear infinite"
        }}
      />
      <div style={{ fontSize: 12, color: "var(--text-muted)", letterSpacing: "0.3px" }}>{text}</div>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};
