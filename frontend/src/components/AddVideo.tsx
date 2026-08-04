import React, { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { uploadVideo } from "@/lib/api/feeds";

export default function AddVideo() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const onClick = () => {
    inputRef.current?.click();
  };

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStatus("Uploading...");
    try {
      const res = await uploadVideo(file);
      setStatus(`Uploaded: ${res.id ?? res.feed_id ?? file.name}`);
      queryClient.invalidateQueries({ queryKey: ["liveFeeds"] });
      queryClient.invalidateQueries({ queryKey: ["dashboardStats"] });
      queryClient.invalidateQueries({ queryKey: ["cctvSummary"] });
      queryClient.invalidateQueries({ queryKey: ["incidentsByCCTV"] });
      queryClient.invalidateQueries({ queryKey: ["recentIncidents"] });
      queryClient.invalidateQueries({ queryKey: ["platformHeatmap"] });
      queryClient.invalidateQueries({ queryKey: ["riskDistribution"] });
      queryClient.invalidateQueries({ queryKey: ["peakHours"] });
      queryClient.invalidateQueries({ queryKey: ["incidentTrend"] });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setStatus(`Error: ${message}`);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input ref={inputRef} type="file" accept="video/*" onChange={onChange} className="hidden" />
      <button
        type="button"
        onClick={onClick}
        className="inline-flex h-10 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm font-medium text-muted-foreground transition hover:bg-secondary hover:text-foreground"
      >
        <Upload className="h-4 w-4" />
        Add Video
      </button>
      {status && <span className="max-w-40 truncate text-xs text-muted-foreground">{status}</span>}
    </div>
  );
}
