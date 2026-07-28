import type { ReactNode } from 'react'

/**
 * Paripraśna is a full-bleed jet-black instrument surface (Marsys tokens,
 * §6.1) — it supplies its own header/chrome and must not compete with the
 * app shell's primary nav rail or the page-ascend mount animation (the same
 * two suppressions the existing `consult` route layout already applies for
 * its own full-viewport overlay, `src/app/clients/[id]/consult/layout.tsx`
 * — mirrored here, not shared, since this lane must not import from or
 * modify the `consult`/`consume` trees).
 */
export default function PariprashnaLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <style>{`
        #main-content{animation:none!important}
        nav[aria-label="Primary navigation"]{display:none!important}
        body{background-color:#000000!important}
      `}</style>
      {children}
    </>
  )
}
