"use client";

import type { BreakdownSection } from "@/content/types";

export function StepTabs({
  sections,
  activeId,
  onSelect,
}: {
  sections: BreakdownSection[];
  activeId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {sections.map((section) => {
        const isActive = section.id === activeId;
        return (
          <button
            key={section.id}
            onClick={() => onSelect(section.id)}
            className={`flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "border-rw-ink bg-rw-ink text-white"
                : "border-rw-border bg-rw-surface text-rw-ink-secondary hover:border-rw-ink-muted hover:text-rw-ink"
            }`}
          >
            <span
              className={`font-mono text-xs ${
                isActive ? "text-white/70" : "text-rw-ink-muted"
              }`}
            >
              {String(section.stepNumber).padStart(2, "0")}
            </span>
            {section.title.split(" ").slice(0, 2).join(" ")}
          </button>
        );
      })}
    </div>
  );
}
