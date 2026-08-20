import type { TurnState } from './state/types'
import { isIncompleteTurn } from './state/reducer'

/**
 * P2-D (PPR-10, FD-9) — the explicit, VISIBLE incomplete-turn state.
 *
 * Renders exactly when a turn is SETTLED_VISUAL (the reader sees a finished
 * answer) but NOT yet DURABLY_PERSISTED (`isIncompleteTurn`, reducer.ts).
 * Distinguishes 'pending' (gentle — still saving, no action needed) from
 * 'failed' (the write did not succeed — the reading itself is unaffected and
 * still fully readable above; this notice is honest about storage only, never
 * about the reading's validity).
 *
 * `isIncompleteTurn` itself already excludes `persistence === 'unknown'`
 * (see reducer.ts's doc comment) — a stream that never emits any persistence
 * signal (every pre-P2-D fixture, and flag-off's own turn.commit-only path in
 * the ordinary case) renders no banner at all, honestly, rather than
 * inventing an alarm from silence (§N.7 item 6).
 */
export function PersistenceNotice({ turn }: { turn: TurnState }) {
  if (!isIncompleteTurn(turn)) return null

  const isFailed = turn.persistence === 'failed'

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-2.5 mt-2 mb-3.5 px-3.5 py-2.5 rounded"
      style={{ border: '1px solid var(--pp-rule)', background: 'var(--pp-tint)', fontSize: 12.5, color: 'var(--pp-ink-dim)' }}
    >
      {!isFailed && (
        <span
          aria-hidden
          data-pp-spin
          className="flex-none inline-block w-2 h-2 rounded-full"
          style={{ border: '1.5px solid var(--pp-gold)', borderTopColor: 'transparent' }}
        />
      )}
      <span>
        {isFailed
          ? "This reading is fully shown above, but we couldn't confirm it saved. It may not survive a refresh — worth a quick note if it matters."
          : 'Confirming this reading saved…'}
      </span>
    </div>
  )
}
