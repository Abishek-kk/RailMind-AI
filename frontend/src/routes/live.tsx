import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { CCTVFeedCard } from "@/components/CCTVFeedCard";
import { RiskBadge } from "@/components/RiskBadge";
import { Camera, Users, AlertTriangle, Activity, Plus, ChevronDown, ArrowRight } from "lucide-react";
import { generateAlerts, getLiveFeeds, riskColor } from "@/lib/mock-data";

export const Route = createFileRoute("/live")({
  head: () => ({ meta: [{ title: "Live Monitoring — RailMind AI" }] }),
  component: LivePage,
});

function LivePage() {
  const [feed, setFeed] = useState("all");
  const feeds = useMemo(getLiveFeeds, []);
  const alerts = useMemo(() => generateAlerts(20), []);

  const filteredFeeds = feed === "all" ? feeds : feeds.filter((f) => f.id === feed);
  const filteredAlerts = feed === "all" ? alerts : alerts.filter((a) => a.cctv === feed);

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
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <StatCard label="Total CCTV Feeds" value={feeds.length} sublabel="Active Cameras" icon={Camera} iconColor="#3b82f6" iconBg="rgba(59,130,246,0.15)" />
          <StatCard label="People Detected" value={totalPeople} sublabel="Across All Feeds" icon={Users} iconColor="#22c55e" iconBg="rgba(34,197,94,0.15)" />
          <StatCard label="Active Alerts" value={active} sublabel="Across All Feeds" icon={AlertTriangle} iconColor="#f97316" iconBg="rgba(249,115,22,0.15)" />
          <StatCard label="High Risk Detected" value={highRisk} sublabel="Require Attention" icon={Activity} iconColor="#ef4444" iconBg="rgba(239,68,68,0.15)" />
          <button className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/30 transition-transform hover:scale-[1.02]">
            <Plus className="h-4 w-4" /> Add CCTV Feed
          </button>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {filteredFeeds.map((f) => (
              <CCTVFeedCard key={f.id} feed={f} />
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
              <a className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline" href="/alerts">
                View All Alerts <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}