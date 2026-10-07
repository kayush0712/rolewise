"use client";

import { usePathname } from "next/navigation";
import { CheckSquareIcon, SquareIcon } from "./icons";

type InterviewStep = {
  label: string;
  completed: boolean;
  current?: boolean;
};

const defaultSteps: InterviewStep[] = [
  { label: "Understand the problem", completed: true },
  { label: "Functional requirements", completed: true },
  { label: "Non-functional requirements", completed: true },
  { label: "Entities", completed: false, current: true },
  { label: "API design", completed: false },
  { label: "High-level design", completed: false },
  { label: "Deep dives", completed: false },
  { label: "Trade-offs", completed: false },
];

export function RightPanel({
  steps = defaultSteps,
  progress = 72,
  completedSections = 18,
  totalSections = 25,
  targetRole = "Senior Software Engineer",
  focusAreas = ["Scalability", "Distributed Systems", "Consistency", "Reliability"],
}: {
  steps?: InterviewStep[];
  progress?: number;
  completedSections?: number;
  totalSections?: number;
  targetRole?: string;
  focusAreas?: string[];
}) {
  const pathname = usePathname();
  if (pathname === "/roles") return null;

  return (
    <aside className="fixed right-0 top-[var(--topbar-h)] z-20 hidden h-[calc(100vh-var(--topbar-h))] w-[var(--right-panel-w)] overflow-y-auto border-l border-rw-border bg-rw-surface p-5 xl:block">
      {/* Interview Plan */}
      <section className="mb-8">
        <h3 className="mb-4 text-xs font-medium tracking-[0.12em] text-rw-ink-muted">
          INTERVIEW PLAN
        </h3>
        <ul className="space-y-2.5">
          {steps.map((step) => (
            <li key={step.label} className="flex items-start gap-2.5">
              {step.completed ? (
                <CheckSquareIcon
                  width={18}
                  height={18}
                  className="mt-0.5 shrink-0 text-rw-green"
                />
              ) : step.current ? (
                <div className="mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded border-2 border-rw-ink">
                  <div className="h-2 w-2 rounded-sm bg-rw-ink" />
                </div>
              ) : (
                <SquareIcon
                  width={18}
                  height={18}
                  className="mt-0.5 shrink-0 text-rw-border"
                />
              )}
              <span
                className={`text-sm leading-tight ${
                  step.completed
                    ? "text-rw-ink-muted line-through"
                    : step.current
                    ? "font-medium text-rw-ink"
                    : "text-rw-ink-secondary"
                }`}
              >
                {step.label}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* Progress */}
      <section className="mb-8">
        <h3 className="mb-3 text-xs font-medium tracking-[0.12em] text-rw-ink-muted">
          YOUR PROGRESS
        </h3>
        <p className="text-4xl font-bold text-rw-ink">{progress}%</p>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-rw-bg">
          <div
            className="h-full rounded-full bg-rw-ink transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-rw-ink-secondary">
          {completedSections} / {totalSections} sections completed
        </p>
      </section>

      {/* Target Role */}
      <section>
        <h3 className="mb-3 text-xs font-medium tracking-[0.12em] text-rw-ink-muted">
          TARGET ROLE
        </h3>
        <p className="text-sm font-semibold text-rw-ink">{targetRole}</p>
        <p className="mt-1 text-xs text-rw-ink-muted">Focus areas</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {focusAreas.map((area) => (
            <span
              key={area}
              className="rounded-full border border-rw-border bg-rw-surface-alt px-2.5 py-1 text-xs text-rw-ink-secondary"
            >
              {area}
            </span>
          ))}
        </div>
      </section>
    </aside>
  );
}
