import { RoleCard } from "@/components/role-card";
import { getRoles } from "@/lib/catalog";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Roles",
};

export default async function RolesPage() {
  const roles = await getRoles();

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="font-serif text-5xl text-ink">Pick the loop you are walking into</h1>
      <p className="mt-4 max-w-2xl text-ink-soft">
        Mix of coding, LLD, HLD, and behavioral shifts as you go up. Start at the
        level on the job description, not the one you wish they asked.
      </p>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {roles.map((role) => (
          <RoleCard key={role.slug} role={role} />
        ))}
      </div>
    </main>
  );
}
