import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="font-serif text-5xl">That path does not exist</h1>
      <p className="mt-4 text-ink-soft">The role, track, or question is not in the catalog yet.</p>
      <Link href="/roles" className="mt-8 inline-block text-copper">
        Back to roles →
      </Link>
    </main>
  );
}
