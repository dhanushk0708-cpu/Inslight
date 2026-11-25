import React from "react";

interface BrandLogoProps {
  size?: number;
  showText?: boolean;
  subtitle?: string;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = 38,
  showText = true,
  subtitle = "AI Business Intelligence",
}) => {
  return (
    <div className="chat-brand-left" style={{ display: "flex", alignItems: "center", gap: 11 }}>
      <div
        className="chat-logo"
        style={{
          width: size,
          height: size,
          borderRadius: Math.round(size * 0.3),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        <svg
          width={Math.round(size * 0.56)}
          height={Math.round(size * 0.56)}
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect x="3" y="13" width="4" height="8" rx="1.2" fill="rgba(255,255,255,0.75)" />
          <rect x="10" y="8" width="4" height="13" rx="1.2" fill="rgba(255,255,255,0.92)" />
          <rect x="17" y="4" width="4" height="17" rx="1.2" fill="#FFFFFF" />
          <path
            d="M3 10L10 5L17 2"
            stroke="#38BDF8"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      {showText && (
        <div>
          <div className="chat-brand-name">INSLIGHT</div>
          {subtitle && <div className="chat-brand-sub">{subtitle}</div>}
        </div>
      )}
    </div>
  );
};
