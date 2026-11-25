import React from "react";

export const SkeletonCard: React.FC<{ height?: number }> = ({ height = 96 }) => (
  <div
    className="skeleton-box"
    style={{ height, borderRadius: "var(--radius)", width: "100%" }}
    aria-hidden="true"
  />
);

export const SkeletonGrid: React.FC = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
    <div className="kpi-grid">
      <SkeletonCard height={92} />
      <SkeletonCard height={92} />
      <SkeletonCard height={92} />
      <SkeletonCard height={92} />
    </div>
    <div className="chart-grid">
      <SkeletonCard height={240} />
      <SkeletonCard height={240} />
    </div>
  </div>
);
