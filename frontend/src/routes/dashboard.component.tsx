import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopBar } from "@/components/TopBar";
import AddVideo from "@/components/AddVideo";
import { StatCard } from "@/components/StatCard";
import { RiskBadge } from "@/components/RiskBadge";
import {
  ClipboardList,
  AlertTriangle,
  User,
  PersonStanding,
  Shield,
  ExternalLink,
  Clock,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import { riskColor } from "@/lib/mock-data";
import {
  getDashboardStats,
  getIncidentsByCCTV,
  getIncidentTrend,
  getRiskDistribution,
  getPeakHours,
  getPlatformHeatmap,
  getCCTVSummary,
  getRecentIncidents,
} from "@/lib/api/dashboard";
import { deleteFeed, getFeeds } from "@/lib/api/feeds";
import { toast } from "sonner";

// Route exported in dashboard.tsx

const chartColors = ["#00e5ff", "#ff2d55", "#ff9f0a", "#00e676", "#3b82f6"];

export default function DashboardPage() {
  const [feed, setFeed] = useState("all");
  /** BUG 8 FIX: trendDays state, default 7 */
  const [trendDays, setTrendDays] = useState<7 | 30>(7);
  /** BUG 7 FIX: navigate hook for "View Full Heatmap" button */
  const navigate = useNavigate();

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({ queryKey: ["dashboardStats"], queryFn: getDashboardStats });

  const {
    data: byCctvData,
    isLoading: byCctvLoading,
    error: byCctvError,
  } = useQuery({ queryKey: ["incidentsByCCTV"], queryFn: getIncidentsByCCTV });

  /** BUG 8 FIX: queryKey and queryFn both use trendDays so selecting 30 days re-fetches */
  const {
    data: trend,
    isLoading: trendLoading,
    error: trendError,
  } = useQuery({
    queryKey: ["incidentTrend", trendDays],
    queryFn: () => getIncidentTrend(trendDays),
  });

  const {
    data: dist,
    isLoading: distLoading,
    error: distError,
  } = useQuery({ queryKey: ["riskDistribution"], queryFn: getRiskDistribution });

  const {
    data: peak,
    isLoading: peakLoading,
    error: peakError,
  } = useQuery({ queryKey: ["peakHours"], queryFn: getPeakHours });

  const {
    data: heatmap,
    isLoading: heatmapLoading,
    error: heatmapError,
  } = useQuery({ queryKey: ["platformHeatmap"], queryFn: getPlatformHeatmap });

  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({ queryKey: ["cctvSummary"], queryFn: getCCTVSummary });

  const {
    data: recent,
    isLoading: recentLoading,
    error: recentError,
  } = useQuery({ queryKey: ["recentIncidents"], queryFn: getRecentIncidents });

  const queryClient = useQueryClient();

  /** BUG 12 FIX: fetch feeds so TopBar can show dynamic camera list */
  const { data: feedsData } = useQuery({
    queryKey: ["liveFeeds"],
    queryFn: getFeeds,
    staleTime: 1000 * 60,
  });

  const queryErrors = [
    statsError && "stats",
    byCctvError && "incidents by CCTV",
    trendError && "trend",
    distError && "risk distribution",
    peakError && "peak hours",
    heatmapError && "heatmap",
    summaryError && "CCTV summary",
    recentError && "recent alerts",
  ].filter(Boolean);

  const byCctv = useMemo(() => {
    return (byCctvData ?? []).map((item, index) => ({
      name: item.camera_id,
      value: item.incidents,
      color: chartColors[index % chartColors.length],
    }));
  }, [byCctvData]);

  const heatmapRows = useMemo(() => {
    return (heatmap ?? []).map((point) => {
      const level =
        point.intensity >= 0.75
          ? "very-high"
          : point.intensity >= 0.5
            ? "high"
            : point.intensity >= 0.25
              ? "medium"
              : "low";
      const risk =
        point.intensity >= 0.75
          ? "Very High Risk"
          : point.intensity >= 0.5
            ? "High Risk"
            : point.intensity >= 0.25
              ? "Medium Risk"
              : "Low Risk";
      return {
        ...point,
        name: `${point.platform} ${point.zone}`,
        risk,
        level,
      };
    });
  }, [heatmap]);

  const totalByCctv = byCctv.reduce((s, x) => s + x.value, 0);

  /** BUG 13 FIX: compute actual peak hour from data */
  const peakHour = useMemo(() => {
    if (!peak || peak.length === 0) return null;
    return peak.reduce((max, h) => (h.incidents > max.incidents ? h : max), peak[0]);
  }, [peak]);

  /** BUG 12 FIX: dynamic feeds for TopBar */
  const dynamicFeeds = useMemo(() => {
    if (!Array.isArray(feedsData) || feedsData.length === 0) return undefined;
    return feedsData.map((f) => ({ id: f.id, label: `${f.id} (${f.platform})` }));
  }, [feedsData]);

  const stopFeed = async (feedId: string) => {
    try {
      await deleteFeed(feedId);
      await queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
      await queryClient.invalidateQueries({ queryKey: ["cctvSummary"] });
    } catch (err) {
      console.error("Failed to stop feed", err);
      // Optionally show a toast or inline error state here
    }
  };

  return (
    <div className="mx-auto max-w-screen-2xl space-y-6 p-6">
      <TopBar
        title="Dashboard"
        subtitle="Overview of all CCTV feeds and safety analytics"
        selectedFeed={feed}
        onFeedChange={setFeed}
        feeds={dynamicFeeds}
        right={<AddVideo />}
      />
      <div className="space-y-6">
        {queryErrors.length > 0 && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            Some dashboard panels could not load: {queryErrors.join(", ")}.
          </div>
        )}
        {/* BUG 14 FIX: removed hardcoded change/dir props from all StatCards */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-5">
          <StatCard
            label="Total Incidents"
            value={stats?.total_incidents ?? 0}
            icon={ClipboardList}
            iconColor="#a855f7"
            iconBg="rgba(168,85,247,0.15)"
          />
          <StatCard
            label="Active Alerts"
            value={stats?.active_alerts ?? 0}
            icon={AlertTriangle}
            iconColor="#ef4444"
            iconBg="rgba(239,68,68,0.15)"
          />
          <StatCard
            label="Track Zone Intrusions"
            value={stats?.track_zone_intrusions ?? 0}
            icon={User}
            iconColor="#f97316"
            iconBg="rgba(249,115,22,0.15)"
          />
          <StatCard
            label="Loitering / Trespass"
            value={stats?.loitering_trespass ?? 0}
            icon={PersonStanding}
            iconColor="#a855f7"
            iconBg="rgba(168,85,247,0.15)"
          />
          <StatCard
            label="General Anomalies"
            value={stats?.general_anomalies ?? 0}
            icon={Shield}
            iconColor="#3b82f6"
            iconBg="rgba(59,130,246,0.15)"
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-[2.2fr_minmax(360px,1fr)]">
          <div className="hud-panel rounded-xl bg-card p-5">
            {/* Top accent line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                  Trend overview
                </p>
                <h3 className="text-xl font-semibold">Incident Trend</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Rolling alert distribution across major incident categories.
                </p>
              </div>
              <div className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary px-3 py-2 text-xs text-muted-foreground">
                <label htmlFor="trend-period-select" className="cursor-pointer">
                  Window
                </label>
                <select
                  id="trend-period-select"
                  value={trendDays}
                  onChange={(e) => setTrendDays(Number(e.target.value) as 7 | 30)}
                  className="rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground"
                >
                  <option value={7}>7 Days</option>
                  <option value={30}>30 Days</option>
                </select>
              </div>
            </div>

            <div className="mt-5 h-[340px] sm:h-[360px]">
              {trendLoading ? (
                <div className="h-full rounded-lg bg-muted/20 animate-pulse" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={trend ?? []}
                    margin={{ top: 10, right: 12, left: -12, bottom: 0 }}
                  >
                    <CartesianGrid stroke="#1a2432" vertical={false} />
                    <XAxis dataKey="date" stroke="#6b7f99" fontSize={11} />
                    <YAxis stroke="#6b7f99" fontSize={11} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line
                      type="monotone"
                      dataKey="Track Zone Intrusion"
                      name="Track Zone Intrusion"
                      stroke="#ff2d55"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Loitering / Trespass"
                      name="Loitering / Trespass"
                      stroke="#ff9f0a"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="General Anomalies"
                      name="General Anomalies"
                      stroke="#00e5ff"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="grid gap-6">
            <div className="hud-panel rounded-xl bg-card p-5">
              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
              <h3 className="text-sm font-semibold">Incidents by CCTV</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Camera-level alert volume for active stations.
              </p>
              <div className="mt-5 flex items-center gap-4">
                <div className="relative h-44 w-44 shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={byCctv}
                        dataKey="value"
                        innerRadius={50}
                        outerRadius={75}
                        stroke="none"
                      >
                        {byCctv.map((d) => (
                          <Cell key={d.name} fill={d.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <div className="text-2xl font-bold">{totalByCctv}</div>
                    <div className="text-[11px] text-muted-foreground">Total</div>
                  </div>
                </div>
                <div className="flex-1 space-y-2 text-sm">
                  {byCctv.map((d) => (
                    <div key={d.name} className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: d.color }}
                        />
                        <span>{d.name}</span>
                      </div>
                      <span className="tabular-nums text-muted-foreground">
                        {d.value} ({Math.round(totalByCctv ? (d.value / totalByCctv) * 100 : 0)}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <Link
                to="/live"
                className="mt-5 inline-flex w-full items-center justify-center rounded-lg border border-border bg-secondary py-2 text-xs font-semibold text-muted-foreground transition hover:text-foreground"
              >
                View All Cameras
              </Link>
            </div>

            <div className="hud-panel rounded-xl bg-card p-5">
              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
              <h3 className="text-sm font-semibold">Risk Distribution</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Category share across current incidents.
              </p>
              <div className="mt-5 flex items-center gap-4">
                <div className="relative h-44 w-44 shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={dist ?? []}
                        dataKey="value"
                        innerRadius={50}
                        outerRadius={75}
                        stroke="none"
                      >
                        {(dist ?? []).map((d) => (
                          <Cell key={d.name} fill={d.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <div className="text-2xl font-bold">{stats?.total_incidents ?? 0}</div>
                    <div className="text-[11px] text-muted-foreground">Total</div>
                  </div>
                </div>
                <div className="flex-1 space-y-2 text-sm">
                  {(dist ?? []).map((d) => (
                    <div key={d.name}>
                      <div className="flex items-center gap-2 text-xs">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: d.color }}
                        />
                        <span>{d.name}</span>
                      </div>
                      <div className="ml-4 text-xs text-muted-foreground">{d.value}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Row 2 */}
        <div className="grid grid-cols-1 gap-6 items-start lg:grid-cols-3">
          {/* Heatmap */}
          <div className="hud-panel rounded-xl bg-card p-5">
            {/* Top accent line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
            <h3 className="text-sm font-semibold">
              Platform Heatmap <span className="text-muted-foreground">(Risk Intensity)</span>
            </h3>
            <div className="mt-4 max-h-[420px] space-y-4 overflow-y-auto pr-1">
              {heatmapRows.length === 0 ? (
                <div className="rounded-lg border border-border/50 bg-secondary/20 px-4 py-6 text-center">
                  <div className="text-sm text-muted-foreground">
                    No heatmap data yet. Data appears once the CV pipeline processes feeds.
                  </div>
                </div>
              ) : (
                heatmapRows.map((p) => (
                  <div key={p.name} className="flex items-center gap-3">
                    <div className="w-24">
                      <div className="text-xs font-medium font-mono">{p.name}</div>
                      <div
                        className="text-[11px]"
                        style={{ color: riskColor(p.level === "very-high" ? "high" : p.level) }}
                      >
                        {p.risk}
                      </div>
                    </div>
                    <div className="relative h-10 flex-1 overflow-hidden rounded-md border border-border bg-secondary/40">
                      <Hotspots point={p} />
                    </div>
                  </div>
                ))
              )}
            </div>
            <p className="mt-3 text-[11px] text-muted-foreground">
              Positions are illustrative; intensity reflects real incident data.
            </p>
            <div className="mt-4 flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Low</span>
              <div className="mx-3 h-1.5 flex-1 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 to-red-500" />
              <span>Very High</span>
            </div>
            {/* BUG 7 FIX: navigate to /live on click */}
            <button
              type="button"
              onClick={() => navigate({ to: "/live" })}
              className="mt-3 flex w-full items-center justify-center gap-1 rounded-lg border border-border bg-secondary py-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              View Full Heatmap <ExternalLink className="h-3 w-3" />
            </button>
          </div>

          {/* Peak hours */}
          <div className="hud-panel rounded-xl bg-card p-5">
            {/* Top accent line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
            <h3 className="text-sm font-semibold">Peak Risk Hours</h3>
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={peak ?? []} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke="#1a2432" vertical={false} />
                  <XAxis dataKey="hour" stroke="#6b7f99" fontSize={10} interval={3} />
                  <YAxis stroke="#6b7f99" fontSize={11} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="incidents" fill="#00e5ff" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* BUG 13 FIX: display computed peak hour from data */}
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs">
              <Clock className="h-4 w-4 text-primary" />
              <span>
                Peak Time:{" "}
                <span className="font-semibold text-primary font-mono">
                  {peakHour?.hour ?? "—"}
                </span>
              </span>
            </div>
          </div>

          {/* Recent alerts */}
          <div className="hud-panel rounded-xl bg-card">
            {/* Top accent line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="text-sm font-semibold">Recent Alerts</h3>
              <a href="/alerts" className="text-xs font-medium text-primary hover:underline">
                View All
              </a>
            </div>
            <div className="space-y-3 p-3">
              {(recent ?? []).map((a) => (
                <div
                  key={a.id}
                  className="flex gap-3 rounded-lg p-2 transition-colors hover:bg-secondary/50"
                >
                  <img
                    src={a.image}
                    alt=""
                    className="h-14 w-20 rounded object-cover"
                    loading="lazy"
                  />
                  <div className="flex-1 min-w-0">
                    <RiskBadge
                      level={a.riskLevel}
                      label={
                        a.riskLevel === "high"
                          ? "HIGH"
                          : a.riskLevel === "medium"
                            ? "MEDIUM"
                            : a.riskLevel === "suspicious"
                              ? "MEDIUM"
                              : "LOW"
                      }
                    />
                    <div className="mt-1 truncate text-sm font-medium">{a.type}</div>
                    <div className="text-[11px] text-muted-foreground">
                      {a.cctv} | {a.platform}
                    </div>
                    <div className="text-[11px] text-muted-foreground">{a.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CCTV Summary */}
        <div className="hud-panel rounded-xl bg-card">
          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent pointer-events-none" />
          <div className="border-b border-border p-4">
            <h3 className="text-sm font-semibold">CCTV Summary</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-foreground">
                  <th className="px-4 py-3 font-medium">CCTV ID</th>
                  <th className="px-4 py-3 font-medium">Location</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Total Incidents</th>
                  <th className="px-4 py-3 font-medium">Active Alerts</th>
                  <th className="px-4 py-3 font-medium">Last Incident</th>
                  <th className="px-4 py-3 font-medium">Risk Level</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {(summary ?? []).map((row) => (
                  <tr
                    key={row.camera_id}
                    className="border-t border-border transition-colors hover:bg-secondary/40"
                  >
                    <td className="px-4 py-3 font-medium font-mono">{row.camera_id}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.location}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-md px-2 py-0.5 text-[11px] font-semibold font-mono tracking-wider ${row.status === "active" ? "bg-[#00e676]/15 text-[#00e676]" : "bg-[#6b7f99]/15 text-[#6b7f99]"}`}
                      >
                        {row.status === "active" ? "ONLINE" : "OFFLINE"}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">{row.total_incidents}</td>
                    <td className="px-4 py-3 font-mono">{row.active_alerts}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground font-mono">
                      {row.last_incident ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge
                        level={
                          row.current_risk_level.toLowerCase().includes("high")
                            ? "high"
                            : row.current_risk_level.toLowerCase().includes("medium")
                              ? "medium"
                              : row.current_risk_level.toLowerCase().includes("suspicious")
                                ? "suspicious"
                                : "low"
                        }
                        label={row.current_risk_level.toUpperCase()}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => stopFeed(row.camera_id)}
                        className="rounded-md border border-[#ff2d55]/30 bg-[#ff2d55]/10 px-3 py-1 text-xs font-medium text-[#ff2d55] transition hover:bg-[#ff2d55]/20 hover:shadow-[var(--glow-danger)]"
                      >
                        Stop
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

const tooltipStyle = {
  backgroundColor: "rgba(11, 14, 20, 0.75)",
  backdropFilter: "blur(16px)",
  border: "1px solid #1a2432",
  borderRadius: 8,
  fontSize: 12,
};

function Hotspots({
  point,
}: {
  point: { level: string; platform: string; zone: string; intensity: number };
}) {
  const normalizedLevel = point.level === "very-high" ? "high" : point.level;
  const color = riskColor(normalizedLevel as "low" | "medium" | "high" | "very-high");
  const zoneHash = Array.from(`${point.platform}:${point.zone}`).reduce(
    (sum, char) => sum + char.charCodeAt(0),
    0,
  );
  const mainX = 10 + (zoneHash % 70);
  const intensityX = 10 + Math.round(point.intensity * 80);
  const size = 12 + Math.round(point.intensity * 18);

  return (
    <>
      <span
        className="absolute top-1/2 h-10 w-10 -translate-y-1/2 rounded-full blur-xl opacity-70"
        style={{ left: `${mainX}%`, backgroundColor: color }}
      />
      <span
        className="absolute top-1/2 h-8 w-8 -translate-y-1/2 rounded-full blur-lg opacity-80"
        style={{ left: `${intensityX}%`, backgroundColor: color }}
      />
      <span
        className="absolute top-1/2 rounded-full opacity-90"
        style={{
          left: `${Math.min(95, Math.max(5, Math.round((mainX + intensityX) / 2)))}%`,
          width: `${size}px`,
          height: `${size}px`,
          backgroundColor: color,
        }}
      />
    </>
  );
}
