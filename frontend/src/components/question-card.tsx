import { difficultyLabel } from "@/lib/catalog";
import type { Question, RoleSlug } from "@/content/types";
import Link from "next/link";

export function QuestionCard({
  question,
  role,
}: {
  question: Question;
  role: RoleSlug;
}) {
  return (
    <Link
      href={`/roles/${role}/questions/${question.slug}`}
      className="block border border-line bg-paper p-5 hover:border-copper"
    >
      <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.16em] text-ink-soft">
        <span>{question.track}</span>
        <span>{difficultyLabel(question.difficulty)}</span>
      </div>
      <h3 className="mt-3 font-serif text-2xl text-ink">{question.title}</h3>
      <p className="mt-2 text-sm leading-6 text-ink-soft">{question.summary}</p>
    </Link>
  );
}
