/**
 * SAMĪKṢĀ lifecycle transitions — PB-3 lane L-1.
 *
 * Pure enforcement of the ONE legal-transition matrix (LEGAL_TRANSITIONS in schema.ts). No
 * DB, no I/O — so it is unit-testable in isolation and is the single place both the writer
 * DAL and any caller consult to decide whether a lifecycle move is allowed. Illegal moves
 * throw IllegalTransitionError; they are never silently allowed.
 */

import { LEGAL_TRANSITIONS, LifecycleStateSchema, type LifecycleState } from './schema'

export class IllegalTransitionError extends Error {
  readonly from: LifecycleState
  readonly to: LifecycleState
  constructor(from: LifecycleState, to: LifecycleState) {
    super(
      `Illegal SAMĪKṢĀ lifecycle transition ${from} → ${to}. ` +
        `Legal targets from ${from}: [${LEGAL_TRANSITIONS[from].join(', ') || '(terminal)'}].`,
    )
    this.name = 'IllegalTransitionError'
    this.from = from
    this.to = to
  }
}

/** True iff `from → to` is a legal transition. A same-state self-loop is NOT legal. */
export function isLegalTransition(from: LifecycleState, to: LifecycleState): boolean {
  return LEGAL_TRANSITIONS[from]?.includes(to) ?? false
}

/** Throw IllegalTransitionError unless `from → to` is legal. Validates both are real states. */
export function assertLegalTransition(from: LifecycleState, to: LifecycleState): void {
  // Guard against a caller passing a value outside the enum (e.g. a stale/hand-typed status).
  LifecycleStateSchema.parse(from)
  LifecycleStateSchema.parse(to)
  if (!isLegalTransition(from, to)) {
    throw new IllegalTransitionError(from, to)
  }
}

/** True iff a state has no legal outbound transitions (a terminal exit). */
export function isTerminal(state: LifecycleState): boolean {
  return LEGAL_TRANSITIONS[state].length === 0
}
