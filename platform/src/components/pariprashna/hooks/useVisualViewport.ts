'use client'

import { useEffect, useState } from 'react'

export interface VisualViewportMetrics {
  /** Visible viewport height in CSS px, or `null` when the API is unsupported. */
  height: number | null
  /** Distance from the layout viewport's top edge to the visual viewport's top edge — non-zero while the page is scrolled under an open keyboard. */
  offsetTop: number
  supported: boolean
}

function hasVisualViewport(): boolean {
  return typeof window !== 'undefined' && !!window.visualViewport
}

function readMetrics(): VisualViewportMetrics {
  if (!hasVisualViewport()) return { height: null, offsetTop: 0, supported: false }
  const vv = window.visualViewport as VisualViewport
  return { height: vv.height, offsetTop: vv.offsetTop, supported: true }
}

/**
 * §9.2: "Virtual keyboard: composer pins above the keyboard via
 * `visualViewport` tracking (not `100vh` guesses)."
 *
 * `window.visualViewport` (iOS Safari 13+, Chrome/Android, Samsung Internet —
 * every current mobile engine) shrinks to the area actually visible above an
 * open on-screen keyboard. The layout viewport — and therefore a static
 * `100vh`/`100dvh` — does not reliably shrink to match on every engine,
 * which is the exact defect this hook exists to close: a `100vh` shell keeps
 * its full height while the keyboard covers its bottom slice, burying the
 * composer underneath it.
 *
 * Falls back to `supported: false` wherever the API is absent (SSR, jsdom,
 * legacy browsers) — callers use a `100dvh` CSS fallback in that case, never
 * a bare `100vh`.
 */
export function useVisualViewport(): VisualViewportMetrics {
  const [metrics, setMetrics] = useState<VisualViewportMetrics>(readMetrics)

  useEffect(() => {
    if (!hasVisualViewport()) return
    const vv = window.visualViewport as VisualViewport
    const onUpdate = () => setMetrics({ height: vv.height, offsetTop: vv.offsetTop, supported: true })
    onUpdate()
    vv.addEventListener('resize', onUpdate)
    vv.addEventListener('scroll', onUpdate)
    return () => {
      vv.removeEventListener('resize', onUpdate)
      vv.removeEventListener('scroll', onUpdate)
    }
  }, [])

  return metrics
}
