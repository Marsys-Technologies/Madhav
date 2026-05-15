import type { ReactNode } from "react";
import { ConsumeOverlayPortal } from "@/components/consume/ConsumeOverlayPortal";

export default function ConsumeLayout({ children }: { children: ReactNode }) {
  return <ConsumeOverlayPortal>{children}</ConsumeOverlayPortal>;
}
