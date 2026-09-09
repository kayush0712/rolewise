export function SectionHeader({
  stepNumber,
  label,
  title,
}: {
  stepNumber: number;
  label: string;
  title: string;
}) {
  return (
    <div className="mb-6">
      <p className="mb-1 font-mono text-xs tracking-[0.12em] text-rw-ink-muted">
        {String(stepNumber).padStart(2, "0")} — {label}
      </p>
      <h2 className="text-3xl font-bold text-rw-ink">{title}</h2>
    </div>
  );
}
