import { useState, useEffect, useRef } from "react";
import { Pause, Play, Maximize2, Volume2, VolumeX, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { riskColor, type BoundingBox, type CCTVFeed } from "@/lib/mock-data";
import { Dialog, DialogContent } from "@/components/ui/dialog";

function levelToColor(level: string) {
  return riskColor(level as never);
}

export function CCTVFeedCard({ feed, detections, onRemove, removing }: { feed: CCTVFeed; detections?: BoundingBox[]; onRemove?: (feedId: string) => void; removing?: boolean }) {
  const alertColor = feed.riskLevel ? levelToColor(feed.riskLevel) : "#22c55e";
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [fullscreenOpen, setFullscreenOpen] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const isActuallyLive = feed.status === "online" && !isPaused;
  const [isMuted, setIsMuted] = useState(false);
  const [frozenBoxes, setFrozenBoxes] = useState<BoundingBox[]>([]);

  // Update frozen boxes when not paused
  useEffect(() => {
    if (!isPaused && detections) {
      setFrozenBoxes(detections);
    }
  }, [detections, isPaused]);

  const activeDetections = isPaused ? frozenBoxes : (detections ?? []);

  function handlePlayPauseToggle() {
    setIsPaused(!isPaused);
    toast(isPaused ? "Live feed resumed." : "Live feed paused.");
  }

  function handleMuteToggle() {
    setIsMuted((current) => !current);
    toast(isMuted ? "Audio unmuted." : "Audio muted.");
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-4 py-3">
        <div>
          <div className="text-sm font-semibold">{feed.id}</div>
          <div className="text-xs text-muted-foreground">{feed.platform}</div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[10px] font-bold ${activeDetections.length > 0 && isActuallyLive ? "bg-[#ef4444]/15 text-[#ef4444]" : isActuallyLive ? "bg-[#22c55e]/15 text-[#22c55e]" : "bg-[#64748b]/15 text-[#64748b]"}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${activeDetections.length > 0 && isActuallyLive ? "animate-pulse bg-[#ef4444]" : isActuallyLive ? "bg-[#22c55e]" : "bg-[#64748b]"}`}
          />
          {isActuallyLive ? "LIVE" : isPaused ? "PAUSED" : "OFFLINE"}
        </span>
      </div>
      <div className="relative aspect-video overflow-hidden bg-black">
        {feed.streamUrl ? (
          <video
            ref={videoRef}
            src={feed.streamUrl}
            autoPlay={!isPaused}
            muted={isMuted}
            controls={false}
            className="h-full w-full object-cover"
            playsInline
          />
        ) : (
          <img
            src={feed.image}
            alt={feed.id}
            className={`h-full w-full object-cover transition-opacity duration-300 ${isPaused ? "opacity-60" : "opacity-100"}`}
            loading="lazy"
          />
        )}
        {isPaused && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <span className="rounded bg-black/60 px-3 py-1.5 text-xs font-bold text-white tracking-wider animate-pulse">
              PAUSED
            </span>
          </div>
        )}
        {activeDetections.map((b) => {
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
            <div
              className="flex items-center gap-1.5 text-xs font-bold"
              style={{ color: alertColor }}
            >
              ⚠ {feed.alertType}
            </div>
            <div className="text-[11px] text-white/90">
              Risk Score:{" "}
              <span className="font-bold" style={{ color: alertColor }}>
                {feed.riskScore}%
              </span>
            </div>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between border-t border-border px-3 py-2 text-muted-foreground">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handlePlayPauseToggle}
            title={isPaused ? "Play" : "Pause"}
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={handleMuteToggle}
            title={isMuted ? "Unmute" : "Mute"}
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </button>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setFullscreenOpen(true)}
            title="Fullscreen view"
            className="rounded p-1 hover:bg-secondary hover:text-foreground"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
          {onRemove ? (
            <button
              type="button"
              onClick={() => onRemove(feed.id)}
              disabled={removing}
              title="Remove feed"
              className="rounded p-1 hover:bg-secondary hover:text-foreground disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </div>

      {/* Fullscreen Dialog */}
      <Dialog open={fullscreenOpen} onOpenChange={setFullscreenOpen}>
        <DialogContent className="max-w-5xl p-2">
          <div className="overflow-hidden rounded-lg bg-black">
            <div className="flex items-center justify-between px-4 py-2">
              <span className="text-sm font-semibold text-white">
                {feed.id} — {feed.platform}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-md bg-[#22c55e]/15 px-2 py-0.5 text-[10px] font-bold text-[#22c55e]">
                <span className="h-1.5 w-1.5 rounded-full animate-pulse bg-[#22c55e]" />
                LIVE
              </span>
            </div>
            <div className="relative w-full bg-black max-h-[80vh] overflow-hidden">
              {feed.streamUrl ? (
                <video
                  src={feed.streamUrl}
                  autoPlay={!isPaused}
                  muted={isMuted}
                  controls
                  className="w-full max-h-[80vh] object-contain"
                  playsInline
                />
              ) : (
                <img
                  src={feed.image}
                  alt={`${feed.id} fullscreen`}
                  className="w-full object-contain"
                />
              )}
              {/* Render bounding boxes on fullscreen image */}
              {activeDetections.map((b) => {
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
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
