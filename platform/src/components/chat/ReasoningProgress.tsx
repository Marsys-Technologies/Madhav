'use client'

/**
 * ReasoningProgress — γ2 + Y-S4
 *
 * Collapsible reasoning drawer with live token count + elapsed-time-in-thought.
 * - Elapsed timer starts on first reasoning character; stops when streaming ends.
 * - Auto-collapses when reasoning text exceeds COLLAPSE_THRESHOLD tokens at end of stream.
 * - < COLLAPSE_THRESHOLD: defaults to expanded.
 * - ≥ COLLAPSE_THRESHOLD: defaults to collapsed with a "Show N tokens of reasoning" affordance.
 *
 * Y-S4: When MARSYS_FLAG_R10_REASONING_STEPS is enabled, the component also
 * renders a left-margin step timeline by parsing ### Step: <label> lines from
 * the streaming reasoning text. Active step pulses; completed steps show ✓.
 *
 * The component is mounted as the `Reasoning` renderer inside MessagePrimitive.Parts.
 * It calls useMessagePartReasoning() for live status; the caller passes `text` as a prop.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { useMessagePartReasoning } from '@assistant-ui/react'

/** Approx tokens: Claude tokenizer averages ~4 chars/token. */
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

const COLLAPSE_THRESHOLD = 2000 // tokens

const STEP_RX = /^### Step: (.+)$/m

