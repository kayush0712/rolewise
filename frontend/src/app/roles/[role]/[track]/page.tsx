import { QuestionCard } from "@/components/question-card";
import { TrackPills } from "@/components/track-pills";
import { getQuestionsForRole, getRole, getTrack } from "@/lib/catalog";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

type Props = {
  params: Promise<{ role: string; track: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { role: roleSlug, track: trackSlug } = await params;
  const role = await getRole(roleSlug);
  const track = await getTrack(trackSlug);
  return { title: role && track ? `${track.title} · ${role.title}` : "Track" };
}

export default async function RoleTrackPage({ params }: Props) {
  const { role: roleSlug, track: trackSlug } = await params;
  const role = await getRole(roleSlug);
  const track = await getTrack(trackSlug);
  if (!role || !track) notFound();

  const questions = await getQuestionsForRole(role.slug, track.slug);

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <p className="text-xs uppercase tracking-[0.2em] text-copper">
        {role.title} · {track.title}
      </p>
      <h1 className="mt-3 font-serif text-5xl text-ink">{track.title}</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8 text-ink-soft">{track.summary}</p>
      <div className="mt-10">
        <TrackPills role={role.slug} active={track.slug} />
      </div>
      {questions.length === 0 ? (
        <p className="mt-10 text-ink-soft">No questions tagged for this level yet.</p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {questions.map((question) => (
            <QuestionCard key={question.slug} question={question} role={role.slug} />
          ))}
        </div>
      )}
    </main>
  );
}
