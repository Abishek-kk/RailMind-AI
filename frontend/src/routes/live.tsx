import { createFileRoute, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { CCTVFeedCard } from "@/components/CCTVFeedCard";
import { RiskBadge } from "@/components/RiskBadge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Camera,
  Users,
  AlertTriangle,
  Activity,
  Plus,
  ArrowRight,
  ChevronDown,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { getAlerts, mapBackendAlert, type ApiAlert, type BackendAlert } from "@/lib/api/alerts";
import { createFeed, getFeeds } from "@/lib/api/feeds";
import { useWebSocket } from "@/hooks/useWebSocket";
import { getLiveFeeds, riskColor, type BoundingBox, type RiskLevel } from "@/lib/mock-data";

interface LiveDetectionPayload {
  camera_id: string;
  platform: string;
  dimensions?: {
    width: number;
    height: number;
  };
  timestamp: number;
  detections: Array<{
    track_id: string;
    bbox: [number, number, number, number];
    distance: number;
    risk_score: number;
    risk_level: string;
    incident_type: string;
  }>;
}

/** BUG 4 FIX: id is number to satisfy BoundingBox interface */
type LiveBoundingBox = BoundingBox;

function normalizeTrackId(trackId: string): number {
  const parsed = Number(trackId);
  return Number.isFinite(parsed)
    ? parsed
    : trackId.split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
}

function mapCameraIdToFeedId(cameraId: string) {
  const match = cameraId.match(/CCTV(?:[_-]P?(\d+)|[_-]?(\d+))/i);
  const number = match ? Number(match[1] ?? match[2]) : NaN;
  if (Number.isFinite(number) && number > 0) {
    return `CCTV-${number}`;
  }
  const fallback = cameraId.match(/\d+/);
  return fallback ? `CCTV-${Number(fallback[0])}` : cameraId;
}

export const Route = createFileRoute("/live")({
  head: () => ({ meta: [{ title: "Live Monitoring — RailMind AI" }] }),
  component: LivePage,
});

/** BUG 1 FIX: source_url instead of url */
interface CreateFeedRequest {
  id: string;
  name: string;
  source_url: string;
}

type FilterLevel = "all" | "high" | "medium" | "low";

function LivePage() {
  const [feed, setFeed] = useState("all");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [cameraId, setCameraId] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");
  const [platformName, setPlatformName] = useState("");
  /** BUG 6 FIX: filter level state for Live Detections sidebar */
  const [filterLevel, setFilterLevel] = useState<FilterLevel>("all");
  const [filterDropdownOpen, setFilterDropdownOpen] = useState(false);
  /** BUG 15 FIX: allow user to dismiss mock-data banner */
  const [mockBannerDismissed, setMockBannerDismissed] = useState(false);

  const queryClient = useQueryClient();

  const {
    data: feeds,
    isLoading: feedsLoading,
    error: feedsError,
  } = useQuery({ queryKey: ["liveFeeds"], queryFn: getFeeds });

  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
  } = useQuery({ queryKey: ["liveAlerts"], queryFn: getAlerts, refetchInterval: 30_000 });

  const addFeedMutation = useMutation({
    mutationFn: (payload: CreateFeedRequest) => createFeed(payload),
    onSuccess: () => {
      setIsDialogOpen(false);
      setCameraId("");
      setRtspUrl("");
      setPlatformName("");
      queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
    },
    /** BUG 3 FIX: show error toast on failure; do NOT close dialog */
    onError: () => {
      toast.error("Failed to add feed. Please check the camera ID and URL.");
    },
  });

  const websocketBase = import.meta.env.VITE_WS_URL?.trim() ?? "";
  const websocketUrl = websocketBase
    ? `${websocketBase.replace(/\/+$|\s+$/g, "")}/ws/alerts`
    : "/ws/alerts";
  const {
    data: latestMessage,
    status: wsStatus,
    error: wsError,
    reconnect: reconnectWebSocket,
  } = useWebSocket<Record<string, unknown>>(websocketUrl);
  const [realtimeAlerts, setRealtimeAlerts] = useState<ApiAlert[]>([]);
  const [feedAlerts, setFeedAlerts] = useState<
    Record<string, { alertType: string; riskScore: number; riskLevel: RiskLevel }>
  >({});
  const [feedDetections, setFeedDetections] = useState<Record<string, LiveBoundingBox[]>>({});
  const [feedPeopleCount, setFeedPeopleCount] = useState<Record<string, number>>({});
  const [soundEnabled, setSoundEnabled] = useState(true);
  const shownToastIds = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (wsError) {
      toast.error(`Real-time updates unavailable: ${wsError}`);
    }
  }, [wsError]);

  const playNotificationSound = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const AudioCtx =
        window.AudioContext ||
        (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtx) return;
      const context = new AudioCtx();
      const oscillator = context.createOscillator();
      const gain = context.createGain();

      oscillator.type = "sine";
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0.12, context.currentTime);

      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.14);

      oscillator.onended = () => {
        context.close().catch(() => undefined);
      };
    } catch {
      // Ignore audio failures in unsupported browsers or restricted contexts.
    }
  }, []);

  const showAlertToast = useCallback(
    (alert: ApiAlert) => {
      if (shownToastIds.current.has(alert.backendId)) {
        return;
      }

      shownToastIds.current.add(alert.backendId);
      const message = `${alert.cctv} — ${alert.type} — Risk: ${alert.riskScore}%`;
      const isHighRisk = alert.riskLevel === "high";
      const isMediumRisk = alert.riskLevel === "medium" || alert.riskLevel === "suspicious";
      const icon = (
        <span
          className={`inline-flex h-3.5 w-3.5 rounded-full ${
            isHighRisk ? "bg-red-500" : isMediumRisk ? "bg-orange-500" : "bg-emerald-500"
          }`}
        />
      );

      const options = {
        icon,
        duration: isHighRisk ? Infinity : 5000,
      } as const;

      if (isHighRisk) {
        toast.error(message, options);
      } else if (alert.riskLevel === "low") {
        toast.success(message, options);
      } else {
        toast(message, options);
      }

      if (isHighRisk && soundEnabled) {
        playNotificationSound();
      }
    },
    [playNotificationSound, soundEnabled],
  );

  const isMockData = useMemo(() => {
    return (
      ((Array.isArray(feeds) && feeds.length === 0) || !!feedsError) &&
      import.meta.env.MODE === "development"
    );
  }, [feeds, feedsError]);

  const displayFeeds = useMemo(() => {
    if (feedsError && import.meta.env.MODE === "development") {
      return getLiveFeeds();
    }

    if (!Array.isArray(feeds)) {
      return [];
    }

    return feeds;
  }, [feeds, feedsError]);

  const enrichedDisplayFeeds = useMemo(() => {
    return displayFeeds.map((f) => ({
      ...f,
      peopleDetected: feedPeopleCount[f.id] ?? f.peopleDetected,
      ...(feedAlerts[f.id] ?? {}),
    }));
  }, [displayFeeds, feedPeopleCount, feedAlerts]);

  const filteredFeeds = useMemo(() => {
    const list = enrichedDisplayFeeds;
    return feed === "all" ? list : list.filter((f) => f.id === feed);
  }, [enrichedDisplayFeeds, feed]);

  useEffect(() => {
    if (alerts && alerts.length > 0) {
      setRealtimeAlerts(alerts);
    }
  }, [alerts]);

  const resolveFeedId = useCallback(
    (cameraId: string) => {
      if (Array.isArray(feeds)) {
        const exactMatch = feeds.find((f) => f.id === cameraId);
        if (exactMatch) {
          return cameraId;
        }
        const mapped = mapCameraIdToFeedId(cameraId);
        const mappedMatch = feeds.find((f) => f.id === mapped);
        if (mappedMatch) {
          return mapped;
        }
      }
      return cameraId;
    },
    [feeds],
  );

  useEffect(() => {
    if (!latestMessage) {
      return;
    }

    /**
     * BUG 2 FIX: detect backend alert payloads by checking for fields that
     * only exist on raw BackendAlert objects — NOT by checking for "backendId"
     * which is only added after mapping.
     */
    if ("risk_score" in latestMessage && "incident_type" in latestMessage) {
      const backendAlert = latestMessage as BackendAlert;
      const mappedAlert = mapBackendAlert(backendAlert);
      const feedId = resolveFeedId(backendAlert.camera_id || mappedAlert.cctv);

      setFeedAlerts((current) => ({
        ...current,
        [feedId]: {
          alertType: mappedAlert.type,
          riskScore: mappedAlert.riskScore,
          riskLevel: mappedAlert.riskLevel,
        },
      }));

      setRealtimeAlerts((current) => {
        if (current.some((a) => a.backendId === mappedAlert.backendId)) {
          return current;
        }
        return [mappedAlert, ...current];
      });
      showAlertToast(mappedAlert);
      return;
    }

    if ("camera_id" in latestMessage && Array.isArray(latestMessage.detections)) {
      const latestDetection = latestMessage as LiveDetectionPayload;
      const feedId = resolveFeedId(latestDetection.camera_id);
      const { width, height } = latestDetection.dimensions || {};
      const safeWidth = width || 1;
      const safeHeight = height || 1;
      const boxes: LiveBoundingBox[] = latestDetection.detections.map((detection) => {
        const [x1, y1, x2, y2] = detection.bbox;
        const normalizedLevel = (
          detection.risk_level.toLowerCase().includes("high")
            ? "high"
            : detection.risk_level.toLowerCase().includes("suspicious")
              ? "suspicious"
              : detection.risk_level.toLowerCase().includes("medium")
                ? "medium"
                : "low"
        ) as RiskLevel;

        return {
          id: normalizeTrackId(detection.track_id),
          level: normalizedLevel,
          x: Math.max(0, Math.min(100, (x1 / safeWidth) * 100)),
          y: Math.max(0, Math.min(100, (y1 / safeHeight) * 100)),
          w: Math.max(0, Math.min(100, ((x2 - x1) / safeWidth) * 100)),
          h: Math.max(0, Math.min(100, ((y2 - y1) / safeHeight) * 100)),
        };
      });

      setFeedDetections((current) => ({
        ...current,
        [feedId]: boxes,
      }));
      setFeedPeopleCount((current) => ({
        ...current,
        [feedId]: boxes.length,
      }));
      return;
    }
  }, [latestMessage, showAlertToast, resolveFeedId]);

  const filteredAlerts = useMemo(() => {
    let list = realtimeAlerts;
    if (feed !== "all") {
      list = list.filter((a) => a.cctv === feed);
    }
    if (filterLevel !== "all") {
      list = list.filter((a) => {
        if (filterLevel === "medium") {
          return a.riskLevel === "medium" || a.riskLevel === "suspicious";
        }
        return a.riskLevel === filterLevel;
      });
    }
    return list;
  }, [realtimeAlerts, feed, filterLevel]);

  const totalPeople = filteredFeeds.reduce((s, f) => s + f.peopleDetected, 0);
  const active = filteredAlerts.filter((a) => a.status === "active").length;
  const highRisk = filteredAlerts.filter((a) => a.riskLevel === "high").length;

  /** Build dynamic feeds list for TopBar (BUG 12) */
  const dynamicFeeds = useMemo(() => {
    if (!Array.isArray(enrichedDisplayFeeds) || enrichedDisplayFeeds.length === 0) return undefined;
    return enrichedDisplayFeeds.map((f) => ({ id: f.id, label: `${f.id} (${f.platform})` }));
  }, [enrichedDisplayFeeds]);

  return (
    <div>
      <TopBar
        title="Live Monitoring"
        subtitle="Real-time CCTV Monitoring & Threat Detection"
        selectedFeed={feed}
        onFeedChange={setFeed}
        soundEnabled={soundEnabled}
        onSoundToggle={() => setSoundEnabled((enabled) => !enabled)}
        feeds={dynamicFeeds}
      />
      <div className="p-6">
        {wsError ? (
          <div className="mb-6 rounded-xl border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <div className="flex items-center justify-between gap-3">
              <span>Real-time updates are blocked: {wsError}</span>
              <button
                type="button"
                onClick={reconnectWebSocket}
                className="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-1 text-xs font-semibold text-destructive transition hover:bg-destructive/20"
              >
                Retry
              </button>
            </div>
          </div>
        ) : null}
        {feedsLoading || alertsLoading ? (
          <div className="space-y-4">
            <div className="h-6 w-1/3 rounded bg-muted/30 animate-pulse" />
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="h-24 rounded-xl bg-muted/20 p-4 animate-pulse" />
              ))}
            </div>
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
              <div className="space-y-4">
                {Array.from({ length: 2 }).map((_, index) => (
                  <div key={index} className="h-80 rounded-xl bg-muted/20 p-4 animate-pulse" />
                ))}
              </div>
              <div className="h-[640px] rounded-xl bg-muted/20 p-4 animate-pulse" />
            </div>
          </div>
        ) : feedsError || alertsError ? (
          <div className="rounded-xl border border-border bg-card p-6 text-center text-sm text-destructive">
            Unable to load live monitoring data: {(feedsError || alertsError)?.message}
          </div>
        ) : (
          <>
            {/* BUG 15 FIX: visible yellow banner when showing mock feeds in development */}
            {isMockData && !mockBannerDismissed && (
              <div className="mb-4 flex items-center justify-between rounded-xl border border-yellow-500/40 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-400">
                <span>⚠ Showing mock feeds — no camera feeds registered in backend.</span>
                <button
                  type="button"
                  onClick={() => setMockBannerDismissed(true)}
                  className="ml-4 rounded px-2 py-0.5 text-xs font-medium text-yellow-300 hover:bg-yellow-500/20"
                >
                  Dismiss
                </button>
              </div>
            )}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
              <StatCard
                label="Total CCTV Feeds"
                value={enrichedDisplayFeeds.length}
                sublabel="Active Cameras"
                icon={Camera}
                iconColor="#3b82f6"
                iconBg="rgba(59,130,246,0.15)"
              />
              <StatCard
                label="People Detected"
                value={totalPeople}
                sublabel="Across All Feeds"
                icon={Users}
                iconColor="#22c55e"
                iconBg="rgba(34,197,94,0.15)"
              />
              <StatCard
                label="Active Alerts"
                value={active}
                sublabel="Across All Feeds"
                icon={AlertTriangle}
                iconColor="#f97316"
                iconBg="rgba(249,115,22,0.15)"
              />
              <StatCard
                label="High Risk Detected"
                value={highRisk}
                sublabel="Require Attention"
                icon={Activity}
                iconColor="#ef4444"
                iconBg="rgba(239,68,68,0.15)"
              />
              <button
                type="button"
                onClick={() => setIsDialogOpen(true)}
                className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/30 transition-transform hover:scale-[1.02]"
              >
                <Plus className="h-4 w-4" /> Add CCTV Feed
              </button>
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add CCTV Feed</DialogTitle>
                    <DialogDescription>
                      Add a new camera stream so the live dashboard can monitor it in real time.
                    </DialogDescription>
                  </DialogHeader>
                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      /** BUG 1 FIX: pass source_url instead of url */
                      addFeedMutation.mutate({
                        id: cameraId,
                        name: platformName,
                        source_url: rtspUrl,
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1 text-sm">
                      <label className="block font-medium">Camera ID</label>
                      <input
                        value={cameraId}
                        onChange={(event) => setCameraId(event.target.value)}
                        placeholder="CCTV_P3_01"
                        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                        required
                      />
                    </div>
                    <div className="space-y-1 text-sm">
                      <label className="block font-medium">RTSP Stream URL</label>
                      <input
                        value={rtspUrl}
                        onChange={(event) => setRtspUrl(event.target.value)}
                        placeholder="rtsp://username:password@camera.local/stream"
                        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                        required
                      />
                    </div>
                    <div className="space-y-1 text-sm">
                      <label className="block font-medium">Platform Name</label>
                      <input
                        value={platformName}
                        onChange={(event) => setPlatformName(event.target.value)}
                        placeholder="Platform 3 South"
                        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                        required
                      />
                    </div>
                    <DialogFooter>
                      <button
                        type="button"
                        onClick={() => setIsDialogOpen(false)}
                        className="inline-flex items-center justify-center rounded-xl border border-border bg-secondary px-4 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-secondary/80"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={addFeedMutation.isPending}
                        className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {addFeedMutation.isPending ? "Adding..." : "Add Feed"}
                      </button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
              {filteredFeeds.length === 0 ? (
                <div className="rounded-xl border border-border bg-card p-8 text-center">
                  <h2 className="text-xl font-semibold text-foreground">
                    No camera feeds registered yet
                  </h2>
                  <p className="mt-3 text-sm text-muted-foreground">
                    No camera feeds registered yet. Click "Add CCTV Feed" to get started.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {filteredFeeds.map((f) => (
                    <CCTVFeedCard key={f.id} feed={f} detections={feedDetections[f.id]} />
                  ))}
                </div>
              )}

              <aside className="rounded-xl border border-border bg-card">
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <h3 className="text-sm font-semibold">Live Detections</h3>
                  <div className="relative">
                    <button
                      type="button"
                      id="live-detections-filter"
                      onClick={() => setFilterDropdownOpen((o) => !o)}
                      className="flex items-center gap-1 rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-secondary/80 transition-colors"
                    >
                      <span>
                        {filterLevel === "all"
                          ? "All Alerts"
                          : filterLevel === "high"
                            ? "High Risk"
                            : filterLevel === "medium"
                              ? "Medium Risk"
                              : "Low Risk"}
                      </span>
                      <ChevronDown className="h-3 w-3" />
                    </button>
                    {filterDropdownOpen && (
                      <>
                        <div
                          className="fixed inset-0 z-40"
                          onClick={() => setFilterDropdownOpen(false)}
                        />
                        <div className="absolute right-0 mt-1 z-50 w-32 overflow-hidden rounded-md border border-border bg-popover shadow-lg">
                          {(["all", "high", "medium", "low"] as const).map((level) => (
                            <button
                              key={level}
                              type="button"
                              onClick={() => {
                                setFilterLevel(level);
                                setFilterDropdownOpen(false);
                              }}
                              className="flex w-full items-center justify-between px-3 py-2 text-left text-xs transition-colors hover:bg-secondary hover:text-foreground"
                            >
                              <span>
                                {level === "all"
                                  ? "All Alerts"
                                  : level === "high"
                                    ? "High Risk"
                                    : level === "medium"
                                      ? "Medium Risk"
                                      : "Low Risk"}
                              </span>
                              {filterLevel === level && (
                                <Check className="h-3.5 w-3.5 text-[#22c55e]" />
                              )}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </div>
                <div className="max-h-[640px] space-y-3 overflow-y-auto p-3">
                  {filteredAlerts.length === 0 ? (
                    <div className="rounded-xl border border-border bg-secondary/5 p-6 text-center text-sm text-muted-foreground">
                      No active alerts.
                    </div>
                  ) : (
                    filteredAlerts.map((a) => {
                      const c = riskColor(a.riskLevel);
                      return (
                        <div
                          key={a.id}
                          className="flex gap-3 rounded-lg border p-3 transition-colors hover:bg-secondary/40"
                          style={{ borderColor: `${c}33`, backgroundColor: `${c}0a` }}
                        >
                          <div className="flex-1 min-w-0">
                            <div className="text-[11px] text-muted-foreground">{a.time}</div>
                            <div className="text-[11px] text-muted-foreground">
                              {a.cctv} / {a.platform}
                            </div>
                            <div className="mt-1 truncate text-sm font-semibold">{a.type}</div>
                            <div className="mt-1 text-xs">
                              Risk Score:{" "}
                              <span className="font-bold" style={{ color: c }}>
                                {a.riskScore}%
                              </span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <img
                              src={a.image}
                              alt=""
                              className="h-14 w-20 rounded object-cover"
                              loading="lazy"
                            />
                            <RiskBadge level={a.riskLevel} />
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
                <div className="border-t border-border p-3 text-center">
                  <Link
                    to="/alerts"
                    className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                  >
                    View All Alerts <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </aside>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
