import { Link } from "@tanstack/react-router";
import { Video, LayoutDashboard, Bell, Train, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { useIsMobile } from "@/hooks/use-mobile";
import { useSidebar } from "@/components/sidebar-context-utils";

const navItems = [
  { to: "/live", label: "Live Monitoring", icon: Video },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/alerts", label: "Alerts", icon: Bell },
] as const;

/** Poll backend health endpoint every 30 seconds */
async function checkBackendHealth(): Promise<boolean> {
  await apiFetch("/health");
  return true;
}

export function Sidebar() {
  const isMobile = useIsMobile();
  const { isOpen, close } = useSidebar();
  const { isError: isHttpError, isPending: isHttpPending } = useQuery({
    queryKey: ["backendHealth"],
    queryFn: checkBackendHealth,
    refetchInterval: 15_000,
    staleTime: 0,
    retry: 3,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10_000),
    refetchOnWindowFocus: true,
    refetchOnMount: true,
  });

  const isHttpHealthy = !isHttpError && !isHttpPending;
  const isHealthy = isHttpHealthy;
  const isPulsing = isHealthy || isHttpPending;

  // Set label and color based on health state
  let statusLabel = "Checking...";
  let statusColor = "#ff9f0a"; // orange

  if (isHttpError) {
    statusLabel = "Backend Unreachable";
    statusColor = "#ff2d55"; // red
  } else if (isHttpPending) {
    statusLabel = "Checking...";
    statusColor = "#ff9f0a"; // orange
  } else if (isHealthy) {
    statusLabel = "All Systems Operational";
    statusColor = "#00e676"; // green
  }

  const isDrawerVisible = isMobile ? isOpen : true;

  return (
    <>
      {isMobile && isOpen ? (
        <div className="fixed inset-0 z-40 bg-black/40" onClick={close} />
      ) : null}
      <aside
        className={`fixed z-50 flex h-screen w-64 flex-col border-r border-border bg-sidebar shadow-2xl transition-transform duration-200 md:sticky md:top-0 md:shadow-none ${
          isMobile ? (isDrawerVisible ? "translate-x-0" : "-translate-x-full") : "translate-x-0"
        }`}
      >
        <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-600 shadow-lg shadow-cyan-500/30">
            <Train className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="text-lg font-bold leading-tight">
              RailMind <span className="text-primary">AI</span>
            </div>
            <div className="text-[10px] text-muted-foreground">
              AI-Powered Railway Safety System
            </div>
          </div>
          {isMobile ? (
            <button
              type="button"
              onClick={close}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground transition hover:bg-secondary"
              aria-label="Close sidebar"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              onClick={isMobile ? close : undefined}
              className="relative flex items-center gap-3 rounded-r-lg border-l-[3px] border-transparent px-3 py-2.5 text-sm font-medium text-muted-foreground transition-all hover:bg-secondary hover:text-foreground data-[status=active]:bg-primary/10 data-[status=active]:text-foreground data-[status=active]:border-primary data-[status=active]:shadow-[var(--glow-primary)]"
              activeProps={{ "data-status": "active" } as never}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="hud-panel m-3 rounded-xl bg-card p-4">
          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
          <div className="text-xs font-semibold text-muted-foreground">System Status</div>
          <div className="mt-2 flex items-center gap-2 text-sm">
            <span className="relative flex h-2.5 w-2.5">
              {isPulsing && (
                <span
                  className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
                  style={{ backgroundColor: statusColor, boxShadow: `0 0 12px ${statusColor}` }}
                />
              )}
              <span
                className="relative inline-flex h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: statusColor, boxShadow: `0 0 8px ${statusColor}` }}
              />
            </span>
            <span className="font-mono tracking-wider" style={{ color: statusColor }}>
              {statusLabel}
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
