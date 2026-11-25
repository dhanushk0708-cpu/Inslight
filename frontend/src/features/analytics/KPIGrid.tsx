"use client";
import React, { useEffect, useState } from "react";
import { KPICard as KPICardType } from "../../types";
import {
  IndianRupee,
  TrendingUp,
  Package,
  ShoppingCart,
  Percent,
  BarChart3,
} from "lucide-react";

function KpiIcon({ label }: { label: string }) {
  const l = (label || "").toLowerCase();
  if (l.includes("revenue") || l.includes("sales") || l.includes("profit") || l.includes("total")) {
    return <IndianRupee size={16} />;
  }
  if (l.includes("margin") || l.includes("percent") || l.includes("discount")) {
    return <Percent size={16} />;
  }
  if (l.includes("unit") || l.includes("volume") || l.includes("quantity")) {
    return <Package size={16} />;
  }
  if (l.includes("order") || l.includes("count")) {
    return <ShoppingCart size={16} />;
  }
  if (l.includes("growth") || l.includes("trend")) {
    return <TrendingUp size={16} />;
  }
  return <BarChart3 size={16} />;
}

const AnimatedValue: React.FC<{ value: string }> = ({ value }) => {
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    setDisplay(value);
    if (typeof window === "undefined") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

    const match = value.match(/^([^0-9.-]*)([0-9][0-9,]*(?:\.[0-9]+)?)(.*)$/);
    if (!match) return;

    const [, prefix, numStr, suffix] = match;
    const target = parseFloat(numStr.replace(/,/g, ""));
    if (!isFinite(target) || target === 0) return;

    const decimals = numStr.includes(".") ? numStr.split(".")[1].length : 0;
    const duration = 420;
    const start = performance.now();
    let raf = 0;

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      const formatted = decimals > 0
        ? current.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
        : Math.round(current).toLocaleString("en-IN");
      setDisplay(`${prefix}${formatted}${suffix}`);
      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        setDisplay(value);
      }
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);

  return <>{display}</>;
};

interface KPIGridProps {
  cards: KPICardType[];
}

export const KPIGrid: React.FC<KPIGridProps> = React.memo(({ cards }) => {
  if (!cards?.length) return null;

  return (
    <div className="kpi-grid">
      {cards.map((kpi, i) => (
        <div className="kpi-card" key={`${kpi.label}-${i}`}>
          <div className="kpi-header">
            <div className="kpi-label">{kpi.label}</div>
            <div className="kpi-icon">
              <KpiIcon label={kpi.label} />
            </div>
          </div>
          <div className="kpi-value">
            <AnimatedValue value={kpi.value} />
          </div>
          {kpi.trend && (
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color:
                  kpi.trend_direction === "up"
                    ? "#10b981"
                    : kpi.trend_direction === "down"
                    ? "#ef4444"
                    : "#9aa4bc",
                marginTop: 6,
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              {kpi.trend_direction === "up" ? "↑" : kpi.trend_direction === "down" ? "↓" : "•"}{" "}
              {kpi.trend}
            </span>
          )}
        </div>
      ))}
    </div>
  );
});

KPIGrid.displayName = "KPIGrid";
