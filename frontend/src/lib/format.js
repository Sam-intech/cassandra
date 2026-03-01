export function formatPrice(value) {
  if (typeof value !== "number") return "-";
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export function formatVpin(value) {
  if (typeof value !== "number") return "-";
  return value.toFixed(4);
}

export function classifyAlert(vpin) {
  if (typeof vpin !== "number") return "NORMAL";
  if (vpin >= 0.85) return "CRITICAL";
  if (vpin >= 0.75) return "HIGH";
  if (vpin >= 0.65) return "ELEVATED";
  if (vpin >= 0.5) return "MODERATE";
  return "NORMAL";
}

export function formatTimestamp(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "-";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
