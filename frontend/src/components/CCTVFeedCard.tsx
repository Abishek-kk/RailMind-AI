import { useState } from "react";
import { Pause, Volume2, Maximize2, Expand } from "lucide-react";
import { toast } from "sonner";
import { riskColor, type BoundingBox, type CCTVFeed } from "@/lib/mock-data";
import { Dialog, DialogContent } from "@/components/ui/dialog";

function levelToColor(level: string) {
  return riskColor(level as never);
}

export function CCTVFeedCard({ feed, detections }: { feed: CCTVFeed; detections?: BoundingBox[] }) {
  const alertColor = feed.riskLevel ? levelToColor(feed.riskLevel) : "#22c55e";
  const boxes = detections ?? [];
  /** BUG 5 FIX: state to open the fullscreen dialog */
  const [fullscreenOpen, setFullscreenOpen] = useState(false);

  /** BUG 5 FIX: handler for Pause and Volume2 — no live stream URL available */
  function handleUnsupportedControl() {
    console.info("pause not supported — no live stream URL");
    toast("Live stream controls are not yet connected.");
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-4 py-3">
        <div>
          <div className="text-sm font-semibold">{feed.id}</div>
          <div className="text-xs text-muted-foreground">{feed.platform}</div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[10px] font-bold ${boxes.length > 0 ? "bg-[#ef4444]/15 text-[#ef4444]" : "bg-[#22c55e]/15 text-[#22c55e]"}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${boxes.length > 0 ? "animate-pulse bg-[#ef4444]" : "bg-[#22c55e]"}`}
          />
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
          {/* BUG 5 FIX: Pause button shows toast */}
          <button
            type="button"
            onClick={handleUnsupportedControl}
            title="Pause (not available — no live stream URL)"
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            <Pause className="h-4 w-4" />
          </button>
          {/* BUG 5 FIX: Volume2 button shows toast */}
          <button
            type="button"
            onClick={handleUnsupportedControl}
            title="Volume (not available — no live stream URL)"
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            <Volume2 className="h-4 w-4" />
          </button>
        </div>
        <div className="flex items-center gap-3">
          {/* BUG 5 FIX: Maximize2 opens fullscreen Dialog */}
          <button
            type="button"
            onClick={() => setFullscreenOpen(true)}
            title="Fullscreen view"
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
          {/* BUG 5 FIX: Expand also opens fullscreen Dialog */}
          <button
            type="button"
            onClick={() => setFullscreenOpen(true)}
            title="Expand view"
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            <Expand className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* BUG 5 FIX: Fullscreen Dialog */}
      <Dialog open={fullscreenOpen} onOpenChange={setFullscreenOpen}>
        <DialogContent className="max-w-5xl p-2">
          <div className="overflow-hidden rounded-lg bg-black">
            <div className="flex items-center justify-between px-4 py-2">
              <span className="text-sm font-semibold text-white">{feed.id} — {feed.platform}</span>
              <span className="inline-flex items-center gap-1.5 rounded-md bg-[#22c55e]/15 px-2 py-0.5 text-[10px] font-bold text-[#22c55e]">
                <span className="h-1.5 w-1.5 rounded-full animate-pulse bg-[#22c55e]" />
                LIVE
              </span>
            </div>
            <img
              src={feed.image}
              alt={`${feed.id} fullscreen`}
              className="w-full object-contain max-h-[80vh]"
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}