import type { TurnState } from './state/types'
import { GRADE_SUMMARY_WELL_GROUNDED } from './state/groundingRollup'

/**
 * Mounts once, after `turn.commit` (§5.1 ③) — but its VISUAL content lives
 * in the right dock (native ruling 2026-07-27; `dock/RightDock.tsx` reads
 * `citations`/`blocks` straight off `ThreadState.turns`, so there is a
 * single source of truth instead of a duplicate registration channel).
 * What stays here, in the turn's own DOM position, is the one thing that
 * must NOT live in a collapsible/possibly-hidden panel: the settle
 * announcement for assistive tech (§9.3 — "Settle announces one summary").
 */
export function GroundingRegion({ turn }: { turn: TurnState }) {
  if (turn.status !== 'settled' || !turn.grounding) return null
  const { factorCount, classicalCount, completenessLine, source, gradeSummaryLabel } = turn.grounding
  // The bare citation count is never itself a confidence verdict (§N.7/§N.8
  // — groundingRollup.ts's own rationale): only announce "Grounded in N…" as
  // an unqualified confident claim when the ACTUAL per-citation grade
  // distribution earned that word. Otherwise the count stands, but the
  // already-computed honest rollup (WELL-GROUNDED / SUPPORTED /
  // CATALOG-ONLY — UNVERIFIED / HONEST GAP) replaces the word "Grounded"
  // rather than being silently discarded.
  const isWellGrounded = gradeSummaryLabel === GRADE_SUMMARY_WELL_GROUNDED
  let summary: string
  if (isWellGrounded) {
    summary =
      classicalCount > 0
        ? `Reading complete. Grounded in ${factorCount} chart factors, ${classicalCount} classical sources.`
        : `Reading complete. Grounded in ${factorCount} chart factors.`
  } else {
    summary =
      classicalCount > 0
        ? `Reading complete. ${gradeSummaryLabel} (${factorCount} chart factors, ${classicalCount} classical sources).`
        : `Reading complete. ${gradeSummaryLabel} (${factorCount} chart factors).`
  }
  if (completenessLine) summary += ` ${completenessLine}.`
  // G2-B (§N.7 item 6): a client-estimated rollup must never read the same
  // as a server-derived one — the ONE reader-facing summary this component
  // announces discloses the estimate explicitly rather than silently.
  if (source === 'client_estimate') summary += ' (Estimated from this session — not yet server-verified.)'
  return (
    <p role="status" aria-live="polite" className="sr-only">
      {summary}
    </p>
  )
}
