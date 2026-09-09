import type { EvolutionOption } from "@/content/types";

export function EvolutionCards({ options }: { options: EvolutionOption[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {options.map((opt) => (
        <div
          key={opt.number}
          className={`relative flex flex-col rounded-lg border p-5 ${
            opt.recommended
              ? "border-rw-ink bg-rw-ink text-white"
              : "border-rw-border bg-rw-surface"
          }`}
        >
          {opt.recommended && (
            <span className="absolute right-4 top-4 rounded-full bg-white/20 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
              Recommended
            </span>
          )}
          <p
            className={`font-mono text-xs ${
              opt.recommended ? "text-white/50" : "text-rw-ink-muted"
            }`}
          >
            {opt.number}
          </p>
          <h4
            className={`mt-1 text-lg font-bold ${
              opt.recommended ? "text-white" : "text-rw-ink"
            }`}
          >
            {opt.label}
          </h4>
          <p
            className={`mt-3 flex-1 whitespace-pre-line text-sm ${
              opt.recommended ? "text-white/80" : "text-rw-ink-secondary"
            }`}
          >
            {opt.description}
          </p>
          <div className="mt-4 space-y-1.5 text-sm">
            {opt.pros.map((pro) => (
              <p key={pro}>
                <span
                  className={`mr-2 font-bold ${
                    opt.recommended ? "text-green-300" : "text-green-600"
                  }`}
                >
                  PRO
                </span>
                <span className={opt.recommended ? "text-white/80" : "text-rw-ink-secondary"}>
                  {pro}
                </span>
              </p>
            ))}
            {opt.cons.map((con) => (
              <p key={con}>
                <span
                  className={`mr-2 font-bold ${
                    opt.recommended ? "text-red-300" : "text-red-500"
                  }`}
                >
                  CON
                </span>
                <span className={opt.recommended ? "text-white/80" : "text-rw-ink-secondary"}>
                  {con}
                </span>
              </p>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
