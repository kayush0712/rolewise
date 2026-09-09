import { QuestionCard } from "@/components/question-card";
import { TrackPills } from "@/components/track-pills";
import { getQuestionsForRole, getRole } from "@/lib/catalog";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

type Props = {
  params: Promise<{ role: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { role: slug } = await params;
  const role = await getRole(slug);
  return { title: role?.title ?? "Role" };
}

export default async function RolePage({ params }: Props) {
  const { role: slug } = await params;
  const role = await getRole(slug);
  if (!role) notFound();

  const questions = await getQuestionsForRole(role.slug);

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <p className="text-xs uppercase tracking-[0.2em] text-copper">{role.band}</p>
      <h1 className="mt-3 font-serif text-5xl text-ink">{role.title}</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8 text-ink-soft">{role.summary}</p>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <section>
          <h2 className="text-sm uppercase tracking-[0.16em] text-ink-soft">Interview mix</h2>
          <ul className="mt-4 space-y-3">
            {role.interviewMix.map((item) => (
              <li key={item.track}>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="uppercase tracking-wide">{item.track}</span>
                  <span className="text-ink-soft">{item.weight}%</span>
                </div>
                <div className="h-2 bg-chip">
                  <div className="h-2 bg-moss" style={{ width: `${item.weight}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </section>
        <section className="border border-line bg-chip p-6">
          <h2 className="text-sm uppercase tracking-[0.16em] text-ink-soft">What this bar looks like</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6">
            {role.bar.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>

      <div className="mt-14">
        <TrackPills role={role.slug} active="all" />
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {questions.map((question) => (
            <QuestionCard key={question.slug} question={question} role={role.slug} />
          ))}
        </div>
      </div>
    </main>
  );
}
