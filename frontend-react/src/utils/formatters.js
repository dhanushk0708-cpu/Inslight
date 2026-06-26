export function fmt(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "0";
  }

  const number = Number(value);

  if (Math.abs(number) >= 1e9) {
    return `${(number / 1e9).toFixed(2)}B`;
  }

  if (Math.abs(number) >= 1e6) {
    return `${(number / 1e6).toFixed(1)}M`;
  }

  if (Math.abs(number) >= 1e3) {
    return `${(number / 1e3).toFixed(1)}K`;
  }

  return number % 1 === 0 ? number.toLocaleString() : number.toFixed(1);
}

export function kpiIcon(label) {
  const normalized = (label || "").toLowerCase();

  if (
    normalized.includes("revenue") ||
    normalized.includes("sales") ||
    normalized.includes("total")
  ) {
    return { icon: "💰", className: "revenue" };
  }

  if (normalized.includes("unit") || normalized.includes("quantity")) {
    return { icon: "📦", className: "units" };
  }

  if (normalized.includes("order") || normalized.includes("count")) {
    return { icon: "🛒", className: "orders" };
  }

  if (normalized.includes("rating") || normalized.includes("score")) {
    return { icon: "⭐", className: "rating" };
  }

  if (normalized.includes("profit")) {
    return { icon: "📈", className: "revenue" };
  }

  if (normalized.includes("discount")) {
    return { icon: "🏷️", className: "units" };
  }

  return { icon: "📊", className: "revenue" };
}

export function timeNow() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}
