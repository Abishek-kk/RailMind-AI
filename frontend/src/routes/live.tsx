import { lazy, Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";

const LivePageLazy = lazy(() => import("./live.component"));

export const Route = createFileRoute("/live")({
  head: () => ({ meta: [{ title: "Live Monitoring — RailMind AI" }] }),
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
          Loading Live Monitoring...
        </div>
      }
    >
      <LivePageLazy />
    </Suspense>
  ),
});
