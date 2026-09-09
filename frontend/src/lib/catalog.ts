/**
 * Data catalog — fetches from FastAPI backend.
 *
 * For SSR/ISR pages, we call the backend directly at localhost:8000.
 * The frontend uses /api/* which gets proxied by Next.js rewrites.
 */

import type { Question, RoleSlug, TrackSlug, Difficulty, Role, Track } from "@/content/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    next: { revalidate: 60 }, // ISR: revalidate every 60 seconds
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ─── Types matching MongoDB documents ─────────────────

export type RoleDoc = {
  _id: string;
  title: string;
  shortTitle: string;
  band: string;
  summary: string;
  interviewMix: { track: string; weight: number }[];
  bar: string[];
};

export type TrackDoc = {
  _id: string;
  title: string;
  shortTitle: string;
  summary: string;
};

export type QuestionVersion = {
  role: string;
  levelBar: string;
  breakdown?: {
    focusAreas: string[];
    targetRole: string;
    totalSections: number;
    completedSections: number;
    sections: {
      id: string;
      stepNumber: number;
      label: string;
      title: string;
      blocks: Record<string, unknown>[];
    }[];
  };
};

export type QuestionDoc = {
  _id: string;
  slug: string;
  title: string;
  track: string;
  difficulty: string;
  timeboxMinutes: number;
  prompt: string;
  outline: string[];
  sources: string[];
  status: string;
  discoveredBy: string | null;
  versions: QuestionVersion[];
};

// ─── Role helpers (adapt to old interface) ────────────

export async function getRoles(): Promise<Role[]> {
  const roles = await apiFetch<RoleDoc[]>("/api/roles");
  return roles.map((r) => ({
    slug: r._id as RoleSlug,
    title: r.title,
    shortTitle: r.shortTitle,
    band: r.band,
    summary: r.summary,
    interviewMix: r.interviewMix as any,
    bar: r.bar,
  }));
}

export async function getRole(slug: string): Promise<Role | undefined> {
  try {
    const r = await apiFetch<RoleDoc>(`/api/roles/${slug}`);
    return {
      slug: r._id as RoleSlug,
      title: r.title,
      shortTitle: r.shortTitle,
      band: r.band,
      summary: r.summary,
      interviewMix: r.interviewMix as any,
      bar: r.bar,
    };
  } catch {
    return undefined;
  }
}

// ─── Track helpers ────────────────────────────────────

export async function getTracks(): Promise<Track[]> {
  const tracks = await apiFetch<TrackDoc[]>("/api/tracks");
  return tracks.map((t) => ({
    slug: t._id as TrackSlug,
    title: t.title,
    shortTitle: t.shortTitle,
    summary: t.summary,
  }));
}

export async function getTrack(slug: string): Promise<Track | undefined> {
  try {
    const t = await apiFetch<TrackDoc>(`/api/tracks/${slug}`);
    return {
      slug: t._id as TrackSlug,
      title: t.title,
      shortTitle: t.shortTitle,
      summary: t.summary,
    };
  } catch {
    return undefined;
  }
}

// ─── Question helpers ─────────────────────────────────

function mapQuestionDoc(doc: QuestionDoc): Question {
  return {
    slug: doc.slug,
    title: doc.title,
    track: doc.track as TrackSlug,
    summary: doc.prompt,
    difficulty: doc.difficulty as Difficulty,
    roles: (doc.versions?.map((v) => v.role) || []) as RoleSlug[],
    timeboxMinutes: doc.timeboxMinutes,
    prompt: doc.prompt,
    outline: doc.outline,
    levelBar: Object.fromEntries(
      doc.versions?.map((v) => [v.role, v.levelBar]) || []
    ),
    sources: doc.sources,
    breakdown: doc.versions?.find((v) => v.breakdown)?.breakdown as any,
  };
}

export async function getQuestions(filters?: {
  track?: string;
  role?: string;
  difficulty?: string;
}): Promise<Question[]> {
  const params = new URLSearchParams();
  if (filters?.track) params.set("track", filters.track);
  if (filters?.role) params.set("role", filters.role);
  if (filters?.difficulty) params.set("difficulty", filters.difficulty);

  const qs = params.toString();
  const docs = await apiFetch<QuestionDoc[]>(`/api/questions${qs ? `?${qs}` : ""}`);
  return docs.map(mapQuestionDoc);
}

export async function getQuestion(slug: string, role?: string): Promise<Question | undefined> {
  const params = role ? `?role=${role}` : "";
  try {
    const doc = await apiFetch<QuestionDoc>(`/api/questions/${slug}${params}`);
    return mapQuestionDoc(doc);
  } catch {
    return undefined;
  }
}

export async function getQuestionsForRole(roleSlug: string, track?: string): Promise<Question[]> {
  const params = new URLSearchParams({ role: roleSlug });
  if (track) params.set("track", track);
  const docs = await apiFetch<QuestionDoc[]>(`/api/questions?${params.toString()}`);
  return docs.map(mapQuestionDoc);
}

// ─── Backward compat helper ───────────────────────────

export function difficultyLabel(value: string): string {
  if (value === "foundation") return "Foundation";
  if (value === "core") return "Core";
  return "Stretch";
}
