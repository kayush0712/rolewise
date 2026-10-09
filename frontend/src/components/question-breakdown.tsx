"use client";

import { useState } from "react";
import type { Question, ContentBlock } from "@/content/types";
import { Breadcrumb } from "@/components/breadcrumb";
import { StepTabs } from "@/components/step-tabs";
import { SectionHeader } from "@/components/section-header";
import { RequirementsCard, FunctionalNonFunctionalCard } from "@/components/requirements-card";
import { EntityTable } from "@/components/entity-table";
import { ApiTable } from "@/components/api-table";
import { EvolutionCards } from "@/components/evolution-card";
import { ComparisonCard } from "@/components/comparison-card";
import { Callout } from "@/components/callout";
import { ArchitectureFlow } from "@/components/architecture-flow";
import { UploadComparison } from "@/components/upload-comparison";

function difficultyColor(d: string) {
  if (d === "foundation") return "bg-rw-green-soft text-green-700 border-rw-green-border";
  if (d === "core") return "bg-rw-yellow-soft text-amber-700 border-rw-yellow-border";
  return "bg-rw-red-soft text-red-700 border-red-200";
}

function difficultyLabel(d: string) {
  if (d === "foundation") return "EASY";
  if (d === "core") return "MEDIUM";
  return "HARD";
}

function RenderBlock({ block }: { block: ContentBlock }) {
  switch (block.type) {
    case "text":
      return <p className="text-sm leading-relaxed text-rw-ink-secondary">{block.content}</p>;

    case "requirements":
      return <RequirementsCard core={block.core} outOfScope={block.outOfScope} />;

    case "functional-nonfunctional":
      return (
        <FunctionalNonFunctionalCard
          functional={block.functional}
          nonFunctional={block.nonFunctional}
        />
      );

    case "entity-table":
      return <EntityTable entities={block.entities} />;

    case "api-table":
      return <ApiTable endpoints={block.endpoints} />;

    case "evolution":
      return <EvolutionCards options={block.options} />;

    case "architecture-flow":
      return <ArchitectureFlow data={block} />;

    case "comparison":
      return <ComparisonCard data={block} />;

    case "callout":
      return <Callout variant={block.variant} title={block.title} content={block.content} />;

    case "upload-comparison":
      return <UploadComparison options={block.options} />;

    default:
      return null;
  }
}

export function QuestionBreakdownClient({ question }: { question: Question }) {
  const breakdown = question.breakdown!;
  const [activeSection, setActiveSection] = useState(breakdown.sections[0].id);

  return (
    <div>
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: "System Design", href: "/questions?track=hld" },
          { label: "Problem Breakdowns", href: "/roles" },
          { label: question.title },
        ]}
      />

      {/* Question header */}
      <div className="mt-6">
        <p className="mb-1 font-mono text-xs tracking-[0.12em] text-rw-ink-muted">
          SYSTEM DESIGN
        </p>
        <h1 className="text-4xl font-bold text-rw-ink">{question.title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-rw-ink-secondary">
          {question.summary}
        </p>

        {/* Badges */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span
            className={`rounded-full border px-3 py-1 text-xs font-bold ${difficultyColor(question.difficulty)}`}
          >
            {difficultyLabel(question.difficulty)}
          </span>
          <span className="rounded-full border border-rw-border px-3 py-1 text-xs font-medium text-rw-ink-secondary">
            {question.timeboxMinutes}–{question.timeboxMinutes + 10} MIN
          </span>
          <span className="rounded-full border border-rw-border px-3 py-1 text-xs font-medium text-rw-ink-secondary">
            SYSTEM DESIGN
          </span>
        </div>

        {/* Target role */}
        <div className="mt-4 flex items-center gap-2 text-sm text-rw-ink-secondary">
          <span>Target role</span>
          <span className="rounded-full border border-rw-border bg-rw-surface-alt px-3 py-1 font-medium text-rw-ink">
            {breakdown.targetRole}
          </span>
        </div>

        {/* CTA buttons */}
        <div className="mt-6 flex gap-3">
          <button className="rounded-lg bg-rw-ink px-6 py-2.5 text-sm font-medium text-rw-bg hover:opacity-90">
            Start Practice
          </button>
          <button className="rounded-lg border border-rw-border px-6 py-2.5 text-sm font-medium text-rw-ink hover:bg-rw-surface-alt">
            Read Breakdown
          </button>
        </div>
      </div>

      {/* Focus callout */}
      <div className="mt-8 rounded-lg border-l-4 border-rw-ink bg-rw-surface p-5">
        <h4 className="font-semibold text-rw-ink">{breakdown.targetRole} Focus</h4>
        <p className="mt-1 text-sm text-rw-ink-secondary">
          For this role, expect deeper discussion around scalability, consistency, synchronization,
          large-file handling, failure recovery, and architectural trade-offs.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {breakdown.focusAreas.map((area) => (
            <span
              key={area}
              className="rounded-full border border-rw-border bg-rw-surface-alt px-3 py-1 text-xs text-rw-ink-secondary"
            >
              {area}
            </span>
          ))}
        </div>
      </div>

      {/* Step tabs */}
      <div className="mt-8">
        <StepTabs
          sections={breakdown.sections}
          activeId={activeSection}
          onSelect={setActiveSection}
        />
      </div>

      {/* Scrollbar indicator */}
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-rw-border">
        <div
          className="h-full rounded-full bg-rw-ink transition-all"
          style={{
            width: `${
              ((breakdown.sections.findIndex((s) => s.id === activeSection) + 1) /
                breakdown.sections.length) *
              100
            }%`,
          }}
        />
      </div>

      {/* All sections rendered */}
      <div className="mt-10 space-y-16">
        {breakdown.sections.map((section) => (
          <section key={section.id} id={section.id}>
            <SectionHeader
              stepNumber={section.stepNumber}
              label={section.label}
              title={section.title}
            />
            <div className="space-y-6">
              {section.blocks.map((block, i) => (
                <RenderBlock key={i} block={block} />
              ))}
            </div>
            {/* Divider */}
            <div className="mt-10 border-b border-rw-border" />
          </section>
        ))}
      </div>
    </div>
  );
}
