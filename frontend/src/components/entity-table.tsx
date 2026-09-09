import type { EntityTableBlock } from "@/content/types";

export function EntityTable({ entities }: { entities: EntityTableBlock["entities"] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-rw-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-rw-border bg-rw-surface-alt">
            <th className="px-5 py-3 text-left font-mono text-xs tracking-[0.1em] text-rw-ink-muted">
              ENTITY
            </th>
            <th className="px-5 py-3 text-left font-mono text-xs tracking-[0.1em] text-rw-ink-muted">
              PURPOSE
            </th>
          </tr>
        </thead>
        <tbody>
          {entities.map((entity, i) => (
            <tr
              key={entity.name}
              className={i < entities.length - 1 ? "border-b border-rw-border" : ""}
            >
              <td className="px-5 py-3.5 font-semibold text-rw-ink">{entity.name}</td>
              <td className="px-5 py-3.5 text-rw-ink-secondary">{entity.purpose}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
