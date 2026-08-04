import { lazy, Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";

const DashboardPageLazy = lazy(() => import("./dashboard.component"));

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — RailMind AI" }] }),
  component: () => (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
          Loading Dashboard...
        </div>
      }
    >
      <DashboardPageLazy />
    </Suspense>
  ),
});
