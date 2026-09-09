import Link from "next/link";

const links = [
  { href: "/roles", label: "Roles" },
  { href: "/trends", label: "Trends" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-line bg-paper/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
        <Link href="/" className="font-serif text-2xl tracking-tight text-ink">
          LevelPath
        </Link>
        <nav className="flex items-center gap-6 text-sm text-ink-soft">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-ink">
              {link.label}
            </Link>
          ))}
          <Link
            href="/roles/sde-1"
            className="rounded-full bg-ink px-4 py-2 text-paper hover:bg-copper-dark"
          >
            Start by level
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-ink-soft sm:flex-row sm:items-center sm:justify-between">
        <p>Interview prep that changes with the level they are hiring for.</p>
        <p>Content is original LevelPath material. Trends rank public corpora, not paid courses.</p>
      </div>
    </footer>
  );
}
