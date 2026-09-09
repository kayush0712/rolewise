import { CheckIcon } from "./icons";

export function RequirementsCard({
  core,
  outOfScope,
}: {
  core: string[];
  outOfScope: string[];
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-lg border border-rw-border bg-rw-surface p-5">
        <h4 className="mb-3 font-semibold text-rw-ink">Core Requirements</h4>
        <ul className="space-y-2.5">
          {core.map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm text-rw-ink-secondary">
              <CheckIcon
                width={16}
                height={16}
                className="mt-0.5 shrink-0 text-rw-ink"
              />
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="rounded-lg border border-rw-border bg-rw-surface p-5">
        <h4 className="mb-3 font-semibold text-rw-ink">Out of Scope</h4>
        <ul className="space-y-2.5">
          {outOfScope.map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm text-rw-ink-muted">
              <span className="mt-1 block h-px w-4 shrink-0 bg-rw-ink-muted" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function FunctionalNonFunctionalCard({
  functional,
  nonFunctional,
}: {
  functional: string[];
  nonFunctional: string[];
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-lg border border-rw-border bg-rw-surface p-5">
        <h4 className="mb-3 font-semibold text-rw-ink">Functional</h4>
        <ul className="space-y-2">
          {functional.map((item) => (
            <li key={item} className="flex items-center gap-2 text-sm text-rw-ink-secondary">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-rw-ink" />
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div className="rounded-lg border border-rw-border bg-rw-surface p-5">
        <h4 className="mb-3 font-semibold text-rw-ink">Non-functional</h4>
        <ul className="space-y-2">
          {nonFunctional.map((item) => (
            <li key={item} className="flex items-center gap-2 text-sm text-rw-ink-secondary">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-rw-ink" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
