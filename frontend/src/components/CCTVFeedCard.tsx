import { Pause, Volume2, Maximize2, Expand } from "lucide-react";
import { riskColor, type BoundingBox, type CCTVFeed } from "@/lib/mock-data";

function levelToColor(level: string) {
  return riskColor(level as never);
}

export function CCTVFeedCard({ feed, detections }: { feed: CCTVFeed; detections?: BoundingBox[] }) {
  const alertColor = feed.riskLevel ? levelToColor(feed.riskLevel) : "#22c55e";
  const boxes = detections ?? [];

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-4 py-3">
        <div>
          <div className="text-sm font-semibold">{feed.id}</div>
          <div className="text-xs text-muted-foreground">{feed.platform}</div>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-[#22c55e]/15 px-2 py-0.5 text-[10px] font-bold text-[#22c55e]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e]" />
          LIVE
        </span>
      </div>
      <div className="relative aspect-video overflow-hidden bg-black">
        <img src={feed.image} alt={feed.id} className="h-full w-full object-cover" loading="lazy" />
        {boxes.map((b) => {
          const c = levelToColor(b.level);
          return (
            <div
              key={b.id}
              className="absolute"
              style={{
                left: `${b.x}%`,
                top: `${b.y}%`,
                width: `${b.w}%`,
                height: `${b.h}%`,
                border: `2px solid ${c}`,
                boxShadow: `0 0 0 1px ${c}33`,
              }}
            >
              <span
                className="absolute -top-5 left-0 rounded-sm px-1.5 py-0.5 text-[10px] font-bold text-white"
                style={{ backgroundColor: c }}
              >
                ID: {b.id}
              </span>
            </div>
          );
        })}
        {/* Alert badge bottom-left */}
        {feed.alertType && (
          <div
            className="absolute bottom-3 left-3 rounded-md px-3 py-2 backdrop-blur"
            style={{ backgroundColor: `${alertColor}26`, border: `1px solid ${alertColor}66` }}
          >
            <div className="flex items-center gap-1.5 text-xs font-bold" style={{ color: alertColor }}>
              ⚠ {feed.alertType}
            </div>
            <div className="text-[11px] text-white/90">
              Risk Score: <span className="font-bold" style={{ color: alertColor }}>{feed.riskScore}%</span>
            </div>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between border-t border-border px-3 py-2 text-muted-foreground">
        <div className="flex items-center gap-3">
          <button className="rounded p-1 hover:bg-secondary hover:text-foreground"><Pause className="h-4 w-4" /></button>
          <button className="rounded p-1 hover:bg-secondary hover:text-foreground"><Volume2 className="h-4 w-4" /></button>
        </div>
        <div className="flex items-center gap-3">
          <button className="rounded p-1 hover:bg-secondary hover:text-foreground"><Maximize2 className="h-4 w-4" /></button>
          <button className="rounded p-1 hover:bg-secondary hover:text-foreground"><Expand className="h-4 w-4" /></button>
        </div>
      </div>
    </div>
  );
}