import type { ReactNode } from "react";
interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: number;
  deltaLabel?: string;
  color?: string;
  icon?: ReactNode;
  trend?: number[];
}
export function MetricCard({
  label,
  value,
  unit,
  delta,
  deltaLabel,
  icon,
}: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        {icon} {label}
      </div>
      <div className="metric-value">
        {typeof value === "number" ? value.toLocaleString() : value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {delta !== undefined && (
        <div
          className="metric-detail"
          style={{ color: delta >= 0 ? "var(--green)" : "var(--red)" }}
        >
          {delta >= 0 ? "+" : ""}
          {delta.toFixed(3)} vs previous episode
        </div>
      )}
      {deltaLabel && <div className="metric-detail">{deltaLabel}</div>}
    </div>
  );
}
