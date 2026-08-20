import type { TurnState } from './state/types'

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
  const { factorCount, classicalCount, completenessLine, source } = turn.grounding
  let summary =
    classicalCount > 0
      ? `Reading complete. Grounded in ${factorCount} chart factors, ${classicalCount} classical sources.`
      : `Reading complete. Grounded in ${factorCount} chart factors.`
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
