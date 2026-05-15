import type { ReactNode } from "react";
import { ZoneRoot } from "@/components/shared/ZoneRoot";

export default function ConsumeLayout({ children }: { children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-[oklch(0.07_0.010_70)]">
      <ZoneRoot zone="ink" style={{ height: "100%" }}>
        {children}
      </ZoneRoot>
    </div>
  );
}
