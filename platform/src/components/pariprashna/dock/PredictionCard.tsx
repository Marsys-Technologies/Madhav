import type { PredictionCardData } from '../state/types'
import { PredictionCard as SamikshaPredictionCard } from '../samiksha/PredictionCard'
import type { LifecycleState, Outcome } from '@/lib/pariprashna/samiksha/schema'

/**
 * PB-6 (SAMĀPTI, 2026-07-30): this used to be its own fixture-fed
 * re-implementation of the kāla-rekhā geometry, fed a HARDCODED
 * `todayFractionOfSpan` fixture literal (`0.3`) — so it never rendered
 * correctly outside the one demo fixture that supplied it, and never at all
 * on the live SSE path (which has no producer for that fraction). It now
 * mounts the spec-conformant `samiksha/PredictionCard` + `samiksha/KalaRekha`
 * pair (previously dead code, imported by nothing) and feeds it REAL ISO date
 * anchors, so the geometry is computed live by the pure `computeKalaRekha`
 * (lib/pariprashna/samiksha/kala_rekha.ts) — never a pre-baked fraction —
 * and the today-dot is read from the real clock at render time, not stored
 * data. Dot size follows `samiksha/KalaRekha.tsx`'s CSS (3px, per §6.9),
 * replacing this file's former 7px inline dot.
 *
 * This adapter's only job is translating the dock's simpler view-level
 * `PredictionCardData['lifecycle']` enum into samiksha's
 * `(lifecycleStatus, outcome, closingSoon)` triple — the DB lifecycle enum
 * plus the two derived signals `lifecycleEyebrow` needs — so the eyebrow
 * text this renders is IDENTICAL to the former `LIFECYCLE_LABEL` map.
 */
const DOCK_LIFECYCLE_MAP: Record<
  PredictionCardData['lifecycle'],
  { status: LifecycleState; outcome?: Outcome; closingSoon?: boolean }
> = {
  window_open: { status: 'open', closingSoon: false },
  window_closing: { status: 'open', closingSoon: true },
  awaiting_outcome: { status: 'window_closed' },
  resolved_confirmed: { status: 'outcome_recorded', outcome: 'happened' },
  resolved_missed: { status: 'outcome_recorded', outcome: 'did_not_happen' },
  resolved_mixed: { status: 'outcome_recorded', outcome: 'partial' },
}

/** Today's REAL date, ISO yyyy-mm-dd, UTC — never a stored/fixture value. */
function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

export function PredictionCard({ prediction }: { prediction: PredictionCardData }) {
  const { status, outcome, closingSoon } = DOCK_LIFECYCLE_MAP[prediction.lifecycle]

  return (
    <div className="mb-4">
      <SamikshaPredictionCard
        claimText={prediction.claim}
        lifecycleStatus={status}
        outcome={outcome ?? null}
        closingSoon={closingSoon}
        readingDate={prediction.readingDate}
        windowStart={prediction.windowStart}
        windowEnd={prediction.windowEnd}
        today={todayIso()}
        windowLabel={`${prediction.windowStartLabel} – ${prediction.windowEndLabel}`}
        confidencePhrase={prediction.confidencePhrase}
        predictionRef={prediction.ref}
      />
    </div>
  )
}
