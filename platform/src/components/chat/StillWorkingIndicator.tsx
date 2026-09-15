'use client'

import { useEffect, useState } from 'react'

interface StillWorkingIndicatorProps {
  isStreaming: boolean
  thresholdMs?: number
}

/**
 * X-S4: "Still working…" indicator shown after thresholdMs (default 25s) of
 * continuous streaming. Disappears when streaming ends.
 * Accessible: aria-live="polite" so screen readers announce appearance.
 */
export function StillWorkingIndicator({
  isStreaming,
  thresholdMs = 25_000,
}: StillWorkingIndicatorProps) {
  if (!isStreaming) return null
  return <ActiveStillWorkingIndicator thresholdMs={thresholdMs} />
}

function ActiveStillWorkingIndicator({ thresholdMs }: { thresholdMs: number }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const start = Date.now()
    const id = setInterval(() => {
      setElapsed(Date.now() - start)
    }, 1_000)
    return () => clearInterval(id)
  }, [])

  if (elapsed < thresholdMs) return null

  const seconds = Math.floor(elapsed / 1000)

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="flex items-center gap-2 py-1 text-[11px] text-zinc-500"
      data-testid="v2-still-working"
    >
      <span className="inline-flex gap-0.5">
        <span className="animate-bounce [animation-delay:0ms]">·</span>
        <span className="animate-bounce [animation-delay:150ms]">·</span>
        <span className="animate-bounce [animation-delay:300ms]">·</span>
      </span>
      <span>Still working… ({seconds}s)</span>
    </div>
  )
}
