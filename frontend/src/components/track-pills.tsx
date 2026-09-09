import type { RoleSlug, TrackSlug } from "@/content/types";
import { getTracks } from "@/lib/catalog";
import Link from "next/link";

export async function TrackPills({
  role,
  active,
}: {
  role: RoleSlug;
  active?: TrackSlug | "all";
}) {
  const tracks = await getTracks();
  const current = active ?? "all";

  return (
    <div className="flex flex-wrap gap-2">
      <Link
        href={`/roles/${role}`}
        className={`rounded-full border px-4 py-1.5 text-sm ${
          current === "all"
            ? "border-ink bg-ink text-paper"
            : "border-line text-ink-soft hover:border-ink hover:text-ink"
        }`}
      >
        All
      </Link>
      {tracks.map((track) => (
        <Link
          key={track.slug}
          href={`/roles/${role}/${track.slug}`}
          className={`rounded-full border px-4 py-1.5 text-sm ${
            current === track.slug
              ? "border-ink bg-ink text-paper"
              : "border-line text-ink-soft hover:border-ink hover:text-ink"
          }`}
        >
          {track.shortTitle}
        </Link>
      ))}
    </div>
  );
}
