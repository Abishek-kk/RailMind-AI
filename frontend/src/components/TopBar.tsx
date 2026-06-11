import { useEffect, useState, type ReactNode } from "react";
import { Bell, BellOff, Calendar, Clock, Camera, ChevronDown, Check } from "lucide-react";

interface TopBarProps {
  title: string;
  subtitle: string;
  selectedFeed: string;
  onFeedChange: (id: string) => void;
  soundEnabled?: boolean;
  onSoundToggle?: () => void;
  right?: ReactNode;
  /**
   * BUG 12 FIX: Optional dynamic feeds list. When provided, replaces the
   * static CCTV_OPTIONS. "All CCTV Feeds" is always prepended automatically.
   */
  feeds?: Array<{ id: string; label: string }>;
}

export function TopBar({ title, subtitle, selectedFeed, onFeedChange, soundEnabled = false, onSoundToggle, right, feeds }: TopBarProps) {
  const [now, setNow] = useState(new Date());
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const date = now.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  const time = now.toLocaleTimeString("en-US", { hour12: true });

  /**
   * BUG 13 FIX: Use dynamic feeds when provided, always prepend "All CCTV Feeds".
   * When feeds is undefined (loading), show only a single "All CCTV Feeds" option
   * instead of the stale CCTV_OPTIONS to avoid flashing outdated camera data.
   */
  const feedOptions = feeds
    ? [{ id: "all", label: "All CCTV Feeds" }, ...feeds]
    : [{ id: "all", label: "All CCTV Feeds" }];

  const current = feedOptions.find((c) => c.id === selectedFeed) ?? feedOptions[0];

  return (
    <header className="flex items-center justify-between gap-4 border-b border-border bg-background px-8 py-5">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span>{date}</span>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm tabular-nums">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span>{time}</span>
        </div>
        <div className="relative">
          <button
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm transition-colors hover:bg-secondary"
          >
            <Camera className="h-4 w-4 text-muted-foreground" />
            <span>{current.label}</span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>
          {open && (
            <div className="absolute right-0 top-full z-50 mt-2 w-60 overflow-hidden rounded-lg border border-border bg-popover shadow-xl">
              {feedOptions.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => {
                    onFeedChange(opt.id);
                    setOpen(false);
                  }}
                  className="flex w-full items-center justify-between px-4 py-2.5 text-sm transition-colors hover:bg-secondary"
                >
                  <span>{opt.label}</span>
                  {opt.id === selectedFeed && <Check className="h-4 w-4 text-[#22c55e]" />}
                </button>
              ))}
            </div>
          )}
        </div>
        {onSoundToggle ? (
          <button
            type="button"
            onClick={onSoundToggle}
            aria-pressed={soundEnabled}
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground transition hover:bg-secondary"
          >
            {soundEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
          </button>
        ) : null}
        {right}
      </div>
    </header>
  );
}