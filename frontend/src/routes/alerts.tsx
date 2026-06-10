import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { RiskBadge, ScorePill } from "@/components/RiskBadge";
import {
  AlertTriangle, AlertOctagon, UserCheck, Inbox, Search, Filter,
  X, MoreVertical, CheckCircle, MapPin, Clock, ChevronLeft, ChevronRight, Play, Volume2, Maximize2,
} from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { getAlerts, acknowledgeAlert, resolveAlert, assignAlert, type ApiAlert } from "@/lib/api/alerts";
import { toast } from "sonner";
import { riskColor, type Alert, type AlertStatus } from "@/lib/mock-data";

export const Route = createFileRoute("/alerts")({
  head: () => ({ meta: [{ title: "Alerts — RailMind AI" }] }),
  component: AlertsPage,
});

type TabId = "all" | "high" | "medium" | "low" | "resolved";

function AlertsPage() {
  const [feed, setFeed] = useState("all");
  const [tab, setTab] = useState<TabId>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<ApiAlert[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [filterRisk, setFilterRisk] = useState<'any' | 'high' | 'medium' | 'low'>('any');
  const [filterStatus, setFilterStatus] = useState<'any' | AlertStatus>('any');
  const [filterPlatform, setFilterPlatform] = useState<string>('any');

  const queryClient = useQueryClient();
  const { data, isLoading, isError, error } = useQuery<ApiAlert[]>({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    staleTime: 1000 * 60,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (backendId: number) => acknowledgeAlert(backendId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const resolveMutation = useMutation({
    mutationFn: (backendId: number) => resolveAlert(backendId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  useEffect(() => {
    if (data) {
      setAlerts(data);
    }
  }, [data]);

  const selected = selectedId ? alerts.find((a) => a.id === selectedId) ?? null : null;

  const setStatus = (id: string, status: AlertStatus) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
  };

  const handleAcknowledge = async () => {
    if (!selected) return;
    setStatus(selected.id, "acknowledged");
    await acknowledgeMutation.mutateAsync(selected.backendId);
  };

  const handleResolve = async () => {
    if (!selected) return;
    setStatus(selected.id, "resolved");
    await resolveMutation.mutateAsync(selected.backendId);
  };

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
        Unable to load alerts. {error instanceof Error ? error.message : "Check backend connection."}
      </div>
    );
  }

  const cctvFiltered = feed === "all" ? alerts : alerts.filter((a) => a.cctv === feed);

  const platformOptions = useMemo(() => {
    const setp = new Set<string>();
    alerts.forEach((a) => setp.add(a.platform));
    return Array.from(setp).sort();
  }, [alerts]);

  const counts = {
    all: cctvFiltered.length,
    high: cctvFiltered.filter((a) => a.riskLevel === "high").length,
    medium: cctvFiltered.filter((a) => a.riskLevel === "medium" || a.riskLevel === "suspicious").length,
    low: cctvFiltered.filter((a) => a.riskLevel === "low" && a.status !== "resolved").length,
    resolved: cctvFiltered.filter((a) => a.status === "resolved").length,
  };

  const tabFiltered = useMemo(() => {
    switch (tab) {
      case "high": return cctvFiltered.filter((a) => a.riskLevel === "high");
      case "medium": return cctvFiltered.filter((a) => a.riskLevel === "medium" || a.riskLevel === "suspicious");
      case "low": return cctvFiltered.filter((a) => a.riskLevel === "low" && a.status !== "resolved");
      case "resolved": return cctvFiltered.filter((a) => a.status === "resolved");
      default: return cctvFiltered;
    }
  }, [tab, cctvFiltered]);

  const panelFiltered = useMemo(() => {
    let list = tabFiltered;
    if (filterRisk !== 'any') {
      list = list.filter((a) => a.riskLevel === filterRisk);
    }
    if (filterStatus !== 'any') {
      list = list.filter((a) => a.status === filterStatus);
    }
    if (filterPlatform !== 'any') {
      list = list.filter((a) => a.platform === filterPlatform);
    }
    return list;
  }, [tabFiltered, filterRisk, filterStatus, filterPlatform]);

  const searched = search
    ? panelFiltered.filter((a) =>
        [a.id, a.type, a.platform, a.cctv].some((v) => v.toLowerCase().includes(search.toLowerCase())),
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
      />
      <div className="space-y-5 p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-5">
          <StatCard label="Total Alerts" value={counts.all} change={18} dir="up" icon={AlertOctagon} iconColor="#ef4444" iconBg="rgba(239,68,68,0.15)" />
          <StatCard label="High Risk" value={counts.high} change={33} dir="up" icon={AlertTriangle} iconColor="#ef4444" iconBg="rgba(239,68,68,0.15)" />
          <StatCard label="Medium Risk" value={counts.medium} change={8} dir="up" icon={UserCheck} iconColor="#f97316" iconBg="rgba(249,115,22,0.15)" />
          <StatCard label="Low Risk" value={counts.low} change={12} dir="down" icon={UserCheck} iconColor="#22c55e" iconBg="rgba(34,197,94,0.15)" />
          <StatCard label="Resolved" value={counts.resolved} change={25} dir="up" icon={Inbox} iconColor="#3b82f6" iconBg="rgba(59,130,246,0.15)" />
        </div>

        <div className={selected ? "grid gap-5 xl:grid-cols-[1fr_360px]" : ""}>
          <div className="rounded-xl border border-border bg-card">
            {/* Tabs + search */}
            <div className="flex flex-wrap items-center gap-3 border-b border-border p-4">
              <div className="flex flex-wrap items-center gap-1">
                {([
                  ["all", "All Alerts", counts.all],
                  ["high", "High Risk", counts.high],
                  ["medium", "Medium Risk", counts.medium],
                  ["low", "Low Risk", counts.low],
                  ["resolved", "Resolved", counts.resolved],
                ] as const).map(([id, label, n]) => {
                  const active = tab === id;
                  return (
                    <button
                      key={id}
                      onClick={() => { setTab(id); setPage(1); }}
                      className={`relative px-3 py-2 text-sm transition-colors ${active ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}
                    >
                      {label} ({n})
                      {active && <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-primary" />}
                    </button>
                  );
                })}
              </div>
              <div className="ml-auto flex items-center gap-2">
                <div className="flex items-center gap-2 rounded-lg border border-border bg-secondary px-3 py-1.5">
                  <Search className="h-4 w-4 text-muted-foreground" />
                  <input
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                    placeholder="Search alerts..."
                    className="w-48 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setShowFilters((s) => !s)}
                  className={`flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm ${showFilters ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
                >
                  <Filter className="h-4 w-4" /> Filters
                </button>
              </div>
            </div>

            {showFilters && (
              <div className="border-b border-border p-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="w-40">
                    <label className="block text-xs text-muted-foreground">Risk Level</label>
                    <select value={filterRisk} onChange={(e) => { setFilterRisk(e.target.value as any); setPage(1); }} className="mt-1 w-full rounded-md border border-border bg-secondary px-2 py-1 text-sm">
                      <option value="any">Any</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>

                  <div className="w-40">
                    <label className="block text-xs text-muted-foreground">Status</label>
                    <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value as any); setPage(1); }} className="mt-1 w-full rounded-md border border-border bg-secondary px-2 py-1 text-sm">
                      <option value="any">Any</option>
                      <option value="active">Active</option>
                      <option value="acknowledged">Acknowledged</option>
                      <option value="resolved">Resolved</option>
                    </select>
                  </div>

                  <div className="w-44">
                    <label className="block text-xs text-muted-foreground">Platform</label>
                    <select value={filterPlatform} onChange={(e) => { setFilterPlatform(e.target.value); setPage(1); }} className="mt-1 w-full rounded-md border border-border bg-secondary px-2 py-1 text-sm">
                      <option value="any">Any</option>
                      {platformOptions.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>

                  <div className="ml-auto flex items-center gap-2">
                    <button type="button" onClick={() => { setFilterRisk('any'); setFilterStatus('any'); setFilterPlatform('any'); setPage(1); }} className="rounded-md border border-border bg-secondary px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground">Clear Filters</button>
                  </div>
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
                        className="border-t border-border transition-colors hover:bg-secondary/40"
                        style={{ backgroundColor: a.status === "resolved" ? "transparent" : `${c}08` }}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4" style={{ color: c }} />
                            <span className="font-medium">{a.id}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{a.cctv}</td>
                        <td className="px-4 py-3 text-muted-foreground">{a.platform}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1.5">
                            <span className="inline-flex h-4 w-4 items-center justify-center rounded-full" style={{ backgroundColor: `${c}33`, color: c }}>•</span>
                            {a.type}
                          </span>
                        </td>
                        <td className="px-4 py-3"><ScorePill score={a.riskScore} level={a.riskLevel} /></td>
                        <td className="px-4 py-3 text-muted-foreground">
                          <div className="tabular-nums">{a.time}</div>
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
                            <button className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground">
                              <MoreVertical className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {paged.length === 0 && (
                    <tr><td colSpan={8} className="px-4 py-10 text-center text-sm text-muted-foreground">No alerts match your filters.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-border p-4 text-xs text-muted-foreground">
              <span>
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, searched.length)} of {searched.length} alerts
              </span>
              <div className="flex items-center gap-1">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="rounded-md border border-border bg-secondary p-1.5 disabled:opacity-40">
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                {Array.from({ length: totalPages }).map((_, i) => {
                  const n = i + 1;
                  const active = n === page;
                  return (
                    <button
                      key={n}
                      onClick={() => setPage(n)}
                      className={`min-w-[28px] rounded-md px-2 py-1 ${active ? "bg-primary text-primary-foreground" : "border border-border bg-secondary hover:text-foreground"}`}
                    >
                      {n}
                    </button>
                  );
                })}
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="rounded-md border border-border bg-secondary p-1.5 disabled:opacity-40">
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
    active: { c: "#ef4444", label: "Active" },
    acknowledged: { c: "#f97316", label: "Acknowledged" },
    resolved: { c: "#22c55e", label: "Resolved" },
  } as const;
  const m = map[status];
  return (
    <span className="inline-flex rounded-md px-2 py-0.5 text-[11px] font-semibold"
      style={{ backgroundColor: `${m.c}1f`, color: m.c, border: `1px solid ${m.c}40` }}>
      {m.label}
    </span>
  );
}

function AlertDetails({
  alert, onClose, onAcknowledge, onResolve,
}: { alert: ApiAlert; onClose: () => void; onAcknowledge: () => void; onResolve: () => void; }) {
  const c = riskColor(alert.riskLevel);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [isFullscreenOpen, setIsFullscreenOpen] = useState(false);
  const [assignee, setAssignee] = useState<string>('Not Assigned');
  const queryClient = useQueryClient();
  const videoUrl = (alert as any).video || (alert as any).videoUrl || null;

  const assignMutation = useMutation({
    mutationFn: (name: string) => assignAlert(alert.backendId, name),
    onSuccess: () => {
      toast.success('Assignment saved');
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
  return (
    <aside className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border p-4">
        <h3 className="text-sm font-semibold">Alert Details</h3>
        <button onClick={onClose} className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="space-y-4 p-4">
        <RiskBadge level={alert.riskLevel} />
        <h2 className="text-lg font-bold">{alert.type}</h2>
        <div className="space-y-1 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" /> {alert.cctv} | {alert.platform}</div>
          <div className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" /> {alert.time}, {alert.date}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Risk Score</div>
          <div className="text-3xl font-bold" style={{ color: c }}>{alert.riskScore}%</div>
        </div>
        <div className="relative overflow-hidden rounded-lg bg-black">
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
              <img src={alert.image} alt="Snapshot" className="aspect-video w-full object-cover" loading="lazy" />
              <div className="absolute left-2 top-2 rounded bg-black/60 px-2 py-1 text-xs font-medium text-white">Snapshot</div>
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
              title={videoUrl ? (isPlaying ? 'Pause' : 'Play') : 'No video available'}
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
              className={`rounded p-1 hover:bg-secondary hover:text-foreground ${!videoUrl ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={videoUrl ? (isMuted ? 'Unmute' : 'Mute') : 'No video available'}
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
            <div className="w-full">
              {videoUrl ? (
                <video src={videoUrl} controls autoPlay className="w-full max-h-[90vh] bg-black" />
              ) : (
                <img src={alert.image} alt="Snapshot fullscreen" className="w-full object-contain max-h-[90vh]" />
              )}
            </div>
          </DialogContent>
        </Dialog>
        <DetailRow label="Event Type"><span className="font-semibold" style={{ color: c }}>{alert.type}</span></DetailRow>
        <DetailRow label="Description"><p className="text-right text-xs text-muted-foreground">{alert.description}</p></DetailRow>
        <DetailRow label="Status"><StatusPill status={alert.status} /></DetailRow>
        <DetailRow label="Assigned To">
          <select
            value={assignee}
            onChange={(e) => {
              const name = e.target.value;
              setAssignee(name);
              if (name) {
                assignMutation.mutate(name);
              }
            }}
            disabled={assignMutation.isLoading}
            className="rounded-md border border-border bg-secondary px-2 py-1 text-xs"
          >
            <option value="Not Assigned">Not Assigned</option>
            <option value="Officer A. Khan">Officer A. Khan</option>
            <option value="Officer R. Mehta">Officer R. Mehta</option>
          </select>
        </DetailRow>
        <div className="flex gap-2 pt-2">
          <button onClick={onAcknowledge} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
            <CheckCircle className="h-4 w-4" /> Acknowledge
          </button>
          <button onClick={onResolve} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-sm font-semibold hover:bg-secondary/70">
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