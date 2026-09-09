import type { ComparisonBlock } from "@/content/types";
import { CheckIcon } from "./icons";

export function ComparisonCard({ data }: { data: ComparisonBlock }) {
  return (
    <div className="overflow-hidden rounded-lg border border-rw-border bg-rw-surface">
      {/* Title bar */}
      <div className="border-b border-rw-border bg-rw-surface-alt px-5 py-3.5">
        <h4 className="font-semibold text-rw-ink">{data.title}</h4>
      </div>

      {/* Options side by side */}
      <div className="grid grid-cols-2 divide-x divide-rw-border">
        <div className="p-5">
          <p className="mb-1.5 font-mono text-[11px] tracking-wide text-rw-ink-muted">
            {data.optionA.label}
          </p>
          <p className="text-sm text-rw-ink-secondary">{data.optionA.description}</p>
        </div>
        <div className="p-5">
          <p className="mb-1.5 font-mono text-[11px] tracking-wide text-rw-ink-muted">
            {data.optionB.label}
          </p>
          <p className="text-sm text-rw-ink-secondary">{data.optionB.description}</p>
        </div>
      </div>

      {/* Recommendation */}
      <div className="border-t border-rw-border px-5 py-4">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-rw-green-border bg-rw-green-soft px-3 py-1 text-sm font-medium text-green-700">
          <CheckIcon width={14} height={14} />
          {data.recommendation}
        </span>
        <p className="mt-2 text-sm text-rw-ink-secondary">{data.rationale}</p>
      </div>
    </div>
  );
}
