import { useMemo, useState, type ReactNode } from "react";

import { SidebarContext, type SidebarContextValue } from "./sidebar-context-utils";

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const value = useMemo<SidebarContextValue>(
    () => ({
      isOpen,
      toggle: () => setIsOpen((current) => !current),
      open: () => setIsOpen(true),
      close: () => setIsOpen(false),
    }),
    [isOpen],
  );

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
}
