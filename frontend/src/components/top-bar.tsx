import { SearchIcon, RefreshIcon, BellIcon } from "./icons";

export function TopBar() {
  return (
    <header className="sticky top-0 z-30 flex h-[var(--topbar-h)] items-center justify-between border-b border-rw-border bg-rw-surface px-6">
      {/* Center: Search */}
      <div className="flex flex-1 justify-center">
        <div className="relative w-full max-w-md">
          <SearchIcon
            width={15}
            height={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-rw-ink-muted"
          />
          <input
            type="search"
            placeholder="Search..."
            className="w-full rounded-lg border border-rw-border bg-rw-surface-alt py-2 pl-9 pr-12 text-sm text-rw-ink placeholder:text-rw-ink-muted focus:border-rw-ink-secondary focus:outline-none"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-rw-border bg-rw-surface px-1.5 py-0.5 font-mono text-[10px] text-rw-ink-muted">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right: Role selector, refresh, bell, avatar */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-full border border-rw-border px-4 py-2 text-sm">
          <span className="h-2 w-2 rounded-full bg-rw-green" />
          <span className="font-medium text-rw-ink">Senior Software Engineer</span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-rw-ink-muted"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
        <button className="rounded-lg p-2 text-rw-ink-secondary hover:bg-rw-bg">
          <RefreshIcon width={16} height={16} />
        </button>
        <button className="rounded-lg p-2 text-rw-ink-secondary hover:bg-rw-bg">
          <BellIcon width={16} height={16} />
        </button>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-rw-ink text-xs font-bold text-white">
          JS
        </div>
      </div>
    </header>
  );
}
