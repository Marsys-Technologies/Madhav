'use client'

import { useEffect, useRef, useState } from 'react'
import type { TurnState } from '../state/types'
// S-2's canonical closed vocabulary (PB-1/integrate — replaced the C-1 stand-in).
import { renderSealCompleteLabel } from '@/lib/pariprashna/lexicon'

function formatElapsed(totalSeconds: number): string {
  const s = Math.max(0, totalSeconds)
  return `0:${String(s).padStart(2, '0')}`
}

/**
 * Client clock derived from `openedAtMs` — never round-trips through the
 * reducer (§8.5). A 1s-resolution "calm clock, not a stopwatch" (§5.3): the
 * interval only runs while `running`; once the turn settles, the last tick
 * it wrote simply stops being updated (frozen final elapsed), which is why
 * this holds no `else` branch that recomputes from `Date.now()` — that
 * would make a settled turn's displayed time drift upward forever.
 */
function useElapsedSeconds(openedAtMs: number, running: boolean): number {
  const [tickSeconds, setTickSeconds] = useState(() => Math.floor((Date.now() - openedAtMs) / 1000))
  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setTickSeconds(Math.floor((Date.now() - openedAtMs) / 1000)), 1000)
    return () => clearInterval(id)
  }, [openedAtMs, running])
  return tickSeconds
}

function currentLiveLabel(turn: TurnState): string {
  if (turn.activeSeam) return turn.activeSeam.liveLabel
  const runningActivity = [...turn.activities].reverse().find((a) => a.status === 'running')
  if (runningActivity) return runningActivity.label
  return turn.phaseLabel
}

const BAND_ANNOUNCE_THROTTLE_MS = 5000

/**
 * §9.3: "Working-band label changes announce via a separate throttled
 * polite region (≥ 5 s between announcements)." The VISUAL label
 * (`.pp-band-label`) updates on every event — that's fine, sighted readers
 * see a text swap, no announcement implied. A screen reader's aria-live
 * region is different: announcing every intermediate label ("Checking the
 * ninth house…", "Cross-referencing daśā…", …) as they arrive several
 * times a second would bury the user in noise. This hook holds back
 * updates to at most one per `BAND_ANNOUNCE_THROTTLE_MS`, always
 * eventually landing on the latest text (never stale, never silent).
 */
function useThrottledAnnouncement(text: string, minIntervalMs: number): string {
  const [announced, setAnnounced] = useState(text)
  const lastAtRef = useRef<number>(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const now = Date.now()
    const elapsed = now - lastAtRef.current
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (elapsed >= minIntervalMs) {
      lastAtRef.current = now
      setAnnounced(text)
    } else {
      timeoutRef.current = setTimeout(() => {
        lastAtRef.current = Date.now()
        setAnnounced(text)
        timeoutRef.current = null
      }, minIntervalMs - elapsed)
    }
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [text, minIntervalMs])

  return announced
}

export interface WorkingBandProps {
  turn: TurnState
  expanded: boolean
  onToggle: () => void
}

/**
 * The stable band (§5.1, §6.5): fixed 40px height, full column width. Label
 * is a text-swap only — the box height never changes, whether resting,
 * thinking, or settled. Glyph + counter + chevron sit either side.
 */
export function WorkingBand({ turn, expanded, onToggle }: WorkingBandProps) {
  const isActive = turn.status === 'thinking' || turn.status === 'streaming' || turn.status === 'submitted' || turn.status === 'reconnecting'
  const elapsed = useElapsedSeconds(turn.openedAtMs, isActive)

  // Plain-text twin of the visual label below, for the throttled aria-live
  // region — the JSX label carries markup (a <b>, a dimmed trailing span)
  // that has no place in an announcement string.
  const sealedLabelText = renderSealCompleteLabel((turn.grounding?.factorCount ?? 0) + (turn.grounding?.classicalCount ?? 0), elapsed)
  let announceText: string
  let label: React.ReactNode
  if (turn.status === 'errored' && turn.error) {
    announceText = turn.error.bandLabel
    label = turn.error.bandLabel
  } else if (turn.status === 'interrupted') {
    announceText = 'Stopped — kept what arrived'
    label = 'Stopped — kept what arrived'
  } else if (turn.status === 'settled' || turn.status === 'settling') {
    // S-2's sealed-band label: "Grounded in N sources · Ts" (N = chart factors
    // + classical sources; elapsed is the numeric client-clock seconds).
    announceText = sealedLabelText
    label = <b>{sealedLabelText}</b>
  } else if (turn.status === 'reconnecting') {
    announceText = `${currentLiveLabel(turn)} — reconnecting…`
    label = <>{currentLiveLabel(turn)}<span style={{ color: 'var(--pp-gold-tertiary)' }}> — reconnecting…</span></>
  } else {
    announceText = `${currentLiveLabel(turn)}…`
    label = <>{currentLiveLabel(turn)}<span style={{ color: 'var(--pp-gold-tertiary)' }}>…</span></>
  }

  const throttledAnnouncement = useThrottledAnnouncement(announceText, BAND_ANNOUNCE_THROTTLE_MS)
  const settled = turn.status === 'settled' || turn.status === 'settling'

  return (
    <div
      className="pp-band"
      role="button"
      tabIndex={0}
      aria-expanded={expanded}
      onClick={onToggle}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onToggle()
        }
      }}
    >
      {settled ? (
        <span aria-hidden className="flex-none text-[13px]" style={{ color: 'var(--pp-gold)' }}>
          ✓
        </span>
      ) : (
        <span
          aria-hidden
          data-pp-spin
          className="flex-none inline-block w-[13px] h-[13px] rounded-full"
          style={{ border: '1.5px solid var(--pp-gold-tertiary)', borderTopColor: 'var(--pp-gold)' }}
        />
      )}
      <span
        className="pp-band-label"
        data-pp-breathe={settled ? undefined : true}
        aria-live="off"
      >
        {label}
      </span>
      {/* §9.3: elapsed-counter ticks are `aria-hidden` — a screen reader
          must never hear "0:01… 0:02… 0:03…" once a second. */}
      <span aria-hidden data-testid="pp-band-elapsed" className="font-mono text-[11px] flex-none" style={{ color: 'var(--pp-gold-dim)' }}>
        {formatElapsed(elapsed)}
      </span>
      <span
        aria-hidden
        className="flex-none text-[12px] transition-transform"
        style={{ color: 'var(--pp-gold-tertiary)', transform: expanded ? 'rotate(180deg)' : undefined, transitionDuration: '200ms' }}
      >
        ▾
      </span>
      {/* §9.3: "Working-band label changes announce via a separate
          throttled polite region (≥5s between announcements)." Visually
          hidden — the visible `.pp-band-label` above is `aria-live="off"`
          by design (it swaps too often to announce every change); this is
          the one channel that actually reaches assistive tech, holding
          back to at most one announcement per 5s. */}
      <span className="sr-only" role="status" aria-live="polite">
        {throttledAnnouncement}
      </span>
    </div>
  )
}
