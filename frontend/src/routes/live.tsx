import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { CCTVFeedCard } from "@/components/CCTVFeedCard";
import { RiskBadge } from "@/components/RiskBadge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Camera, Users, AlertTriangle, Activity, Plus, ChevronDown, ArrowRight } from "lucide-react";
import { getAlerts, type ApiAlert } from "@/lib/api/alerts";
import { createFeed, getFeeds } from "@/lib/api/feeds";
import { useWebSocket } from "@/hooks/useWebSocket";
import { riskColor } from "@/lib/mock-data";

interface LiveDetectionPayload {
  camera_id: string;
  platform: string;
  dimensions: {
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

interface LiveBoundingBox {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  level: string;
}

function mapCameraIdToFeedId(cameraId: string) {
  const match = cameraId.match(/CCTV(?:[_-]P?(\d+)|[_-]?(\d+))/i);
  const number = match ? Number(match[1] ?? match[2]) : NaN;
  if (Number.isFinite(number) && number > 0) {
    return `CCTV-${number}`;
  }
  const fallback = cameraId.match(/\d+/);
  return fallback ? `CCTV-${fallback[0]}` : cameraId;
}

export const Route = createFileRoute("/live")({
  head: () => ({ meta: [{ title: "Live Monitoring — RailMind AI" }] }),
  component: LivePage,
});

interface CreateFeedRequest {
  id: string;
  name: string;
  url: string;
}

function LivePage() {
  const [feed, setFeed] = useState("all");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [cameraId, setCameraId] = useState("");
  const [rtspUrl, setRtspUrl] = useState("");
  const [platformName, setPlatformName] = useState("");

  const queryClient = useQueryClient();

  const {
    data: feeds,
    isLoading: feedsLoading,
    error: feedsError,
  } = useQuery(["liveFeeds"], getFeeds);

  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
  } = useQuery(["liveAlerts"], getAlerts);

  const addFeedMutation = useMutation({
    mutationFn: (payload: CreateFeedRequest) => createFeed(payload),
    onSuccess: () => {
      setIsDialogOpen(false);
      setCameraId("");
      setRtspUrl("");
      setPlatformName("");
      queryClient.invalidateQueries(["liveFeeds"]);
    },
  });

  const latestMessage = useWebSocket<Record<string, any>>("ws://localhost:8000/ws/alerts");
  const [realtimeAlerts, setRealtimeAlerts] = useState<ApiAlert[]>([]);
  const [feedDetections, setFeedDetections] = useState<Record<string, LiveBoundingBox[]>>({});

  const filteredFeeds = useMemo(() => {
    const list = feeds ?? [];
    return feed === "all" ? list : list.filter((f) => f.id === feed);
  }, [feeds, feed]);

  useEffect(() => {
    if (alerts) {
      setRealtimeAlerts(alerts);
    }
  }, [alerts]);

  useEffect(() => {
    if (!latestMessage) {
      return;
    }

    if ("backendId" in latestMessage) {
      const latestAlert = latestMessage as ApiAlert;
      setRealtimeAlerts((current) => {
        if (current.some((alert) => alert.backendId === latestAlert.backendId)) {
          return current;
        }
        return [latestAlert, ...current];
      });
      return;
    }

    if ("camera_id" in latestMessage && Array.isArray(latestMessage.detections)) {
      const latestDetection = latestMessage as LiveDetectionPayload;
      const feedId = mapCameraIdToFeedId(latestDetection.camera_id);
      const { width, height } = latestDetection.dimensions;
      const boxes = latestDetection.detections.map((detection) => {
        const [x1, y1, x2, y2] = detection.bbox;
        const safeWidth = width || 1;
        const safeHeight = height || 1;

        return {
          id: detection.track_id,
          level: detection.risk_level,
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
    }
  }, [latestMessage]);

  const filteredAlerts = useMemo(() => {
    const list = realtimeAlerts;
    return feed === "all" ? list : list.filter((a) => a.cctv === feed);
  }, [realtimeAlerts, feed]);

  const totalPeople = filteredFeeds.reduce((s, f) => s + f.peopleDetected, 0);
  const active = filteredAlerts.filter((a) => a.status === "active").length;
  const highRisk = filteredAlerts.filter((a) => a.riskLevel === "high").length;

  return (
    <div>
      <TopBar
        title="Live Monitoring"
        subtitle="Real-time CCTV Monitoring & Threat Detection"
        selectedFeed={feed}
        onFeedChange={setFeed}
      />
      <div className="p-6">
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
            Unable to load live monitoring data. Please refresh the page.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <StatCard label="Total CCTV Feeds" value={feeds?.length ?? 0} sublabel="Active Cameras" icon={Camera} iconColor="#3b82f6" iconBg="rgba(59,130,246,0.15)" />
          <StatCard label="People Detected" value={totalPeople} sublabel="Across All Feeds" icon={Users} iconColor="#22c55e" iconBg="rgba(34,197,94,0.15)" />
          <StatCard label="Active Alerts" value={active} sublabel="Across All Feeds" icon={AlertTriangle} iconColor="#f97316" iconBg="rgba(249,115,22,0.15)" />
          <StatCard label="High Risk Detected" value={highRisk} sublabel="Require Attention" icon={Activity} iconColor="#ef4444" iconBg="rgba(239,68,68,0.15)" />
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
                  addFeedMutation.mutate({
                    id: cameraId,
                    name: platformName,
                    url: rtspUrl,
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
                    disabled={addFeedMutation.isLoading}
                    className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {addFeedMutation.isLoading ? "Adding..." : "Add Feed"}
                  </button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {filteredFeeds.map((f) => (
              <CCTVFeedCard key={f.id} feed={f} detections={feedDetections[f.id]} />
            ))}
          </div>

          <aside className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h3 className="text-sm font-semibold">Live Detections</h3>
              <button className="flex items-center gap-1 rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground">
                All Alerts <ChevronDown className="h-3 w-3" />
              </button>
            </div>
            <div className="max-h-[640px] space-y-3 overflow-y-auto p-3">
              {filteredAlerts.slice(0, 6).map((a) => {
                const c = riskColor(a.riskLevel);
                return (
                  <div
                    key={a.id}
                    className="flex gap-3 rounded-lg border p-3 transition-colors hover:bg-secondary/40"
                    style={{ borderColor: `${c}33`, backgroundColor: `${c}0a` }}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] text-muted-foreground">{a.time}</div>
                      <div className="text-[11px] text-muted-foreground">{a.cctv} / {a.platform}</div>
                      <div className="mt-1 truncate text-sm font-semibold">{a.type}</div>
                      <div className="mt-1 text-xs">
                        Risk Score: <span className="font-bold" style={{ color: c }}>{a.riskScore}%</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <img src={a.image} alt="" className="h-14 w-20 rounded object-cover" loading="lazy" />
                      <RiskBadge level={a.riskLevel} />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="border-t border-border p-3 text-center">
              <Link to="/alerts" className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
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