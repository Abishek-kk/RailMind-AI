import { useEffect, useState } from "react";
import { Calendar, Clock, Camera, ChevronDown, Check } from "lucide-react";
import { CCTV_OPTIONS } from "@/lib/mock-data";

interface TopBarProps {
  title: string;
  subtitle: string;
  selectedFeed: string;
  onFeedChange: (id: string) => void;
  right?: React.ReactNode;
}

export function TopBar({ title, subtitle, selectedFeed, onFeedChange, right }: TopBarProps) {
  const [now, setNow] = useState(new Date());
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const date = now.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  const time = now.toLocaleTimeString("en-US", { hour12: true });
  const current = CCTV_OPTIONS.find((c) => c.id === selectedFeed) ?? CCTV_OPTIONS[0];

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
              {CCTV_OPTIONS.map((opt) => (
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
        {right}
      </div>
    </header>
  );
}