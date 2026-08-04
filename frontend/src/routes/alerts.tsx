import { lazy, Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";

const AlertsPageLazy = lazy(() => import("./alerts.component"));

export const Route = createFileRoute("/alerts")({
  head: () => ({ meta: [{ title: "Alerts — RailMind AI" }] }),
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
          Loading Alerts...
        </div>
      }
    >
      <AlertsPageLazy />
    </Suspense>
  ),
});
