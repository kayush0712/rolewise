"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookIcon,
  LightbulbIcon,
  GlobeIcon,
  DatabaseIcon,
  WifiIcon,
  CodeIcon,
  ZapIcon,
  MicIcon,
  BarChartIcon,
  ClockIcon,
  SettingsIcon,
  SearchIcon,
} from "./icons";

const navSections = [
  {
    label: "LEARN",
    items: [
      { href: "/", label: "Overview", icon: BookIcon },
      { href: "/concepts", label: "Core Concepts", icon: LightbulbIcon },
      { href: "/questions?track=hld", label: "System Design", icon: GlobeIcon },
      { href: "/questions?track=lld", label: "Databases", icon: DatabaseIcon },
      { href: "/trends", label: "Networking", icon: WifiIcon },
      { href: "/questions?track=coding", label: "Coding", icon: CodeIcon },
    ],
  },
  {
    label: "PRACTICE",
    items: [
      { href: "/roles", label: "Roles", icon: ZapIcon },
      { href: "/mock", label: "Mock Interviews", icon: MicIcon },
    ],
  },
  {
    label: "PROGRESS",
    items: [
      { href: "/progress", label: "My Progress", icon: BarChartIcon },
      { href: "/history", label: "History", icon: ClockIcon },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 hidden md:flex h-full w-[var(--sidebar-w)] flex-col border-r border-rw-border bg-rw-surface">
      {/* Logo */}
      <div className="px-5 pb-2 pt-5">
        <Link href="/" className="text-lg font-bold tracking-tight text-rw-ink">
          ROLEWISE
        </Link>
      </div>

      {/* Sidebar Search removed (moved to top bar) */}

      {/* Nav Sections */}
      <nav className="flex-1 overflow-y-auto px-3 pb-4">
        {navSections.map((section) => (
          <div key={section.label} className="mb-4">
            <p className="mb-1 px-2 text-[11px] font-medium tracking-[0.08em] text-rw-ink-muted">
              {section.label}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href.split("?")[0]));
                const IconComp = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors ${
                        isActive
                          ? "bg-rw-bg font-medium text-rw-ink"
                          : "text-rw-ink-secondary hover:bg-rw-bg hover:text-rw-ink"
                      }`}
                    >
                      <IconComp width={16} height={16} className="shrink-0" />
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Settings at bottom */}
      <div className="border-t border-rw-border px-3 py-3">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm text-rw-ink-secondary hover:bg-rw-bg hover:text-rw-ink"
        >
          <SettingsIcon width={16} height={16} className="shrink-0" />
          Settings
        </Link>
      </div>
    </aside>
  );
}
