import type { ApiEndpoint } from "@/content/types";

const methodColors: Record<string, string> = {
  GET: "method-get",
  POST: "method-post",
  PUT: "method-put",
  DELETE: "method-delete",
  PATCH: "method-patch",
};

export function ApiTable({ endpoints }: { endpoints: ApiEndpoint[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-rw-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-rw-border bg-rw-surface-alt">
            <th className="px-5 py-3 text-left font-mono text-xs tracking-[0.1em] text-rw-ink-muted">
              METHOD
            </th>
            <th className="px-5 py-3 text-left font-mono text-xs tracking-[0.1em] text-rw-ink-muted">
              ENDPOINT
            </th>
            <th className="px-5 py-3 text-left font-mono text-xs tracking-[0.1em] text-rw-ink-muted">
              DESCRIPTION
            </th>
          </tr>
        </thead>
        <tbody>
          {endpoints.map((ep, i) => (
            <tr
              key={`${ep.method}-${ep.endpoint}`}
              className={i < endpoints.length - 1 ? "border-b border-rw-border" : ""}
            >
              <td className="px-5 py-3.5">
                <span
                  className={`inline-block rounded px-2.5 py-1 font-mono text-xs font-bold ${
                    methodColors[ep.method] ?? ""
                  }`}
                >
                  {ep.method}
                </span>
              </td>
              <td className="px-5 py-3.5 font-mono text-rw-ink">{ep.endpoint}</td>
              <td className="px-5 py-3.5 text-rw-ink-secondary">{ep.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