/** Parse all completed ### Step: <label> lines from reasoning text. */
function parseStepLabels(text: string): string[] {
  const lines = text.split('\n')
  const steps: string[] = []
  for (const line of lines) {
    const m = line.match(/^### Step: (.+)$/)
    if (m) steps.push(m[1].trim())
  }
  return steps
}

interface ReasoningProgressProps {
  /** The full accumulated reasoning text (from MessagePrimitive.Parts Reasoning renderer). */
  text: string
  /**
   * C-S3: Whether the first text_delta has arrived for this message.
   * When this flips false → true, the reasoning block auto-collapses (unless the
   * user has manually toggled it during this message lifetime).
   *
   * Sources:
   *   - Anthropic: first text content block delta
   *   - Gemini: first text part in the UIMessage
   *   - DeepSeek: first text part after extractReasoningMiddleware extraction
   */
  hasFirstTextDelta?: boolean
  'data-testid'?: string
}

export function ReasoningProgress({ text, hasFirstTextDelta = false, 'data-testid': testId }: ReasoningProgressProps) {
  const { status } = useMessagePartReasoning()
  const isStreaming = status.type === 'running'

  const tokenCount = useMemo(() => estimateTokens(text), [text])
  const isLong = tokenCount >= COLLAPSE_THRESHOLD

  // Collapsed state: starts expanded if short, starts collapsed if long.
  // On mobile viewports (<768px), defaults to collapsed regardless of length.
  const [collapsed, setCollapsed] = useState(false)
  const hasAutoCollapsed = useRef(false)
  /**
   * C-S3: Track whether the user has manually toggled within this message
   * lifetime. When true, the auto-collapse heuristics (token count + first
   * text_delta) are suppressed so user intent is preserved.
   */
  const userHasToggled = useRef(false)

  const handleToggle = () => {
    userHasToggled.current = true
    setCollapsed((c) => !c)
  }

  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 768) {
      setCollapsed(true)
    }
  }, [])
  const wasStreaming = useRef(isStreaming)

  // Auto-collapse at end of stream if text is long (only fires once)
  useEffect(() => {
    if (wasStreaming.current && !isStreaming && isLong && !hasAutoCollapsed.current && !userHasToggled.current) {
      hasAutoCollapsed.current = true
      setCollapsed(true)
    }
    wasStreaming.current = isStreaming
  }, [isStreaming, isLong])

  /**
   * C-S3: Auto-collapse when first text_delta arrives.
   * This fires when the model transitions from "thinking" to "writing", which
   * is the natural moment to collapse the reasoning block so the user's
   * attention shifts to the response text.
   *
   * Suppressed if:
   *   - User has manually toggled (userHasToggled.current)
   *   - Already auto-collapsed by the end-of-stream heuristic
   */
  const prevHasFirstTextDelta = useRef(hasFirstTextDelta)
  useEffect(() => {
    const flipped = !prevHasFirstTextDelta.current && hasFirstTextDelta
    prevHasFirstTextDelta.current = hasFirstTextDelta
    if (flipped && !userHasToggled.current && !hasAutoCollapsed.current) {
      hasAutoCollapsed.current = true
      setCollapsed(true)
    }
  }, [hasFirstTextDelta])

  // Elapsed timer — counts seconds while streaming, freezes on stop.
  const startRef = useRef<number | null>(null)
  const [elapsedMs, setElapsedMs] = useState(0)

  useEffect(() => {
    if (text.length > 0 && startRef.current === null) {
      startRef.current = Date.now()
    }
  }, [text])

  useEffect(() => {
    if (!isStreaming || startRef.current === null) return
    const id = setInterval(() => {
      setElapsedMs(Date.now() - (startRef.current ?? Date.now()))
    }, 200)
    return () => clearInterval(id)
  }, [isStreaming])

  // Freeze elapsed at stream end
  useEffect(() => {
    if (!isStreaming && startRef.current !== null) {
      setElapsedMs(Date.now() - startRef.current)
    }
  }, [isStreaming])

  const elapsedSec = (elapsedMs / 1000).toFixed(1)
  const collapseLabel = `Show ${tokenCount.toLocaleString()} tokens of reasoning`

  // Y-S4: Parse step labels from streaming text.
  // The server-side R10_REASONING_STEPS flag controls whether the synthesis prompt
  // emits ### Step: markers. This component just renders whatever arrives.
  const stepLabels = useMemo(() => parseStepLabels(text), [text])

  void STEP_RX // referenced by parseStepLabels; silence lint

  return (
    <div
      className="rounded-lg border border-zinc-700 bg-zinc-900/60 overflow-hidden"
      data-testid={testId ?? 'reasoning-progress'}
    >
      {/* Header */}
      <button
        type="button"
        onClick={handleToggle}
        className="flex w-full items-center justify-between px-4 py-2 text-xs text-zinc-400 hover:bg-zinc-800/40 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-500"
        aria-expanded={!collapsed}
        aria-controls="reasoning-content"
        data-testid="reasoning-toggle"
      >
        <span className="flex items-center gap-2">
          {/* Pulsing dot while streaming */}
          {isStreaming && (
            <span
              className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse"
              aria-label="streaming"
              data-testid="reasoning-streaming-dot"
            />
          )}
          <span className="font-semibold text-violet-300" data-testid="reasoning-header-label">
            {isStreaming ? 'Thinking…' : 'Reasoning'}
          </span>
          <span className="text-zinc-600" data-testid="reasoning-token-count">
            {tokenCount.toLocaleString()} tokens
          </span>
          {(isStreaming || elapsedMs > 0) && (
            <span className="text-zinc-600" data-testid="reasoning-elapsed">
              {elapsedSec}s
            </span>
          )}
        </span>

        {/* Chevron */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className={`h-3 w-3 transition-transform ${collapsed ? '' : 'rotate-180'}`}
          aria-hidden="true"
        >
          <path d="M2 4l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* Collapsed affordance label */}
      {collapsed && isLong && (
        <div
          className="px-4 py-1 text-[10px] text-zinc-600 italic cursor-pointer hover:text-zinc-500"
          onClick={() => setCollapsed(false)}
          aria-hidden="true"
          data-testid="reasoning-collapse-label"
        >
          {collapseLabel} ⌄
        </div>
      )}

      {/* Content */}
      {!collapsed && (
        <div
          id="reasoning-content"
          className="border-t border-zinc-800"
          data-testid="reasoning-content"
        >
          {/* Y-S4: left-margin step timeline */}
          {stepLabels.length > 0 && (
            <div
              className="flex gap-3 px-4 pt-3 pb-2"
              data-testid="v2-reasoning-step-timeline"
            >
              {/* Vertical connector line */}
              <div className="relative flex flex-col items-center" aria-hidden="true">
                <div className="absolute top-2 bottom-2 left-1/2 -translate-x-1/2 w-px bg-zinc-700" />
              </div>
              {/* Step list */}
              <ol className="space-y-2 text-[11px] relative z-10">
                {stepLabels.map((label, i) => {
                  const isActive = isStreaming && i === stepLabels.length - 1
                  const isDone = !isActive
                  return (
                    <li
                      key={i}
                      className="flex items-center gap-2"
                      data-testid={`v2-reasoning-step-${i}`}
                    >
                      {/* Tick mark */}
                      <span
                        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[9px] ${
                          isActive
                            ? 'border-violet-500 bg-violet-900/60 text-violet-300 animate-pulse'
                            : isDone
                            ? 'border-zinc-600 bg-zinc-800 text-zinc-400'
                            : 'border-zinc-700 bg-transparent text-zinc-600'
                        }`}
                        data-testid={isActive ? 'v2-step-active-indicator' : isDone ? 'v2-step-done-indicator' : 'v2-step-pending-indicator'}
                        aria-label={isActive ? 'active' : 'completed'}
                      >
                        {isActive ? '·' : '✓'}
                      </span>
                      {/* Label */}
                      <span
                        className={isActive ? 'text-violet-300 font-medium' : 'text-zinc-500'}
                      >
                        {label}
                      </span>
                    </li>
                  )
                })}
              </ol>
            </div>
          )}

          {/* Reasoning text */}
          <div
            className="px-4 pb-3 pt-0 text-xs font-mono text-zinc-400 whitespace-pre-wrap leading-relaxed"
            aria-live={isStreaming ? 'polite' : undefined}
          >
            {text}
          </div>
        </div>
      )}
    </div>
  )
}
