// frontend/src/routes/live.component.tsx
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
import { createFeed, deleteFeed, getFeeds, uploadVideo, type Feed } from "@/lib/api/feeds";
import { riskColor, type BoundingBox, type RiskLevel, type CCTVFeed } from "@/lib/mock-data";
import { parseCameraId } from "@/lib/utils";

// Route exported in live.tsx
export const Route = createFileRoute("/live")({
  component: LivePage,
});

type FilterLevel = "all" | "high" | "medium" | "low";
type FeedSubmissionMode = "upload" | "stream";

// Real-time detection payload from WebSocket
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

// Helper to normalize track_id to number for BoundingBox.id
function normalizeTrackId(trackId: string): number {
  const parsed = Number(trackId);
  return Number.isFinite(parsed)
    ? parsed
    : trackId.split("").reduce((sum, char) => sum + char.charCodeAt(0), 0);
}

// Map camera_id from backend to feed id (if different)
function mapCameraIdToFeedId(cameraId: string) {
  return parseCameraId(cameraId);
}

export default function LivePage() {
  const [feed, setFeed] = useState("all");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [cameraId, setCameraId] = useState("");
  const [platformName, setPlatformName] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [sourceUrl, setSourceUrl] = useState("");
  const [submissionMode, setSubmissionMode] = useState<FeedSubmissionMode>("upload");
  const [feedToRemove, setFeedToRemove] = useState<string | null>(null);
  const [filterLevel, setFilterLevel] = useState<FilterLevel>("all");
  const [filterDropdownOpen, setFilterDropdownOpen] = useState(false);

  const queryClient = useQueryClient();

  // --- Feeds query with polling when any feed is processing ---
  const {
    data: feeds,
    isLoading: feedsLoading,
    error: feedsError,
  } = useQuery<Feed[]>({
    queryKey: ["liveFeeds"],
    queryFn: getFeeds,
    staleTime: 1000 * 60,
    refetchInterval: (query) => {
      const feeds = query.state.data as Feed[] | undefined;
      if (feeds?.some((f) => f.status === "processing")) {
        return 2000; // poll every 2 seconds while processing
      }
      return false;
    },
  });

  // --- Alerts query ---
  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
  } = useQuery({
    queryKey: ["liveAlerts"],
    queryFn: getAlerts,
    refetchInterval: 30_000,
  });

  // --- Mutations ---

  const resetDialogState = useCallback(() => {
    setCameraId("");
    setPlatformName("");
    setUploadedFile(null);
    setSourceUrl("");
    setSubmissionMode("upload");
  }, []);

  const addFeedMutation = useMutation({
    mutationFn: (payload: { file: File; feedId: string; name: string }) =>
      uploadVideo(payload.file, payload.feedId, payload.name),
    onSuccess: () => {
      setIsDialogOpen(false);
      resetDialogState();
      queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
      toast.success("Video uploaded; processing in background.");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to upload video.");
    },
  });

  const addLiveFeedMutation = useMutation({
    mutationFn: (payload: { id: string; name: string; source_url: string }) => createFeed(payload),
    onSuccess: () => {
      setIsDialogOpen(false);
      resetDialogState();
      queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
      toast.success("Live stream feed added successfully!");
    },
    onError: () => {
      toast.error("Failed to add live stream feed. Please check the URL and inputs.");
    },
  });

  const removeFeedMutation = useMutation({
    mutationFn: deleteFeed,
    onSuccess: () => {
      setFeedToRemove(null);
      queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
      toast.success("Feed removed successfully.");
    },
    onError: () => {
      toast.error("Failed to remove feed.");
    },
  });

  const [realtimeAlerts, setRealtimeAlerts] = useState<ApiAlert[]>([]);
  const [feedAlerts, setFeedAlerts] = useState<
    Record<string, { alertType: string; riskScore: number; riskLevel: RiskLevel }>
  >({});
  const [feedDetections, setFeedDetections] = useState<Record<string, BoundingBox[]>>({});
  const [feedPeopleCount, setFeedPeopleCount] = useState<Record<string, number>>({});
  const [soundEnabled, setSoundEnabled] = useState(true);
  const SHOWN_TOAST_MAX = 500;
  const shownToastIds = useRef<Map<number, true>>(new Map());
  const lastAudioPlaybackAt = useRef<number>(0);

  const playNotificationSound = useCallback(() => {
    if (typeof window === "undefined") return;
    const now = Date.now();
    if (now - lastAudioPlaybackAt.current < 300) return;
    lastAudioPlaybackAt.current = now;

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
      // Ignore audio failures
    }
  }, []);

  const showAlertToast = useCallback(
    (alert: ApiAlert) => {
      if (shownToastIds.current.has(alert.backendId)) return;
      // Evict oldest if cap reached
      if (shownToastIds.current.size >= SHOWN_TOAST_MAX) {
        const oldestKey = shownToastIds.current.keys().next().value;
        if (oldestKey !== undefined) {
          shownToastIds.current.delete(oldestKey);
        }
      }
      shownToastIds.current.set(alert.backendId, true);

      const message = `${alert.cctv} — ${alert.type} — Risk: ${alert.riskScore}%`;
      const isHighRisk = alert.riskLevel === "high";
      const isMediumRisk = alert.riskLevel === "medium" || alert.riskLevel === "suspicious";
      const icon = (
        <span
          className={`inline-flex h-3.5 w-3.5 rounded-full ${
            isHighRisk ? "bg-[#ff2d55]" : isMediumRisk ? "bg-[#ff9f0a]" : "bg-[#00e676]"
          }`}
          style={{
            boxShadow: isHighRisk
              ? "0 0 8px rgba(255, 45, 85, 0.6)"
              : isMediumRisk
                ? "0 0 8px rgba(255, 159, 10, 0.5)"
                : "0 0 6px rgba(0, 230, 118, 0.4)",
          }}
        />
      );

      const options = { icon, duration: isHighRisk ? Infinity : 5000 } as const;
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

  // --- Convert backend feeds to frontend CCTVFeed ---
  const displayFeeds = useMemo<CCTVFeed[]>(() => {
    if (!feeds) return [];
    return feeds.map((f) => ({
      id: f.id,
      name: f.name,
      platform: f.name,
      status: f.status,
      streamUrl: f.stream_url || "",
      peopleDetected: f.track_count ?? 0,
      error_message: f.error_message,
      track_count: f.track_count,
      alertType: undefined,
      riskScore: undefined,
      riskLevel: undefined,
      image: "/cctv-platform.jpg",
    }));
  }, [feeds]);

  // --- Merge real-time data into feeds ---
  const enrichedDisplayFeeds = useMemo(() => {
    return displayFeeds.map((f) => ({
      ...f,
      peopleDetected: feedPeopleCount[f.id] ?? f.peopleDetected,
      ...(feedAlerts[f.id] ?? {}),
    }));
  }, [displayFeeds, feedPeopleCount, feedAlerts]);

  // --- Filter feeds by selected camera ---
  const filteredFeeds = useMemo(() => {
    const list = enrichedDisplayFeeds;
    return feed === "all" ? list : list.filter((f) => f.id === feed);
  }, [enrichedDisplayFeeds, feed]);

  // --- Update realtime alerts ---
  useEffect(() => {
    if (alerts && alerts.length > 0) {
      setRealtimeAlerts(alerts);
    }
  }, [alerts]);

  // --- Resolve feed id from camera_id ---
  const resolveFeedId = useCallback(
    (cameraId: string) => {
      if (Array.isArray(feeds)) {
        const exactMatch = feeds.find((f) => f.id === cameraId);
        if (exactMatch) return cameraId;
        const mapped = mapCameraIdToFeedId(cameraId);
        const mappedMatch = feeds.find((f) => f.id === mapped);
        if (mappedMatch) return mapped;
      }
      return cameraId;
    },
    [feeds],
  );

  // --- Filter alerts for sidebar ---
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

  // --- Stats ---
  const totalPeople = useMemo(
    () => filteredFeeds.reduce((sum, f) => sum + (f.peopleDetected ?? 0), 0),
    [filteredFeeds],
  );
  const active = filteredAlerts.filter((a) => a.status === "active").length;
  const highRisk = filteredAlerts.filter((a) => a.riskLevel === "high").length;

  // --- Dynamic feeds for TopBar ---
  const dynamicFeeds = useMemo(() => {
    if (!enrichedDisplayFeeds.length) return undefined;
    return enrichedDisplayFeeds.map((f) => ({ id: f.id, label: `${f.id} (${f.platform})` }));
  }, [enrichedDisplayFeeds]);

  const liveDataError = feedsError ?? alertsError;

  // --- Loading / Error states ---
  if (feedsLoading || alertsLoading) {
    return (
      <div className="space-y-4 p-6">
        <div className="h-6 w-1/3 rounded bg-muted/30 animate-pulse" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-muted/20 p-4 animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="h-80 rounded-xl bg-muted/20 p-4 animate-pulse" />
            ))}
          </div>
          <div className="h-[640px] rounded-xl bg-muted/20 p-4 animate-pulse" />
        </div>
      </div>
    );
  }

  if (liveDataError) {
    return (
      <div className="p-6 text-center text-sm text-destructive">
        Unable to load live monitoring data: {liveDataError.message}
      </div>
    );
  }

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
        {/* Stats & Add Button */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <StatCard
            label="Total CCTV Feeds"
            value={filteredFeeds.length}
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
            iconColor="#ff9f0a"
            iconBg="rgba(255,159,10,0.15)"
          />
          <StatCard
            label="High Risk Detected"
            value={highRisk}
            sublabel="Require Attention"
            icon={Activity}
            iconColor="#ff2d55"
            iconBg="rgba(255,45,85,0.15)"
          />
          <button
            type="button"
            onClick={() => setIsDialogOpen(true)}
            className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:scale-[1.02] hover:shadow-[var(--glow-primary)]"
          >
            <Plus className="h-4 w-4" /> Add CCTV Feed
          </button>
        </div>

        {/* Dialog for adding feed */}
        <Dialog
          open={isDialogOpen}
          onOpenChange={(open) => {
            setIsDialogOpen(open);
            if (!open) resetDialogState();
          }}
        >
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
                if (submissionMode === "stream") {
                  addLiveFeedMutation.mutate({
                    id: cameraId,
                    name: platformName,
                    source_url: sourceUrl,
                  });
                  return;
                }
                if (uploadedFile) {
                  addFeedMutation.mutate({
                    file: uploadedFile,
                    feedId: cameraId,
                    name: platformName,
                  });
                }
              }}
              className="space-y-4"
            >
              <div className="flex rounded-lg border border-border bg-muted/50 p-1">
                {(
                  [
                    ["upload", "Upload Video File"],
                    ["stream", "Add Live Stream (RTSP/HTTP URL)"],
                  ] as const
                ).map(([mode, label]) => {
                  const isActive = submissionMode === mode;
                  return (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => setSubmissionMode(mode)}
                      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${
                        isActive
                          ? "bg-background text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>

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
                <label className="block font-medium">Platform Name</label>
                <input
                  value={platformName}
                  onChange={(event) => setPlatformName(event.target.value)}
                  placeholder="Platform 3 South"
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  required
                />
              </div>
              {submissionMode === "stream" ? (
                <div className="space-y-1 text-sm">
                  <label className="block font-medium">Source URL</label>
                  <input
                    value={sourceUrl}
                    onChange={(event) => setSourceUrl(event.target.value)}
                    placeholder="rtsp://camera.local/stream"
                    className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    required
                  />
                </div>
              ) : (
                <div className="space-y-2 text-sm">
                  <label className="block font-medium">Select Video File</label>
                  <div className="flex flex-col gap-2">
                    <label className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-input bg-muted/50 px-4 py-6 cursor-pointer hover:border-primary hover:bg-muted/75 transition">
                      <input
                        type="file"
                        accept="video/*"
                        onChange={(event) => {
                          const file = event.currentTarget.files?.[0];
                          if (file) setUploadedFile(file);
                        }}
                        className="hidden"
                        required={submissionMode === "upload"}
                      />
                      <div className="text-center">
                        <p className="font-medium text-sm">
                          {uploadedFile ? uploadedFile.name : "Click to select a video file"}
                        </p>
                        {!uploadedFile && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Supported formats: MP4, WebM, MOV, AVI, etc.
                          </p>
                        )}
                      </div>
                    </label>
                    {uploadedFile && (
                      <button
                        type="button"
                        onClick={() => setUploadedFile(null)}
                        className="text-xs text-destructive hover:text-destructive/80 font-medium"
                      >
                        Clear selection
                      </button>
                    )}
                  </div>
                </div>
              )}
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
                  disabled={
                    addFeedMutation.isPending ||
                    addLiveFeedMutation.isPending ||
                    (submissionMode === "upload" ? !uploadedFile : !sourceUrl)
                  }
                  className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submissionMode === "stream"
                    ? addLiveFeedMutation.isPending
                      ? "Adding..."
                      : "Add Live Feed"
                    : addFeedMutation.isPending
                      ? "Uploading..."
                      : "Upload Feed"}
                </button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Main grid: feeds + sidebar */}
        <div className="mt-6 grid grid-cols-1 gap-6 items-start xl:grid-cols-[1fr_360px]">
          {filteredFeeds.length === 0 ? (
            <div className="rounded-xl border border-border bg-card p-8 text-center">
              <h2 className="text-xl font-semibold text-foreground">No active CCTV feeds</h2>
              <p className="mt-3 text-sm text-muted-foreground">Add a feed to begin monitoring.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 items-start md:grid-cols-2">
              {filteredFeeds.map((f) => (
                <CCTVFeedCard
                  key={f.id}
                  feed={f}
                  detections={feedDetections[f.id]}
                  onRemove={(feedId) => setFeedToRemove(feedId)}
                  removing={removeFeedMutation.isPending}
                />
              ))}
            </div>
          )}

          {/* Live Detections Sidebar */}
          <aside className="hud-panel rounded-xl bg-card">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h3 className="text-sm font-semibold">Live Detections</h3>
              <div className="relative">
                <button
                  type="button"
                  id="live-detections-filter"
                  aria-label={`Filter live detections: ${filterLevel}`}
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
                    <div className="absolute right-0 mt-1 z-50 w-32 overflow-hidden rounded-md border border-[#1a2432]/90 bg-[#0b0e14]/75 backdrop-blur-md shadow-lg">
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
                            <Check className="h-3.5 w-3.5 text-[#00e676]" />
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
                        <div className="text-[11px] text-muted-foreground font-mono">{a.time}</div>
                        <div className="text-[11px] text-muted-foreground font-mono">
                          {a.cctv} / {a.platform}
                        </div>
                        <div className="mt-1 truncate text-sm font-semibold">{a.type}</div>
                        <div className="mt-1 text-xs">
                          Risk Score:{" "}
                          <span className="font-bold font-mono" style={{ color: c }}>
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
      </div>

      {/* Remove Confirmation Dialog */}
      <Dialog open={Boolean(feedToRemove)} onOpenChange={(open) => !open && setFeedToRemove(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Remove feed?</DialogTitle>
            <DialogDescription>
              This will stop processing and delete the selected feed. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              type="button"
              onClick={() => setFeedToRemove(null)}
              className="inline-flex items-center justify-center rounded-xl border border-border bg-secondary px-4 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-secondary/80"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                if (!feedToRemove) return;
                removeFeedMutation.mutate(feedToRemove);
              }}
              disabled={removeFeedMutation.isPending}
              className="inline-flex items-center justify-center rounded-xl bg-destructive px-4 py-2 text-sm font-semibold text-destructive-foreground transition disabled:cursor-not-allowed disabled:opacity-60"
            >
              {removeFeedMutation.isPending ? "Removing..." : "Remove"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
