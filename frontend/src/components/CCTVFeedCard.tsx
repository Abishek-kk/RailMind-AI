import { useState, useEffect, useRef, useCallback } from "react";
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
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const [fullscreenOpen, setFullscreenOpen] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const isActuallyLive = feed.status === "online" && !isPaused;
  const [isMuted, setIsMuted] = useState(true);
  const [frozenBoxes, setFrozenBoxes] = useState<BoundingBox[]>([]);
  const [videoError, setVideoError] = useState(false);

  // Update frozen boxes when not paused
  useEffect(() => {
    if (!isPaused && detections) {
      setFrozenBoxes(detections);
    }
  }, [detections, isPaused]);

  useEffect(() => {
    setVideoError(false);
  }, [feed.streamUrl]);

  // Imperatively control playback — autoPlay only fires once on mount.
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (isPaused) {
      video.pause();
    } else {
      video.play().catch(() => {
        // Autoplay may be blocked by the browser; ignore silently.
      });
    }
  }, [isPaused]);

  // Sync muted state imperatively as well.
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.muted = isMuted;
    }
  }, [isMuted]);

  const activeDetections = isPaused ? frozenBoxes : (detections ?? []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    // Prevent the page from scrolling when the pointer is over the CCTV card.
    // Allow the container itself to scroll if it has overflow; otherwise just
    // consume the wheel event so the outer page doesn't move.
    const el = scrollRef.current;
    if (!el) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    const canScrollVertically = el.scrollHeight > el.clientHeight;
    if (canScrollVertically) {
      // Scroll the container itself.
      e.preventDefault();
      el.scrollTop += e.deltaY;
    } else {
      // Consume the event so the page doesn't scroll.
      e.preventDefault();
      e.stopPropagation();
    }
  }, []);

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
      <div
        ref={scrollRef}
        onWheel={handleWheel}
        className="relative aspect-video overflow-hidden bg-black"
        style={{ overscrollBehavior: "contain" }}
      >
        {feed.streamUrl && !videoError ? (
          <video
            ref={videoRef}
            src={feed.streamUrl}
            autoPlay={!isPaused}
            muted={isMuted}
            loop
            controls={false}
            className="h-full w-full object-cover"
            playsInline
            onError={() => setVideoError(true)}
            onCanPlay={() => {
              setVideoError(false);
              try {
                videoRef.current?.play();
              } catch {}
            }}
            onLoadedData={(e) => {
              setVideoError(false);
              try {
                (e.currentTarget as HTMLVideoElement).play();
              } catch {}
            }}
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
            <div
              className="relative w-full bg-black max-h-[80vh] overflow-hidden"
              onWheel={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              style={{ overscrollBehavior: "contain" }}
            >
              {feed.streamUrl && !videoError ? (
                <video
                  src={feed.streamUrl}
                  autoPlay={!isPaused}
                  muted={isMuted}
                  loop
                  controls
                  className="w-full max-h-[80vh] object-contain"
                  playsInline
                  onError={() => setVideoError(true)}
                  onCanPlay={() => {
                    setVideoError(false);
                    // attempt to play the fullscreen video element
                    try {
                      const els = document.getElementsByTagName('video');
                      for (const el of Array.from(els)) {
                        if (el.src === feed.streamUrl) {
                          el.play().catch(() => {});
                        }
                      }
                    } catch {}
                  }}
                  onLoadedData={(e) => {
                    setVideoError(false);
                    try {
                      (e.currentTarget as HTMLVideoElement).play().catch(() => {});
                    } catch {}
                  }}
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
