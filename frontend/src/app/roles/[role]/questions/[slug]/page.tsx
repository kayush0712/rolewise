import { getQuestion, getRole } from "@/lib/catalog";
import type { RoleSlug } from "@/content/types";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

type Props = {
  params: Promise<{ role: string; slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const question = await getQuestion(slug);
  return { title: question?.title ?? "Question" };
}

export default async function QuestionPage({ params }: Props) {
  const { role: roleSlug, slug } = await params;
  const role = await getRole(roleSlug);
  const question = await getQuestion(slug);
  if (!role || !question || !question.roles.includes(role.slug as RoleSlug)) {
    notFound();
  }

  const levelNote = question.levelBar[role.slug as RoleSlug];

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link href={`/roles/${role.slug}/${question.track}`} className="text-sm text-copper">
        ← {role.title} · {question.track}
      </Link>
      <p className="mt-8 text-xs uppercase tracking-[0.2em] text-ink-soft">
        {question.timeboxMinutes} min · {question.track}
      </p>
      <h1 className="mt-3 font-serif text-5xl text-ink">{question.title}</h1>
      <p className="mt-5 text-lg leading-8 text-ink-soft">{question.prompt}</p>

      {levelNote ? (
        <aside className="mt-10 border border-line bg-chip p-6">
          <p className="text-xs uppercase tracking-[0.16em] text-copper">
            {role.title} bar
          </p>
          <p className="mt-3 leading-7">{levelNote}</p>
        </aside>
      ) : null}

      <section className="mt-12">
        <h2 className="font-serif text-3xl">Walkthrough spine</h2>
        <ol className="mt-6 space-y-4">
          {question.outline.map((step, index) => (
            <li key={step} className="flex gap-4">
              <span className="font-mono text-sm text-ink-soft">{String(index + 1).padStart(2, "0")}</span>
              <span className="leading-7">{step}</span>
            </li>
          ))}
        </ol>
      </section>

      {question.roles.length > 1 ? (
        <section className="mt-12 border-t border-line pt-8">
          <h2 className="text-sm uppercase tracking-[0.16em] text-ink-soft">
            Same problem, other levels
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {question.roles.map((other) => (
              <Link
                key={other}
                href={`/roles/${other}/questions/${question.slug}`}
                className={`rounded-full border px-4 py-1.5 text-sm ${
                  other === role.slug
                    ? "border-ink bg-ink text-paper"
                    : "border-line hover:border-ink"
                }`}
              >
                {other}
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
