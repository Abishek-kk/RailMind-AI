import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { RiskBadge, ScorePill } from "@/components/RiskBadge";
import {
  AlertTriangle,
  AlertOctagon,
  UserCheck,
  Inbox,
  Search,
  Filter,
  X,
  CheckCircle,
  MapPin,
  Clock,
  ChevronLeft,
  ChevronRight,
  Play,
  Volume2,
  Maximize2,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import {
  getAlerts,
  acknowledgeAlert,
  resolveAlert,
  assignAlert,
  type ApiAlert,
} from "@/lib/api/alerts";
import { getFeeds } from "@/lib/api/feeds";
import { toast } from "sonner";
import { riskColor, type Alert, type AlertStatus } from "@/lib/mock-data";

// Route exported in alerts.tsx

type TabId = "all" | "high" | "medium" | "low" | "resolved";

function getPaginationRange(current: number, total: number): (number | "ellipsis")[] {
  if (total <= 1) return [1];

  const delta = 1;
  const range: (number | "ellipsis")[] = [];
  const left = Math.max(2, current - delta);
  const right = Math.min(total - 1, current + delta);

  range.push(1);
  if (left > 2) range.push("ellipsis");
  for (let i = left; i <= right; i++) range.push(i);
  if (right < total - 1) range.push("ellipsis");
  if (total > 1) range.push(total);

  return range;
}

export default function AlertsPage() {
  const [feed, setFeed] = useState("all");
  const [tab, setTab] = useState<TabId>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<ApiAlert[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [filterRisk, setFilterRisk] = useState<"any" | "high" | "medium" | "low">("any");
  const [filterStatus, setFilterStatus] = useState<"any" | AlertStatus>("any");
  const [filterPlatform, setFilterPlatform] = useState<string>("any");

  useEffect(() => {
    setPage(1);
  }, [tab, search, filterRisk, filterStatus, filterPlatform, feed]);

  const queryClient = useQueryClient();
  const { data, isLoading, isError, error } = useQuery<ApiAlert[]>({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    staleTime: 1000 * 60,
  });

  const { data: feedsData } = useQuery({
    queryKey: ["liveFeeds"],
    queryFn: getFeeds,
    staleTime: 1000 * 60,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: ({ backendId, operatorId }: { backendId: number; operatorId?: string | null }) =>
      acknowledgeAlert(backendId, operatorId),
    onError: (error: Error) => {
      toast.error(error.message || "Failed to acknowledge alert. Please try again.");
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const resolveMutation = useMutation({
    mutationFn: (backendId: number) => resolveAlert(backendId),
    onError: (error: Error) => {
      toast.error(error.message || "Failed to resolve alert. Please try again.");
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  useEffect(() => {
    if (data) {
      setAlerts(data);
    }
  }, [data]);

  const selected = selectedId ? (alerts.find((a) => a.id === selectedId) ?? null) : null;

  const setStatus = (id: string, status: AlertStatus) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
  };

  const handleAcknowledge = async (operatorId?: string | null) => {
    if (!selected) return;
    const previousStatus = selected.status;
    setStatus(selected.id, "acknowledged");

    try {
      await acknowledgeMutation.mutateAsync({ backendId: selected.backendId, operatorId });
      toast.success("Alert acknowledged successfully.");
    } catch (error) {
      setStatus(selected.id, previousStatus);
      toast.error(
        error instanceof Error
          ? `Failed to acknowledge alert: ${error.message}`
          : "Failed to acknowledge alert.",
      );
    }
  };

  const handleResolve = async () => {
    if (!selected) return;
    const previousStatus = selected.status;
    setStatus(selected.id, "resolved");

    try {
      await resolveMutation.mutateAsync(selected.backendId);
      toast.success("Alert resolved successfully.");
    } catch (error) {
      setStatus(selected.id, previousStatus);
      toast.error(
        error instanceof Error
          ? `Failed to resolve alert: ${error.message}`
          : "Failed to resolve alert.",
      );
    }
  };

  // BUG 4 FIX: move all useMemo hooks before early returns to comply with rules of hooks
  const cctvFiltered = feed === "all" ? alerts : alerts.filter((a) => a.cctv === feed);

  const dynamicFeeds = useMemo(() => {
    if (!Array.isArray(feedsData) || feedsData.length === 0) return undefined;
    return feedsData.map((f) => ({ id: f.id, label: `${f.id} (${f.platform})` }));
  }, [feedsData]);

  const platformOptions = useMemo(() => {
    const setp = new Set<string>();
    alerts.forEach((a) => setp.add(a.platform));
    return Array.from(setp).sort();
  }, [alerts]);

  const counts = {
    all: cctvFiltered.length,
    high: cctvFiltered.filter((a) => a.riskLevel === "high").length,
    medium: cctvFiltered.filter((a) => a.riskLevel === "medium" || a.riskLevel === "suspicious")
      .length,
    low: cctvFiltered.filter((a) => a.riskLevel === "low" && a.status !== "resolved").length,
    resolved: cctvFiltered.filter((a) => a.status === "resolved").length,
  };

  const tabFiltered = useMemo(() => {
    switch (tab) {
      case "high":
        return cctvFiltered.filter((a) => a.riskLevel === "high");
      case "medium":
        return cctvFiltered.filter((a) => a.riskLevel === "medium" || a.riskLevel === "suspicious");
      case "low":
        return cctvFiltered.filter((a) => a.riskLevel === "low" && a.status !== "resolved");
      case "resolved":
        return cctvFiltered.filter((a) => a.status === "resolved");
      default:
        return cctvFiltered;
    }
  }, [tab, cctvFiltered]);

  const panelFiltered = useMemo(() => {
    let list = tabFiltered;
    if (filterRisk !== "any") {
      list = list.filter((a) => a.riskLevel === filterRisk);
    }
    if (filterStatus !== "any") {
      list = list.filter((a) => a.status === filterStatus);
    }
    if (filterPlatform !== "any") {
      list = list.filter((a) => a.platform === filterPlatform);
    }
    return list;
  }, [tabFiltered, filterRisk, filterStatus, filterPlatform]);

  if (isLoading) {
    return (
      <div className="p-6 text-center text-sm text-muted-foreground">
        Loading alerts from backend...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 text-center text-sm text-destructive">
        Unable to load alerts.{" "}
        {error instanceof Error ? error.message : "Check backend connection."}
      </div>
    );
  }

  const searched = search
    ? panelFiltered.filter((a) =>
        [a.id, a.type, a.platform, a.cctv].some((v) =>
          v.toLowerCase().includes(search.toLowerCase()),
        ),
      )
    : panelFiltered;

  const pageSize = 8;
  const totalPages = Math.max(1, Math.ceil(searched.length / pageSize));
  const paged = searched.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div>
      <TopBar
        title="Alerts"
        subtitle="Manage and respond to all detected incidents"
        selectedFeed={feed}
        onFeedChange={setFeed}
        feeds={dynamicFeeds}
      />
      <div className="space-y-5 p-6">
        {/* BUG 14 FIX: removed hardcoded change/dir props from all StatCards */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-5">
          <StatCard
            label="Total Alerts"
            value={counts.all}
            icon={AlertOctagon}
            iconColor="#ef4444"
            iconBg="rgba(239,68,68,0.15)"
          />
          <StatCard
            label="High Risk"
            value={counts.high}
            icon={AlertTriangle}
            iconColor="#ef4444"
            iconBg="rgba(239,68,68,0.15)"
          />
          <StatCard
            label="Medium Risk"
            value={counts.medium}
            icon={UserCheck}
            iconColor="#f97316"
            iconBg="rgba(249,115,22,0.15)"
          />
          <StatCard
            label="Low Risk"
            value={counts.low}
            icon={UserCheck}
            iconColor="#22c55e"
            iconBg="rgba(34,197,94,0.15)"
          />
          <StatCard
            label="Resolved"
            value={counts.resolved}
            icon={Inbox}
            iconColor="#3b82f6"
            iconBg="rgba(59,130,246,0.15)"
          />
        </div>

        <div className={selected ? "grid gap-5 xl:grid-cols-[1fr_360px]" : ""}>
          <div className="hud-panel rounded-xl bg-card">
            {/* Top accent line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
            {/* Tabs + search */}
            <div className="flex flex-wrap items-center gap-3 border-b border-border p-4">
              <div className="flex flex-wrap items-center gap-1">
                {(
                  [
                    ["all", "All Alerts", counts.all],
                    ["high", "High Risk", counts.high],
                    ["medium", "Medium Risk", counts.medium],
                    ["low", "Low Risk", counts.low],
                    ["resolved", "Resolved", counts.resolved],
                  ] as const
                ).map(([id, label, n]) => {
                  const active = tab === id;
                  return (
                    <button
                      key={id}
                      onClick={() => {
                        setTab(id);
                      }}
                      className={`relative px-3 py-2 text-sm transition-colors ${active ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      {label} ({n})
                      {active && (
                        <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-primary" />
                      )}
                    </button>
                  );
                })}
              </div>
              <div className="ml-auto flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                    }}
                    placeholder="Search alerts"
                    className="h-9 w-56 rounded-md border border-border bg-secondary pl-8 pr-8 text-sm outline-none transition focus:border-primary"
                  />
                  {search && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearch("");
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:text-foreground"
                      title="Clear search"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setShowFilters((value) => !value)}
                  className={`inline-flex h-9 items-center gap-2 rounded-md border px-3 text-sm transition ${
                    showFilters
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Filter className="h-4 w-4" />
                  Filters
                </button>
              </div>
            </div>

            {showFilters && (
              <div className="border-b border-[#1a2432]/90 bg-[#0b0e14]/75 backdrop-blur-md p-4">
                <div className="flex flex-wrap items-end gap-4">
                  <div className="w-40">
                    <label className="block text-xs text-muted-foreground">Risk</label>
                    <select
                      value={filterRisk}
                      onChange={(e) => {
                        setFilterRisk(e.target.value as typeof filterRisk);
                      }}
                      className="mt-1 w-full rounded-md border border-[#1a2432] bg-[#0b0e14]/50 px-2 py-1.5 text-sm"
                    >
                      <option value="any">Any</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>
                  <div className="w-40">
                    <label className="block text-xs text-muted-foreground">Status</label>
                    <select
                      value={filterStatus}
                      onChange={(e) => {
                        setFilterStatus(e.target.value as typeof filterStatus);
                      }}
                      className="mt-1 w-full rounded-md border border-[#1a2432] bg-[#0b0e14]/50 px-2 py-1.5 text-sm"
                    >
                      <option value="any">Any</option>
                      <option value="active">Active</option>
                      <option value="acknowledged">Acknowledged</option>
                      <option value="resolved">Resolved</option>
                    </select>
                  </div>
                  <div className="w-52">
                    <label className="block text-xs text-muted-foreground">Platform</label>
                    <select
                      value={filterPlatform}
                      onChange={(e) => {
                        setFilterPlatform(e.target.value);
                      }}
                      className="mt-1 w-full rounded-md border border-[#1a2432] bg-[#0b0e14]/50 px-2 py-1.5 text-sm"
                    >
                      <option value="any">Any</option>
                      {platformOptions.map((p) => (
                        <option key={p} value={p}>
                          {p}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setFilterRisk("any");
                      setFilterStatus("any");
                      setFilterPlatform("any");
                    }}
                    className="rounded-md border border-border bg-secondary px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-muted-foreground">
                    <th className="px-4 py-3 font-medium">Alert ID</th>
                    <th className="px-4 py-3 font-medium">CCTV Feed</th>
                    <th className="px-4 py-3 font-medium">Platform</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">Risk Score</th>
                    <th className="px-4 py-3 font-medium">Time</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((a) => {
                    const c = riskColor(a.riskLevel);
                    return (
                      <tr
                        key={a.id}
                        className="group border-t border-border transition-colors hover:bg-secondary/40 relative"
                        style={{
                          backgroundColor: a.status === "resolved" ? "transparent" : `${c}08`,
                        }}
                      >
                        <td className="relative px-4 py-3">
                          {/* Row hover left glow bar */}
                          <div
                            className="absolute left-0 top-0 bottom-0 w-[3px] opacity-0 group-hover:opacity-100 transition-all duration-300"
                            style={{
                              backgroundColor: c,
                              boxShadow: `0 0 10px ${c}`,
                            }}
                          />
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4" style={{ color: c }} />
                            <span className="font-medium font-mono">{a.id}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground font-mono">{a.cctv}</td>
                        <td className="px-4 py-3 text-muted-foreground">{a.platform}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1.5">
                            <span
                              className="inline-flex h-4 w-4 items-center justify-center rounded-full animate-pulse"
                              style={{ backgroundColor: `${c}33`, color: c }}
                            >
                              •
                            </span>
                            {a.type}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <ScorePill score={a.riskScore} level={a.riskLevel} />
                        </td>
                        <td className="px-4 py-3 text-muted-foreground font-mono">
                          <div>{a.time}</div>
                          <div className="text-[11px]">{a.date}</div>
                        </td>
                        <td className="px-4 py-3">
                          <StatusPill status={a.status} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => setSelectedId(a.id)}
                              className="rounded-md border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-medium text-primary hover:bg-primary/20"
                            >
                              View
                            </button>
                            {/* BUG 9 FIX: DropdownMenu replacing dead MoreVertical button */}
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <button
                                  className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
                                  aria-label="More actions"
                                >
                                  {/* Using SVG inline to avoid extra import complexity */}
                                  <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  >
                                    <circle cx="12" cy="5" r="1" />
                                    <circle cx="12" cy="12" r="1" />
                                    <circle cx="12" cy="19" r="1" />
                                  </svg>
                                </button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-44">
                                <DropdownMenuItem onClick={() => setSelectedId(a.id)}>
                                  View Details
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                {/* Only show Acknowledge if status is active */}
                                {a.status === "active" && (
                                  <DropdownMenuItem
                                    onClick={() => {
                                      setStatus(a.id, "acknowledged");
                                      acknowledgeMutation.mutate({
                                        backendId: a.backendId,
                                        operatorId: a.operator_assigned,
                                      });
                                    }}
                                  >
                                    Acknowledge
                                  </DropdownMenuItem>
                                )}
                                {/* Only show Resolve if status is not resolved */}
                                {a.status !== "resolved" && (
                                  <DropdownMenuItem
                                    onClick={() => {
                                      setStatus(a.id, "resolved");
                                      resolveMutation.mutate(a.backendId);
                                    }}
                                  >
                                    Mark Resolved
                                  </DropdownMenuItem>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {paged.length === 0 && (
                    <tr>
                      <td
                        colSpan={8}
                        className="px-4 py-10 text-center text-sm text-muted-foreground"
                      >
                        No alerts match your filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex flex-wrap items-center justify-between gap-y-2 overflow-hidden border-t border-border p-4 text-xs text-muted-foreground">
              <span>
                {searched.length === 0
                  ? "No results"
                  : `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, searched.length)} of ${searched.length} alerts`}
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-md border border-border bg-secondary p-1.5 disabled:opacity-40"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                {getPaginationRange(page, totalPages).map((entry, idx) =>
                  entry === "ellipsis" ? (
                    <span key={`ellipsis-${idx}`} className="px-1.5 text-muted-foreground">
                      …
                    </span>
                  ) : (
                    <button
                      key={entry}
                      onClick={() => setPage(entry)}
                      className={`min-w-[28px] rounded-md px-2 py-1 ${
                        entry === page
                          ? "bg-primary text-primary-foreground"
                          : "border border-border bg-secondary hover:text-foreground"
                      }`}
                    >
                      {entry}
                    </button>
                  ),
                )}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="rounded-md border border-border bg-secondary p-1.5 disabled:opacity-40"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>

          {selected && (
            <AlertDetails
              alert={selected}
              onClose={() => setSelectedId(null)}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: AlertStatus }) {
  const map = {
    active: { c: "#ff2d55", label: "Active", glow: "0 0 10px rgba(255, 45, 85, 0.45)" },
    acknowledged: { c: "#ff9f0a", label: "Acknowledged", glow: "0 0 8px rgba(255, 159, 10, 0.4)" },
    resolved: { c: "#00e676", label: "Resolved", glow: "0 0 4px rgba(0, 230, 118, 0.15)" },
  } as const;
  const m = map[status];
  return (
    <span
      className="inline-flex rounded-md px-2 py-0.5 text-[11px] font-semibold font-mono tracking-wider"
      style={{
        backgroundColor: `${m.c}1f`,
        color: m.c,
        border: `1px solid ${m.c}40`,
        boxShadow: m.glow,
      }}
    >
      {m.label.toUpperCase()}
    </span>
  );
}

function AlertDetails({
  alert,
  onClose,
  onAcknowledge,
  onResolve,
}: {
  alert: ApiAlert;
  onClose: () => void;
  onAcknowledge: (operatorId?: string | null) => void;
  onResolve: () => void;
}) {
  const c = riskColor(alert.riskLevel);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [isFullscreenOpen, setIsFullscreenOpen] = useState(false);
  /**
   * BUG 10 FIX: initialize assignee from alert.operator_assigned instead of
   * hardcoding "Not Assigned" regardless of the alert's actual state.
   */
  const [assignee, setAssignee] = useState<string>(alert.operator_assigned || "Not Assigned");
  const queryClient = useQueryClient();
  const videoUrl = alert.videoUrl || null;

  /** BUG 10 FIX: reset assignee when the displayed alert changes */
  useEffect(() => {
    setAssignee(alert.operator_assigned || "Not Assigned");
  }, [alert.backendId, alert.operator_assigned]);

  const assignMutation = useMutation({
    mutationFn: (name: string) => assignAlert(alert.backendId, name),
    onSuccess: () => {
      toast.success("Assignment saved");
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to save assignment. Please try again.");
      // Roll back the dropdown to the actual saved value so the UI stays consistent.
      setAssignee(alert.operator_assigned || "Not Assigned");
    },
  });
  return (
    <aside className="hud-panel rounded-xl bg-card">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
      <div className="flex items-center justify-between border-b border-border p-4">
        <h3 className="text-sm font-semibold">Alert Details</h3>
        <button
          onClick={onClose}
          className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="space-y-4 p-4">
        <div className="flex items-center gap-2">
          <RiskBadge level={alert.riskLevel} />
          {alert.reasoning_mode === "llm" && (
            <span
              className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wide"
              style={{
                backgroundColor: "rgba(0, 229, 255, 0.15)",
                color: "#00e5ff",
                border: "1px solid rgba(0, 229, 255, 0.4)",
              }}
            >
              AI-Reasoned
            </span>
          )}
          {alert.reasoning_mode === "rule_based" && (
            <span
              className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wide"
              style={{
                backgroundColor: "rgba(148,163,184,0.15)",
                color: "#94a3b8",
                border: "1px solid rgba(148,163,184,0.4)",
              }}
            >
              Rule-Based
            </span>
          )}
        </div>
        <h2 className="text-lg font-bold">{alert.type}</h2>
        <div className="space-y-1 text-xs text-muted-foreground font-mono">
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5" /> {alert.cctv} | {alert.platform}
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" /> {alert.time}, {alert.date}
          </div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Risk Score</div>
          <div className="text-3xl font-bold font-mono" style={{ color: c }}>
            {alert.riskScore}%
          </div>
        </div>
        <div className="hud-brackets relative overflow-hidden rounded-lg bg-black">
          {videoUrl ? (
            <video
              ref={videoRef}
              src={videoUrl}
              poster={alert.image}
              className="aspect-video w-full object-cover bg-black"
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              muted={isMuted}
              controls={false}
            />
          ) : (
            <>
              <img
                src={alert.image}
                alt="Snapshot"
                className="aspect-video w-full object-cover"
                loading="lazy"
              />
              <div className="absolute left-2 top-2 rounded bg-black/60 px-2 py-1 text-xs font-medium text-white font-mono">
                Snapshot
              </div>
            </>
          )}
        </div>
        <div className="flex items-center justify-between text-muted-foreground">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (!videoRef.current) return;
                if (videoRef.current.paused) {
                  videoRef.current.play().catch(() => {});
                } else {
                  videoRef.current.pause();
                }
              }}
              className="rounded p-1 hover:bg-secondary hover:text-foreground"
              aria-pressed={isPlaying}
              title={videoUrl ? (isPlaying ? "Pause" : "Play") : "No video available"}
            >
              <Play className="h-4 w-4" />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (!videoRef.current) return;
                videoRef.current.muted = !videoRef.current.muted;
                setIsMuted(videoRef.current.muted);
              }}
              className={`rounded p-1 hover:bg-secondary hover:text-foreground ${!videoUrl ? "opacity-50 cursor-not-allowed" : ""}`}
              title={videoUrl ? (isMuted ? "Unmute" : "Mute") : "No video available"}
            >
              <Volume2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setIsFullscreenOpen(true)}
              className="rounded p-1 hover:bg-secondary hover:text-foreground"
              title="Open fullscreen"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        <Dialog open={isFullscreenOpen} onOpenChange={setIsFullscreenOpen}>
          <DialogContent>
            <DialogTitle className="sr-only">{`${alert.type} — ${alert.cctv}`}</DialogTitle>
            <DialogDescription className="sr-only">
              Fullscreen video view for {alert.type} at {alert.cctv}.
            </DialogDescription>
            <div className="w-full">
              {videoUrl ? (
                <video src={videoUrl} controls autoPlay className="w-full max-h-[90vh] bg-black" />
              ) : (
                <img
                  src={alert.image}
                  alt="Snapshot fullscreen"
                  className="w-full object-contain max-h-[90vh]"
                />
              )}
            </div>
          </DialogContent>
        </Dialog>
        <DetailRow label="Event Type">
          <span className="font-semibold" style={{ color: c }}>
            {alert.type}
          </span>
        </DetailRow>
        <DetailRow label="Description">
          <p className="text-right text-xs text-muted-foreground">{alert.description}</p>
        </DetailRow>
        <DetailRow label="Status">
          <StatusPill status={alert.status} />
        </DetailRow>
        <DetailRow label="Assigned To">
          <select
            value={assignee}
            onChange={(e) => {
              const name = e.target.value;
              setAssignee(name);
              assignMutation.mutate(name === "Not Assigned" ? "" : name);
            }}
            disabled={assignMutation.isPending}
            className="rounded-md border border-[#1a2432] bg-[#0b0e14]/50 px-2 py-1 text-xs"
          >
            <option value="Not Assigned">Not Assigned</option>
            <option value="Officer A. Khan">Officer A. Khan</option>
            <option value="Officer R. Mehta">Officer R. Mehta</option>
          </select>
        </DetailRow>
        <div className="flex gap-2 pt-2">
          <button
            onClick={() => onAcknowledge(assignee === "Not Assigned" ? undefined : assignee)}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90 hover:shadow-[var(--glow-primary)]"
          >
            <CheckCircle className="h-4 w-4" /> Acknowledge
          </button>
          <button
            onClick={onResolve}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-sm font-semibold transition-all hover:bg-secondary/70 hover:shadow-lg hover:shadow-secondary/10"
          >
            <CheckCircle className="h-4 w-4" /> Mark Resolved
          </button>
        </div>
      </div>
    </aside>
  );
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 border-t border-border pt-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <div className="text-right">{children}</div>
    </div>
  );
}
