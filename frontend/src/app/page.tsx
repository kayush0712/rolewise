import { getRoles, getQuestions } from "@/lib/catalog";
import Link from "next/link";

export default async function Home() {
  const roles = await getRoles();
  const allQuestions = await getQuestions();
  const questionsWithBreakdowns = allQuestions.filter((q) => q.breakdown);

  return (
    <div className="flex flex-col items-center">
      {/* 1. Hero Section */}
      <section className="mb-20 mt-16 flex max-w-4xl flex-col items-center px-4 text-center">
        <div className="easter-egg-zone mb-4 inline-flex items-center gap-2 rounded-full border border-rw-border bg-rw-surface-alt px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-rw-ink-muted">
          <span className="flex h-2 w-2 rounded-full bg-rw-green"></span>
          Now supporting Principal (L7) tracks ✨
        </div>
        <h1 className="font-serif text-5xl tracking-tight text-rw-ink sm:text-7xl">
          Crack the System Design Interview for Your Exact Level
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-rw-ink-secondary sm:text-xl">
          Stop studying generic questions. We break down the exact LLD and HLD expectations for SDE 1 through Principal so you know precisely what your interviewers are looking for.
        </p>
        <div className="mt-10 flex flex-col gap-4 sm:flex-row">
          <Link
            href="/roles"
            className="btn-whimsy rounded-lg bg-rw-ink px-8 py-3.5 text-base font-bold text-rw-bg shadow-lg"
          >
            Start Practicing for Free
          </Link>
          <Link
            href="/concepts"
            className="btn-whimsy rounded-lg border border-rw-border bg-rw-surface px-8 py-3.5 text-base font-bold text-rw-ink"
          >
            View Core Concepts
          </Link>
        </div>
      </section>

      {/* 2. Social Proof Band */}
      <section className="mb-24 w-full border-y border-rw-border bg-rw-surface-alt py-10">
        <div className="mx-auto max-w-5xl px-6 text-center">
          <p className="mb-6 text-sm font-semibold uppercase tracking-widest text-rw-ink-muted">
            Engineers using Rolewise have landed offers at
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 text-xl font-bold text-rw-ink-secondary opacity-60 sm:gap-16 sm:text-2xl">
            <span>Google</span>
            <span>Meta</span>
            <span>Stripe</span>
            <span>Netflix</span>
            <span>Amazon</span>
          </div>
        </div>
      </section>

      {/* 3. Interactive Role Selection */}
      <section className="mb-24 w-full max-w-6xl px-6">
        <div className="mb-10 text-center">
          <h2 className="font-serif text-4xl text-rw-ink">Pick your target loop</h2>
          <p className="mt-3 text-rw-ink-secondary">
            Interview expectations shift dramatically as you go up. Pick your level.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {roles.map((role) => (
            <Link
              key={role.slug}
              href={`/roles/${role.slug}`}
              className="group flex flex-col justify-between rounded-2xl border border-rw-border bg-rw-surface p-6 transition-all hover:border-rw-ink-muted hover:shadow-md"
            >
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-rw-ink-muted">
                  {role.band}
                </p>
                <p className="mt-2 text-2xl font-bold text-rw-ink">{role.title}</p>
              </div>
              <div className="mt-8 flex items-center justify-between">
                <span className="text-sm font-medium text-rw-ink-secondary transition-colors group-hover:text-rw-ink">
                  View breakdown →
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 4. Curiosity Gap / Premium Tease for Breakdowns */}
      <section className="mb-24 w-full max-w-6xl px-6">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <h2 className="font-serif text-4xl text-rw-ink">Featured Breakdowns</h2>
            <p className="mt-3 text-rw-ink-secondary">
              Step-by-step architectural deep dives for real-world systems.
            </p>
          </div>
          <Link
            href="/roles"
            className="hidden text-sm font-bold text-rw-ink hover:underline sm:block"
          >
            View all problems →
          </Link>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {questionsWithBreakdowns.slice(0, 3).map((q) => (
            <div
              key={q.slug}
              className="group relative flex flex-col overflow-hidden rounded-2xl border border-rw-border bg-rw-surface transition-all hover:border-rw-ink-muted hover:shadow-md"
            >
              <div className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <span className="rounded-full border border-rw-border bg-rw-surface-alt px-3 py-1 text-xs font-bold uppercase tracking-wider text-rw-ink-muted">
                    SYSTEM DESIGN
                  </span>
                  {/* Padlock Icon to signal locked/premium state */}
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-rw-ink-muted"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-rw-ink group-hover:text-rw-ink">
                  {q.title}
                </h3>
                <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-rw-ink-secondary">
                  {q.prompt}
                </p>
              </div>

              {/* Fake Auth Wall overlay on hover */}
              <div className="absolute inset-0 flex items-center justify-center bg-rw-surface/80 opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
                <Link
                  href={`/questions/${q.slug}`}
                  className="btn-whimsy rounded-full bg-rw-ink px-6 py-2.5 text-sm font-bold text-rw-bg shadow-lg"
                >
                  Unlock Breakdown 🔓
                </Link>
              </div>

              <div className="mt-auto border-t border-rw-border bg-rw-surface-alt px-6 py-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-xs font-bold ${
                      q.difficulty === "foundation"
                        ? "border-rw-green-border bg-rw-green-soft text-rw-green"
                        : q.difficulty === "core"
                        ? "border-rw-yellow-border bg-rw-yellow-soft text-rw-yellow"
                        : "border-transparent bg-rw-red-soft text-rw-red"
                    }`}
                  >
                    {q.difficulty === "foundation"
                      ? "EASY"
                      : q.difficulty === "core"
                      ? "MEDIUM"
                      : "HARD"}
                  </span>
                  <span className="text-xs font-medium text-rw-ink-muted">
                    {q.timeboxMinutes} MIN
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
