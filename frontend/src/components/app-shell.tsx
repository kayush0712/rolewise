import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";
import { RightPanel } from "./right-panel";

export function AppShell({
  children,
  showRightPanel = true,
}: {
  children: React.ReactNode;
  showRightPanel?: boolean;
}) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />

      {/* Main area (offset by sidebar) */}
      <div className="ml-[var(--sidebar-w)] flex flex-1 flex-col">
        {/* Top bar */}
        <TopBar />

        {/* Content + optional right panel */}
        <div className="flex flex-1">
          <main
            className={`flex-1 overflow-y-auto p-8 ${
              showRightPanel ? "xl:mr-[var(--right-panel-w)]" : ""
            }`}
          >
            {children}
          </main>

          {showRightPanel && <RightPanel />}
        </div>
      </div>
    </div>
  );
}
