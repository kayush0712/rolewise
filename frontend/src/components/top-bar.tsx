import { SearchIcon, RefreshIcon, BellIcon } from "./icons";
import { SignInButton, Show, UserButton } from "@clerk/nextjs";
import { auth, clerkClient } from "@clerk/nextjs/server";
import { RoleSelector } from "./role-selector";

export async function TopBar() {
  const { userId } = await auth();
  
  let targetRoleDisplay = "Select Target Role";
  let currentRoleDisplay = "Select Current Role";
  
  if (userId) {
    const client = await clerkClient();
    const user = await client.users.getUser(userId);
    const targetRole = user.publicMetadata?.targetRole as string;
    const currentRole = user.publicMetadata?.currentRole as string;
    
    if (targetRole === "sde_2") targetRoleDisplay = "Mid-Level (SDE II)";
    else if (targetRole === "sde_3") targetRoleDisplay = "Senior (SDE III)";
    else if (targetRole === "staff") targetRoleDisplay = "Staff";
    else if (targetRole === "principal") targetRoleDisplay = "Principal+";
    else if (user.publicMetadata?.onboardingComplete) targetRoleDisplay = "Role Set";

    if (currentRole === "student") currentRoleDisplay = "Student / New Grad";
    else if (currentRole === "sde_1") currentRoleDisplay = "Junior (SDE I)";
    else if (currentRole === "sde_2") currentRoleDisplay = "Mid-Level (SDE II)";
    else if (currentRole === "sde_3") currentRoleDisplay = "Senior (SDE III)";
    else if (currentRole === "staff") currentRoleDisplay = "Staff / Principal";
  }

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
        {userId ? (
          <RoleSelector currentRole={currentRoleDisplay} targetRole={targetRoleDisplay} />
        ) : (
          <div className="flex items-center gap-2 rounded-full border border-rw-border px-4 py-2 text-sm transition-colors cursor-not-allowed opacity-50">
            <span className="h-2 w-2 rounded-full bg-rw-ink-muted" />
            <span className="font-medium text-rw-ink-muted">Sign In Required</span>
          </div>
        )}
        <button className="rounded-lg p-2 text-rw-ink-secondary hover:bg-rw-bg">
          <RefreshIcon width={16} height={16} />
        </button>
        <button className="rounded-lg p-2 text-rw-ink-secondary hover:bg-rw-bg">
          <BellIcon width={16} height={16} />
        </button>
        
        {/* Clerk Auth UI */}
        <Show when="signed-out">
          <div className="ml-2">
            <SignInButton mode="modal">
              <button className="rounded-lg bg-rw-ink px-4 py-2 text-sm font-medium text-white hover:bg-rw-ink-secondary transition-colors btn-whimsy">
                Sign In
              </button>
            </SignInButton>
          </div>
        </Show>
        <Show when="signed-in">
          <div className="ml-2 h-9 w-9">
            <UserButton appearance={{ elements: { avatarBox: "h-9 w-9" } }} />
          </div>
        </Show>
      </div>
    </header>
  );
}
