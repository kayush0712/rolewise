import type { UploadComparisonBlock } from "@/content/types";

export function UploadComparison({ options }: { options: UploadComparisonBlock["options"] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {options.map((opt) => (
        <div
          key={opt.label}
          className={`rounded-lg border p-5 ${
            opt.recommended
              ? "border-rw-ink bg-rw-ink text-white"
              : "border-rw-border bg-rw-surface"
          }`}
        >
          <div className="flex items-center justify-between">
            <h4
              className={`font-semibold ${
                opt.recommended ? "text-white" : "text-rw-ink"
              }`}
            >
              {opt.label}
            </h4>
            {opt.recommended && (
              <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                Recommended
              </span>
            )}
          </div>
          <p
            className={`mt-2 font-mono text-sm ${
              opt.recommended ? "text-white/70" : "text-rw-ink-muted"
            }`}
          >
            {opt.description}
          </p>
          {opt.details && (
            <p
              className={`mt-3 text-sm leading-relaxed ${
                opt.recommended ? "text-white/80" : "text-rw-ink-secondary"
              }`}
            >
              {opt.details}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
