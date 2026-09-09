import type { ArchitectureFlowBlock } from "@/content/types";

export function ArchitectureFlow({ data }: { data: ArchitectureFlowBlock }) {
  return (
    <div className="space-y-6">
      {/* Flow Diagram */}
      <div className="overflow-hidden rounded-lg border border-rw-border bg-rw-surface p-6">
        {/* Visual flow: row of nodes */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          {data.nodes.map((node, i) => (
            <div key={node.label} className="flex items-center gap-3">
              <div
                className={`rounded-lg px-5 py-2.5 text-sm font-medium ${
                  node.type === "critical"
                    ? "bg-rw-ink text-white"
                    : "border border-rw-border bg-rw-surface text-rw-ink"
                }`}
              >
                {node.label}
              </div>
              {i < data.nodes.length - 1 && (
                <span className="text-rw-ink-muted">→</span>
              )}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center justify-center gap-6 text-xs text-rw-ink-secondary">
          <span className="flex items-center gap-2">
            <span className="h-3 w-3 rounded bg-rw-ink" />
            Critical path
          </span>
          <span className="flex items-center gap-2">
            <span className="h-3 w-3 rounded border border-rw-border bg-rw-surface" />
            Supporting service
          </span>
        </div>
      </div>

      {/* Explanation */}
      {data.explanation && (
        <div>
          <h4 className="mb-2 font-semibold text-rw-ink">Why this architecture?</h4>
          <p className="text-sm leading-relaxed text-rw-ink-secondary">{data.explanation}</p>
        </div>
      )}
    </div>
  );
}
