export type Variant = "green" | "red" | "amber" | "purple" | "cyan" | "blue" | "muted";

interface BadgeProps {
  label: string;
  variant?: Variant;
}

const VARIANT_STYLES: Record<Variant, { bg: string; color: string }> = {
  green: { bg: "var(--green-dim)", color: "var(--green)" },
  red: { bg: "var(--red-dim)", color: "var(--red)" },
  amber: { bg: "var(--amber-dim)", color: "var(--amber)" },
  purple: { bg: "var(--purple-dim)", color: "var(--purple)" },
  cyan: { bg: "var(--cyan-dim)", color: "var(--cyan)" },
  blue: { bg: "var(--accent-dim)", color: "var(--accent)" },
  muted: { bg: "transparent", color: "var(--text-secondary)" },
};

/** Ink stamp: outlined, uppercase, the variant colour is the ink. Styling lives in ledger.css. */
export function Badge({ label, variant = "muted" }: BadgeProps) {
  const { color } = VARIANT_STYLES[variant];
  return (
    <span className="badge" style={{ color, display: "inline-block", lineHeight: 1.4 }}>
      {label}
    </span>
  );
}
