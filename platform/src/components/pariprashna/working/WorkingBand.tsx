'use client'

import { useEffect, useState } from 'react'
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

  let label: React.ReactNode
  if (turn.status === 'errored' && turn.error) {
    label = turn.error.bandLabel
  } else if (turn.status === 'interrupted') {
    label = 'Stopped — kept what arrived'
  } else if (turn.status === 'settled' || turn.status === 'settling') {
    // S-2's sealed-band label: "Grounded in N sources · Ts" (N = chart factors
    // + classical sources; elapsed is the numeric client-clock seconds).
    label = <b>{renderSealCompleteLabel((turn.grounding?.factorCount ?? 0) + (turn.grounding?.classicalCount ?? 0), elapsed)}</b>
  } else if (turn.status === 'reconnecting') {
    label = <>{currentLiveLabel(turn)}<span style={{ color: 'var(--pp-gold-tertiary)' }}> — reconnecting…</span></>
  } else {
    label = <>{currentLiveLabel(turn)}<span style={{ color: 'var(--pp-gold-tertiary)' }}>…</span></>
  }

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
      <span className="font-mono text-[11px] flex-none" style={{ color: 'var(--pp-gold-dim)' }}>
        {formatElapsed(elapsed)}
      </span>
      <span
        aria-hidden
        className="flex-none text-[12px] transition-transform"
        style={{ color: 'var(--pp-gold-tertiary)', transform: expanded ? 'rotate(180deg)' : undefined, transitionDuration: '200ms' }}
      >
        ▾
      </span>
    </div>
  )
}
