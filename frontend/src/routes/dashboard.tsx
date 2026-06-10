import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { RiskBadge } from "@/components/RiskBadge";
import {
  ClipboardList, AlertTriangle, User, PersonStanding, Shield,
  ExternalLink, Clock,
} from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, BarChart, Bar,
} from "recharts";
import {
  generateAlerts, getCCTVSummary, getDashboardStats, getIncidentTrend,
  getIncidentsByCCTV, getPeakHours, getPlatformHeatmap, getRiskDistribution, riskColor,
} from "@/lib/mock-data";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — RailMind AI" }] }),
  component: DashboardPage,
});

function DashboardPage() {
  const [feed, setFeed] = useState("all");
  const stats = getDashboardStats();
  const byCctv = useMemo(getIncidentsByCCTV, []);
  const trend = useMemo(getIncidentTrend, []);
  const dist = useMemo(getRiskDistribution, []);
  const peak = useMemo(getPeakHours, []);
  const heatmap = getPlatformHeatmap();
  const summary = getCCTVSummary();
  const recent = useMemo(() => generateAlerts(8).slice(0, 4), []);

  const totalByCctv = byCctv.reduce((s, x) => s + x.value, 0);
  const totalDist = dist.reduce((s, x) => s + x.value, 0);

  return (
    <div>
      <TopBar
        title="Dashboard"
        subtitle="Overview of all CCTV feeds and safety analytics"
        selectedFeed={feed}
        onFeedChange={setFeed}
      />
      <div className="space-y-6 p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-5">
          <StatCard label="Total Incidents" value={stats.totalIncidents.value} change={stats.totalIncidents.change} dir="up" icon={ClipboardList} iconColor="#a855f7" iconBg="rgba(168,85,247,0.15)" />
          <StatCard label="Active Alerts" value={stats.activeAlerts.value} change={stats.activeAlerts.change} dir="up" icon={AlertTriangle} iconColor="#ef4444" iconBg="rgba(239,68,68,0.15)" />
          <StatCard label="Suicide Risk" value={stats.suicideRisk.value} change={stats.suicideRisk.change} dir="up" icon={User} iconColor="#f97316" iconBg="rgba(249,115,22,0.15)" />
          <StatCard label="Pickpocketing Risk" value={stats.pickpocketingRisk.value} change={stats.pickpocketingRisk.change} dir="up" icon={PersonStanding} iconColor="#a855f7" iconBg="rgba(168,85,247,0.15)" />
          <StatCard label="Security Threats" value={stats.securityThreats.value} change={stats.securityThreats.change} dir="up" icon={Shield} iconColor="#3b82f6" iconBg="rgba(59,130,246,0.15)" />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Incidents by CCTV */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold">Incidents by CCTV</h3>
            <div className="mt-4 flex items-center gap-4">
              <div className="relative h-44 w-44 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={byCctv} dataKey="value" innerRadius={50} outerRadius={75} stroke="none">
                      {byCctv.map((d) => <Cell key={d.name} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-2xl font-bold">{totalByCctv}</div>
                  <div className="text-[11px] text-muted-foreground">Total</div>
                </div>
              </div>
              <div className="flex-1 space-y-1.5 text-sm">
                {byCctv.map((d) => (
                  <div key={d.name} className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
                      <span>{d.name}</span>
                    </div>
                    <span className="tabular-nums text-muted-foreground">
                      {d.value} ({Math.round((d.value / totalByCctv) * 100)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <button className="mt-4 w-full rounded-lg border border-border bg-secondary py-2 text-xs text-muted-foreground hover:text-foreground">
              View All Cameras
            </button>
          </div>

          {/* Trend */}
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">
                Incident Trend <span className="text-muted-foreground">(Last 7 Days)</span>
              </h3>
              <select className="rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground">
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
              </select>
            </div>
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke="#1e1e2e" vertical={false} />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="total" name="Total Incidents" stroke="#a855f7" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="suicide" name="Suicide Risk" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="pickpocket" name="Pickpocketing Risk" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="security" name="Security Threats" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk distribution */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold">Risk Distribution</h3>
            <div className="mt-4 flex items-center gap-4">
              <div className="relative h-44 w-44 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={dist} dataKey="value" innerRadius={50} outerRadius={75} stroke="none">
                      {dist.map((d) => <Cell key={d.name} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-2xl font-bold">{totalDist}</div>
                  <div className="text-[11px] text-muted-foreground">Total</div>
                </div>
              </div>
              <div className="flex-1 space-y-2 text-sm">
                {dist.map((d) => (
                  <div key={d.name}>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
                      <span>{d.name}</span>
                    </div>
                    <div className="ml-4 text-xs text-muted-foreground">
                      {((d.value / totalDist) * 100).toFixed(1)}% ({d.value})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Row 2 */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Heatmap */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold">
              Platform Heatmap <span className="text-muted-foreground">(Risk Intensity)</span>
            </h3>
            <div className="mt-4 space-y-4">
              {heatmap.map((p) => (
                <div key={p.name} className="flex items-center gap-3">
                  <div className="w-24">
                    <div className="text-xs font-medium">{p.name}</div>
                    <div className="text-[11px]" style={{ color: riskColor(p.level === "very-high" ? "high" : p.level) }}>
                      {p.risk}
                    </div>
                  </div>
                  <div className="relative h-10 flex-1 overflow-hidden rounded-md border border-border bg-secondary/40">
                    <Hotspots level={p.level} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Low</span>
              <div className="mx-3 h-1.5 flex-1 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 to-red-500" />
              <span>Very High</span>
            </div>
            <button className="mt-3 flex w-full items-center justify-center gap-1 rounded-lg border border-border bg-secondary py-2 text-xs text-muted-foreground hover:text-foreground">
              View Full Heatmap <ExternalLink className="h-3 w-3" />
            </button>
          </div>

          {/* Peak hours */}
          <div className="rounded-xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold">Peak Risk Hours</h3>
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={peak} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke="#1e1e2e" vertical={false} />
                  <XAxis dataKey="hour" stroke="#94a3b8" fontSize={10} interval={3} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="incidents" fill="#6366f1" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs">
              <Clock className="h-4 w-4 text-primary" />
              <span>Peak Time: <span className="font-semibold text-primary">12:00 PM – 04:00 PM</span></span>
            </div>
          </div>

          {/* Recent alerts */}
          <div className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="text-sm font-semibold">Recent Alerts</h3>
              <a href="/alerts" className="text-xs font-medium text-primary hover:underline">View All</a>
            </div>
            <div className="space-y-3 p-3">
              {recent.map((a) => (
                <div key={a.id} className="flex gap-3 rounded-lg p-2 transition-colors hover:bg-secondary/50">
                  <img src={a.image} alt="" className="h-14 w-20 rounded object-cover" loading="lazy" />
                  <div className="flex-1 min-w-0">
                    <RiskBadge level={a.riskLevel} label={a.riskLevel === "high" ? "HIGH" : a.riskLevel === "medium" ? "MEDIUM" : a.riskLevel === "suspicious" ? "MEDIUM" : "LOW"} />
                    <div className="mt-1 truncate text-sm font-medium">{a.type}</div>
                    <div className="text-[11px] text-muted-foreground">{a.cctv} | {a.platform}</div>
                    <div className="text-[11px] text-muted-foreground">{a.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CCTV Summary */}
        <div className="rounded-xl border border-border bg-card">
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
                </tr>
              </thead>
              <tbody>
                {summary.map((row) => (
                  <tr key={row.id} className="border-t border-border transition-colors hover:bg-secondary/40">
                    <td className="px-4 py-3 font-medium">{row.id}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.location}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-md bg-[#22c55e]/15 px-2 py-0.5 text-[11px] font-semibold text-[#22c55e]">Online</span>
                    </td>
                    <td className="px-4 py-3 tabular-nums">{row.incidents}</td>
                    <td className="px-4 py-3 tabular-nums">{row.alerts}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.last}</td>
                    <td className="px-4 py-3">
                      <RiskBadge level={row.risk as never} label={row.risk.toUpperCase()} />
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
  backgroundColor: "#111118",
  border: "1px solid #1e1e2e",
  borderRadius: 8,
  fontSize: 12,
};

function Hotspots({ level }: { level: "high" | "very-high" | "medium" | "low" }) {
  const spots =
    level === "very-high"
      ? [{ x: 25, c: "#ef4444" }, { x: 45, c: "#f97316" }, { x: 60, c: "#ef4444" }, { x: 80, c: "#22c55e" }]
      : level === "high"
      ? [{ x: 30, c: "#f97316" }, { x: 55, c: "#22c55e" }, { x: 75, c: "#22c55e" }]
      : level === "medium"
      ? [{ x: 35, c: "#22c55e" }, { x: 70, c: "#22c55e" }]
      : [{ x: 50, c: "#22c55e" }];
  return (
    <>
      {spots.map((s, i) => (
        <span
          key={i}
          className="absolute top-1/2 h-12 w-12 -translate-y-1/2 rounded-full blur-md opacity-70"
          style={{ left: `${s.x}%`, backgroundColor: s.c }}
        />
      ))}
    </>
  );
}