import type { Role } from "@/content/types";
import Link from "next/link";

export function RoleCard({ role }: { role: Role }) {
  return (
    <Link
      href={`/roles/${role.slug}`}
      className="group flex flex-col border border-line bg-chip p-6 transition-colors hover:border-copper hover:bg-paper"
    >
      <p className="text-xs uppercase tracking-[0.18em] text-ink-soft">{role.band}</p>
      <h2 className="mt-3 font-serif text-3xl text-ink">{role.title}</h2>
      <p className="mt-3 flex-1 text-sm leading-6 text-ink-soft">{role.summary}</p>
      <p className="mt-6 text-sm text-copper group-hover:text-copper-dark">Open path →</p>
    </Link>
  );
}
