import { Link } from "@tanstack/react-router";
import { Video, LayoutDashboard, Bell, Train } from "lucide-react";

const navItems = [
  { to: "/live", label: "Live Monitoring", icon: Video },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/alerts", label: "Alerts", icon: Bell },
] as const;

export function Sidebar() {
  return (
    <aside className="flex h-screen w-64 flex-col border-r border-border bg-sidebar">
      <div className="flex items-center gap-3 border-b border-border px-5 py-5">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 shadow-lg shadow-indigo-500/30">
          <Train className="h-6 w-6 text-white" />
        </div>
        <div>
          <div className="text-lg font-bold leading-tight">
            RailMind <span className="text-[#22c55e]">AI</span>
          </div>
          <div className="text-[10px] text-muted-foreground">
            AI-Powered Railway Safety System
          </div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground data-[status=active]:bg-primary data-[status=active]:text-primary-foreground data-[status=active]:shadow-lg data-[status=active]:shadow-primary/20"
            activeProps={{ "data-status": "active" } as never}
          >
            <Icon className="h-5 w-5" />
            {label}
          </Link>
        ))}
      </nav>
      <div className="m-3 rounded-xl border border-border bg-card p-4">
        <div className="text-xs font-semibold text-muted-foreground">System Status</div>
        <div className="mt-2 flex items-center gap-2 text-sm">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#22c55e] opacity-60" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#22c55e]" />
          </span>
          <span className="text-[#22c55e]">All Systems Operational</span>
        </div>
      </div>
    </aside>
  );
}