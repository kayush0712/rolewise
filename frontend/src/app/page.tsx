import { getRoles, getQuestionsForRole, getQuestions } from "@/lib/catalog";
import Link from "next/link";

export default async function Home() {
  const roles = await getRoles();
  const allQuestions = await getQuestions();
  const questionsWithBreakdowns = allQuestions.filter(
    (q) => q.breakdown
  );

  return (
    <div>
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-rw-ink">Welcome back</h1>
        <p className="mt-2 text-sm text-rw-ink-secondary">
          Pick up where you left off, or start a new problem breakdown.
        </p>
      </div>

      {/* Featured Breakdowns */}
      <section className="mb-10">
        <h2 className="mb-4 text-xs font-medium tracking-[0.12em] text-rw-ink-muted">
          PROBLEM BREAKDOWNS
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {questionsWithBreakdowns.map((q) => (
            <Link
              key={q.slug}
              href={`/questions/${q.slug}`}
              className="group rounded-xl border border-rw-border bg-rw-surface p-5 transition-all hover:border-rw-ink-muted hover:shadow-sm"
            >
              <p className="mb-1 font-mono text-[10px] tracking-[0.1em] text-rw-ink-muted">
                SYSTEM DESIGN
              </p>
              <h3 className="text-lg font-bold text-rw-ink group-hover:text-rw-ink">
                {q.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-rw-ink-secondary">
                {q.prompt}
              </p>
              <div className="mt-4 flex items-center gap-2">
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
                    q.difficulty === "foundation"
                      ? "border-green-200 bg-green-50 text-green-700"
                      : q.difficulty === "core"
                      ? "border-amber-200 bg-amber-50 text-amber-700"
                      : "border-red-200 bg-red-50 text-red-700"
                  }`}
                >
                  {q.difficulty === "foundation" ? "EASY" : q.difficulty === "core" ? "MEDIUM" : "HARD"}
                </span>
                <span className="text-[10px] text-rw-ink-muted">
                  {q.timeboxMinutes} MIN
                </span>
              </div>
            </Link>
          ))}

          {/* Placeholder cards for upcoming breakdowns */}
          {["Design a URL Shortener", "Design a News Feed", "Design a Chat System"].map(
            (title) => (
              <div
                key={title}
                className="flex flex-col items-center justify-center rounded-xl border border-dashed border-rw-border bg-rw-surface-alt p-5 text-center"
              >
                <p className="text-sm font-medium text-rw-ink-muted">{title}</p>
                <p className="mt-1 text-xs text-rw-ink-muted">Coming soon</p>
              </div>
            )
          )}
        </div>
      </section>

      {/* Roles */}
      <section>
        <h2 className="mb-4 text-xs font-medium tracking-[0.12em] text-rw-ink-muted">
          EXPLORE BY ROLE
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {roles.map((role) => (
            <Link
              key={role.slug}
              href={`/roles/${role.slug}`}
              className="group flex items-center justify-between rounded-xl border border-rw-border bg-rw-surface p-4 transition-all hover:border-rw-ink-muted hover:shadow-sm"
            >
              <div>
                <p className="text-xs text-rw-ink-muted">{role.band}</p>
                <p className="mt-0.5 font-semibold text-rw-ink">{role.title}</p>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-rw-ink-muted transition-colors group-hover:text-rw-ink"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
