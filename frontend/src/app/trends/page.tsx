
import { getTracks } from "@/lib/catalog";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Trends",
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type TrendHit = {
  slug: string;
  title: string;
  track: string;
  score: number;
  why: string;
  sources: string[];
};

type TrendsResponse = {
  generatedAt: string;
  method: string;
  hits: TrendHit[];
};

async function getTrends(track?: string): Promise<TrendsResponse> {
  const url = track ? `${API_BASE}/api/trends?track=${track}` : `${API_BASE}/api/trends`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Failed to fetch trends");
  return res.json();
}

export default async function TrendsPage({
  searchParams,
}: {
  searchParams: Promise<{ track?: string }>;
}) {
  const { track } = await searchParams;
  const tracks = await getTracks();
  const active = tracks.find((item) => item.slug === track)?.slug;
  const report = await getTrends(active);

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <p className="text-xs uppercase tracking-[0.2em] text-copper">Trend analyzer</p>
      <h1 className="mt-3 font-serif text-5xl text-ink">What people are practicing</h1>
      <p className="mt-4 max-w-2xl leading-7 text-ink-soft">
        The agent ranks HLD, LLD, coding, and behavioral prompts using public
        corpora (system-design-primer, awesome-low-level-design, and similar).
        Wire a search API later; the ranking contract stays the same.
      </p>
      <p className="mt-3 font-mono text-xs text-ink-soft">
        {report.method} · generated {new Date(report.generatedAt).toUTCString()}
      </p>

      <div className="mt-8 flex flex-wrap gap-2">
        <Link
          href="/trends"
          className={`rounded-full border px-4 py-1.5 text-sm ${
            !active ? "border-ink bg-ink text-paper" : "border-line"
          }`}
        >
          All tracks
        </Link>
        {tracks.map((item) => (
          <Link
            key={item.slug}
            href={`/trends?track=${item.slug}`}
            className={`rounded-full border px-4 py-1.5 text-sm ${
              active === item.slug ? "border-ink bg-ink text-paper" : "border-line"
            }`}
          >
            {item.shortTitle}
          </Link>
        ))}
      </div>

      <ol className="mt-10 divide-y divide-line border border-line">
        {report.hits.map((hit, index) => (
          <li key={hit.slug} className="grid gap-2 p-5 sm:grid-cols-[3rem_1fr_auto]">
            <span className="font-mono text-ink-soft">{String(index + 1).padStart(2, "0")}</span>
            <div>
              <p className="font-serif text-2xl">{hit.title}</p>
              <p className="mt-1 text-sm text-ink-soft">{hit.why}</p>
            </div>
            <div className="text-right text-sm">
              <p className="uppercase tracking-wide text-ink-soft">{hit.track}</p>
              <p className="mt-1 font-mono">{hit.score}</p>
            </div>
          </li>
        ))}
      </ol>
    </main>
  );
}
