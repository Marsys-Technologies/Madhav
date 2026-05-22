'use client'

/**
 * PreTokenIndicator — "Thinking… Ns" affordance for the pre-first-text-delta gap.
 *
 * Renders an animated dot + optional elapsed counter beneath the user's message
 * while the assistant is streaming but no text_delta has arrived yet.
 *
 * - Thinking-capable providers (Anthropic/Google/DeepSeek): shows "Thinking… {N}s"
 * - Other providers: shows only the animated dot
 * - Unmounts immediately when hasFirstTextDelta becomes true
 *
 * A11y: role="status" aria-live="polite" so screen readers announce the wait.
 *
 * C-S1: R11.C streaming + thinking indicator.
 */

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

export interface PreTokenIndicatorProps {
  /**
   * Whether the parent message has received its first text_delta.
   * When true, this component should NOT be rendered (caller is responsible
   * for conditional rendering, but the component also gates itself internally
   * so it's safe to always mount when isStreaming=true).
   */
  hasFirstTextDelta: boolean
  /**
   * Whether the provider supports extended thinking (any variant).
   * When true, shows "Thinking… {N}s"; when false, shows only the dot.
   */
  hasThinking: boolean
  /** Optional className for the wrapper div. */
  className?: string
}

/**
 * Typical pre-first-delta wait times by provider (for documentation):
 * - Anthropic (Sonnet 4.6 thinking): 1–8s (effort=low) / 5–30s (effort=high)
 * - Google (Gemini 2.5 Pro thinking): 2–15s
 * - DeepSeek: 3–20s (inline <think> blocks)
 * - OpenAI / NVIDIA: 0.5–3s (no thinking; pre-stream network latency only)
 */
export function PreTokenIndicator({
  hasFirstTextDelta,
  hasThinking,
  className,
}: PreTokenIndicatorProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const startRef = useRef<number>(Date.now())
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    // Reset timer when component mounts (new streaming turn)
    startRef.current = Date.now()
    setElapsedSeconds(0)

    intervalRef.current = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startRef.current) / 1000))
    }, 1000)

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [])

  // Gate: once first text_delta arrives, render nothing
  if (hasFirstTextDelta) return null

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={hasThinking ? `Thinking, ${elapsedSeconds} seconds` : 'Waiting for response'}
      className={cn('flex items-center gap-1.5 py-2 text-xs text-muted-foreground/60', className)}
    >
      {/* Animated dot */}
      <span
        aria-hidden="true"
        className="inline-block size-1.5 rounded-full bg-current animate-[pre-token-pulse_1.2s_ease-in-out_infinite]"
      />
      {hasThinking && (
        <span>
          Thinking
          {elapsedSeconds > 0 && (
            <span aria-hidden="true">… {elapsedSeconds}s</span>
          )}
          {elapsedSeconds === 0 && (
            <span aria-hidden="true">…</span>
          )}
        </span>
      )}
    </div>
  )
}
