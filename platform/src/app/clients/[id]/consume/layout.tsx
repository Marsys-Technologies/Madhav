import type { ReactNode } from "react";
import { ConsumeOverlayPortal } from "@/components/consume/ConsumeOverlayPortal";

export default function ConsumeLayout({ children }: { children: ReactNode }) {
  return (
    <>
      {/*
       * Suppress page-ascend animation on <main id="main-content">.
       *
       * Root cause: animation-fill-mode:both starts <main> at opacity:0,
       * which makes <main> a stacking context at z-auto (below z-50).
       * The inline overlay rendered inside <main> is trapped in that lower
       * stacking context, allowing the AppShellRail (z-50 in ROOT) to paint
       * on top. Removing the animation keeps <main> at opacity:1, so <main>
       * does NOT form a stacking context and the overlay competes in ROOT
       * stacking context at z-50 — winning over the rail in DOM order.
       */}
      {/*
       * Two scoped global rules for the consume route:
       * 1. Suppress page-ascend animation on <main> — prevents opacity:0 start
       *    from forming a stacking context below AppShellRail's z-50, which
       *    would trap the inline overlay below the rail.
       * 2. Hide AppShellRail nav — the overlay covers the full viewport; the
       *    rail has the same z-50 as the overlay so both fight for stacking
       *    order. Hiding it eliminates the conflict entirely.
       */}
      <style>{`
        #main-content{animation:none!important}
        nav[aria-label="Primary navigation"]{display:none!important}
      `}</style>
      <ConsumeOverlayPortal>{children}</ConsumeOverlayPortal>
    </>
  );
}
