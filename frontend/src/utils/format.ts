export function clamp01(x: number): number {
  if (Number.isNaN(x)) return 0;
  return Math.max(0, Math.min(1, x));
}

export function pct(x: number): string {
  return `${Math.round(clamp01(x) * 100)}%`;
}

export function fmtDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function statusLabel(s: "active" | "inactive" | "unknown"): string {
  if (s === "active") return "Тривога зараз: ТАК";
  if (s === "inactive") return "Тривога зараз: НІ";
  return "Тривога зараз: невідомо";
}
