import Link from "next/link";
import { ChevronRightIcon } from "./icons";

export function Breadcrumb({
  items,
}: {
  items: { label: string; href?: string }[];
}) {
  return (
    <nav className="flex items-center gap-1 text-sm text-rw-ink-secondary">
      {items.map((item, i) => (
        <span key={item.label} className="flex items-center gap-1">
          {i > 0 && (
            <ChevronRightIcon width={12} height={12} className="text-rw-ink-muted" />
          )}
          {item.href ? (
            <Link href={item.href} className="hover:text-rw-ink">
              {item.label}
            </Link>
          ) : (
            <span className="font-medium text-rw-ink">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
