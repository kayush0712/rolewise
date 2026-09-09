import { getQuestion } from "@/lib/catalog";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { QuestionBreakdownClient } from "@/components/question-breakdown";

type Props = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const question = await getQuestion(slug);
  return { title: question?.title ?? "Question" };
}

export default async function QuestionPage({ params }: Props) {
  const { slug } = await params;
  const question = await getQuestion(slug);

  if (!question) notFound();

  // Ensure this question has a breakdown
  if (!question.breakdown) notFound();

  // Convert to the format the client component expects
  const clientQuestion = {
    slug: question.slug,
    title: question.title,
    track: question.track,
    summary: question.prompt,
    difficulty: question.difficulty,
    roles: question.roles ?? [],
    timeboxMinutes: question.timeboxMinutes,
    prompt: question.prompt,
    outline: question.outline,
    levelBar: question.levelBar,
    sources: question.sources,
    breakdown: {
      sections: question.breakdown.sections.map((s) => ({
        id: s.id,
        stepNumber: s.stepNumber,
        label: s.label,
        title: s.title,
        blocks: s.blocks as any[],
      })),
      focusAreas: question.breakdown.focusAreas,
      targetRole: question.breakdown.targetRole,
      totalSections: question.breakdown.totalSections,
      completedSections: question.breakdown.completedSections,
    },
  };

  return <QuestionBreakdownClient question={clientQuestion as any} />;
}
