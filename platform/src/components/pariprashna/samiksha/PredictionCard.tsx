/**
 * PredictionCard — the signature dock component — PB-3 lane L-2.
 *
 * Design authority: PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §6.9 + AC-16.
 *
 * Settled block (§6.9), top → bottom:
 *   1. Eyebrow — `TIME-INDEXED READING` + lifecycle suffix (the ONLY element
 *      that changes after settle; in-place text swap at fixed geometry, P1).
 *   2. Claim — Cormorant (the chart's voice is serif; §6.2).
 *   3. The kāla-rekhā — the time hairline whose geometry IS the calendar (AC-16).
 *
 * Lives in the collapsible right dock (§10.3 "the right dock"): the prediction
 * card + kāla-rekhā dock right rather than mount inline in the prose column.
 */

'use client'

import { KalaRekha } from './KalaRekha'
import { lifecycleEyebrow } from '@/lib/pariprashna/samiksha/lifecycle_label'
import type { LifecycleState, Outcome } from '@/lib/pariprashna/samiksha/schema'

export interface PredictionCardProps {
  claimText: string
  lifecycleStatus: LifecycleState
  outcome?: Outcome | null
  /** Near-window-end signal (derived, not a lifecycle state) → `WINDOW CLOSING`. */
  closingSoon?: boolean
  /** kāla-rekhā anchors — omit the trio to render the card without a timeline
   *  (e.g. a claim with no resolvable window). ISO yyyy-mm-dd. */
  readingDate?: string
  windowStart?: string | null
  windowEnd?: string | null
  today?: string
  windowLabel?: string
  /** Optional in-stream/dock action slot (e.g. the Log-to-Samīkṣā affordance). */
  action?: React.ReactNode
}

export function PredictionCard(props: PredictionCardProps) {
  const eyebrow = lifecycleEyebrow(props.lifecycleStatus, {
    outcome: props.outcome ?? null,
    closingSoon: props.closingSoon,
  })
  const hasTimeline = !!(props.readingDate && props.windowStart && props.windowEnd && props.today)

  return (
    <div className="pp-prediction-card" data-testid="prediction-card" data-lifecycle={props.lifecycleStatus}>
      <div className="pp-prediction-card__eyebrow" data-testid="prediction-card-eyebrow">
        {eyebrow}
      </div>
      <div className="pp-prediction-card__claim" data-testid="prediction-card-claim">
        {props.claimText}
      </div>
      {hasTimeline ? (
        <KalaRekha
          readingDate={props.readingDate!}
          windowStart={props.windowStart!}
          windowEnd={props.windowEnd!}
          today={props.today!}
          windowLabel={props.windowLabel}
        />
      ) : null}
      {props.action ? <div className="pp-prediction-card__action">{props.action}</div> : null}
    </div>
  )
}
