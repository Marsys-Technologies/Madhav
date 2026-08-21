/**
 * Paripraśna transcript reducer.
 *
 * Implements the "reducer laws" from the design plan §8.3:
 *  - `block.delta` may touch only `tail`, never `blocks` (P1 — settled
 *    content is sacred; the tail is the ONLY volatile thing).
 *  - `block.commit` moves tail → blocks, append-only, and freezes it.
 *  - `citation.define` may arrive before its chip is referenced in prose —
 *    chips must render fully-formed on first paint (M6).
 *  - `turn.commit` populates `grounding`; the settling choreography (§5.3
 *    "the Seal") is triggered by the component layer observing the status
 *    transition to `settling`, not by the reducer performing side effects.
 *  - Duplicate event ids are dropped idempotently (reconnect safety).
 *  - `flag` events populate presentation flags used by grade/gap rendering.
 *
 * Pass seams (§5.8.1 ruling 8a) are modeled as a second transient slot
 * (`activeSeam`) parallel to `tail`: a seam opens live (band-style spinner +
 * label) between passes, then settles in place into a frozen divider block —
 * exactly the tail's open → commit lifecycle, applied to a different block
 * kind, which is why FrozenBlock's "never re-render post-commit" invariant
 * is never violated by a seam.
 */

import type { ThreadState, TurnState, WireEvent, ActivityRow } from './types'

export const initialThreadState: ThreadState = {
  turns: [],
  surfaceStatus: 'empty',
}

export function makeInitialTurnState(id: string, userText: string): TurnState {
  return {
    id,
    userText,
    status: 'submitted',
    phaseLabel: 'Reading the question…',
    passIndex: 0,
    openedAtMs: Date.now(),
    activities: [],
    blocks: [],
    tail: null,
    activeSeam: null,
    citations: {},
    grounding: null,
    readingDepthReceived: null,
    error: null,
    pendingPredictionCandidates: [],
    lastEventId: null,
    seenEventIds: new Set<string>(),
    reconnectHollowCaret: false,
    persistence: 'unknown',
    receipt: null,
    interpretationSets: null,
  }
}

/**
 * P2-D (PPR-10, FD-9) — SETTLED_VISUAL: the reader sees a finished answer.
 * Deliberately a pure function of `status`, not a stored field — it is
 * fully derivable and a second source of truth would risk drifting from the
 * status transitions the reducer already owns.
 */
export function isSettledVisual(turn: Pick<TurnState, 'status'>): boolean {
  return turn.status === 'settled'
}

/**
 * P2-D (PPR-10, FD-9) — DURABLY_PERSISTED: the assistant turn is confirmed
 * safely stored. See `PersistenceStatus`'s doc comment (state/types.ts) for
 * the full back-compat contract.
 */
export function isDurablyPersisted(turn: Pick<TurnState, 'persistence'>): boolean {
  return turn.persistence === 'durable'
}

/**
 * P2-D — true exactly when the UI owes the reader a visible incomplete-turn
 * notice: the answer LOOKS done but is confirmed NOT (yet, or ever) durable.
 * Never true while still streaming/thinking — an in-flight turn's
 * incompleteness is already communicated by the working band, not this.
 *
 * `persistence === 'unknown'` is deliberately EXCLUDED (not treated as
 * incomplete) — it means no signal has arrived at all, which today is
 * exactly what a pre-P2-D fixture/stream produces (nothing ever emits
 * `turn.persisted`, and `turn.commit` carried no `persistStatus`). Reporting
 * "incomplete" on silence would be an invented judgment (§N.7 item 6) and
 * would surface a false banner on every demo/legacy reading — the honest
 * response to "no signal" is no claim either way, not an alarm.
 */
export function isIncompleteTurn(turn: Pick<TurnState, 'status' | 'persistence'>): boolean {
  return isSettledVisual(turn) && turn.persistence !== 'unknown' && !isDurablyPersisted(turn)
}

/** Client-only action: submit a new user turn (optimistic, §5.3 `submitted`). */
export interface SubmitTurnAction {
  type: 'CLIENT_SUBMIT_TURN'
  turnId: string
  userText: string
}

/** Client-only action: user pressed Stop — turn settles as interrupted, keeping whatever arrived. */
export interface StopAction {
  type: 'CLIENT_STOP'
  turnId: string
}

/** Client-only action: expand/collapse handled at component level (not reducer) — no action needed. */

export type ThreadAction = WireEvent | SubmitTurnAction | StopAction

function updateTurn(state: ThreadState, turnId: string, fn: (t: TurnState) => TurnState): ThreadState {
  let touched = false
  const turns = state.turns.map((t) => {
    if (t.id !== turnId) return t
    touched = true
    return fn(t)
  })
  if (!touched) return state
  return { ...state, turns }
}

function upsertActivity(activities: ActivityRow[], row: ActivityRow): ActivityRow[] {
  const idx = activities.findIndex((a) => a.id === row.id)
  if (idx === -1) return [...activities, row]
  const next = activities.slice()
  // status-glyph patch only — geometry of the row never changes (§8.2/§5.1)
  next[idx] = { ...next[idx], status: row.status, ms: row.ms ?? next[idx].ms }
  return next
}

/**
 * Duplicate iff this exact event id has ALREADY been applied to this turn.
 * Uses the per-turn seen-SET (not a single last-id slot), so a non-adjacent
 * redelivery — the reconnect-replays-an-earlier-batch case — is correctly
 * recognized, not just a back-to-back repeat.
 */
function isDuplicateEvent(turn: TurnState, eventId: string | undefined): boolean {
  if (!eventId) return false
  return turn.seenEventIds.has(eventId)
}

/** Return a new seen-set with `eventId` recorded (immutable update). */
function addSeen(turn: TurnState, eventId: string | undefined): Set<string> {
  if (!eventId) return turn.seenEventIds
  return new Set(turn.seenEventIds).add(eventId)
}

export function threadReducer(state: ThreadState, action: ThreadAction): ThreadState {
  switch (action.type) {
    case 'CLIENT_SUBMIT_TURN': {
      const newTurn = makeInitialTurnState(action.turnId, action.userText)
      return {
        surfaceStatus: 'idle',
        turns: [...state.turns, newTurn],
      }
    }

    case 'CLIENT_STOP': {
      return updateTurn(state, action.turnId, (t) => {
        // Freeze whatever is in the tail as a final committed block — nothing discarded.
        const blocks = t.tail
          ? [...t.blocks, { id: t.tail.blockId, kind: t.tail.kind, role: t.tail.role, html: t.tail.text }]
          : t.blocks
        return { ...t, status: 'interrupted', tail: null, blocks }
      })
    }

    case 'turn.open': {
      if (state.turns.some((t) => t.id === action.turnId)) return state
      return {
        surfaceStatus: 'idle',
        turns: [...state.turns, makeInitialTurnState(action.turnId, action.userText)],
      }
    }

    case 'phase': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return { ...t, status: t.status === 'submitted' ? 'thinking' : t.status, phaseLabel: action.label, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'activity.upsert': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        const row: ActivityRow = {
          id: action.row.id,
          passIndex: action.row.passIndex,
          label: action.row.label,
          detail: action.row.detail,
          kind: action.row.kind,
          status: action.row.status ?? 'running',
          ms: action.row.ms,
        }
        return {
          ...t,
          status: t.status === 'submitted' ? 'thinking' : t.status,
          activities: upsertActivity(t.activities, row),
          passIndex: Math.max(t.passIndex, action.row.passIndex),
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'pass.seam.open': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return {
          ...t,
          status: 'thinking',
          passIndex: action.passIndex,
          activeSeam: { blockId: action.blockId, passIndex: action.passIndex, liveLabel: action.liveLabel },
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'pass.seam.settle': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        if (!t.activeSeam || t.activeSeam.blockId !== action.blockId) return t
        return {
          ...t,
          activeSeam: null,
          blocks: [...t.blocks, { id: action.blockId, kind: 'seam', html: '', seamSummary: action.summary }],
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'block.open': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        const next: TurnState = { ...t, status: 'streaming', lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
        if (action.kind === 'paragraph' || action.kind === 'list') {
          next.tail = { blockId: action.blockId, kind: action.kind, role: action.role, text: '' }
        }
        return next
      })
    }

    case 'block.delta': {
      // Reducer law: block.delta may touch ONLY `tail`, never `blocks`.
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        if (!t.tail || t.tail.blockId !== action.blockId) return t
        return { ...t, tail: { ...t.tail, text: t.tail.text + action.textDelta }, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'block.commit': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        const committed = {
          id: action.blockId,
          kind: action.kind,
          role: action.role,
          html: action.html ?? (t.tail && t.tail.blockId === action.blockId ? t.tail.text : ''),
          table: action.table,
          tableSpans: action.tableSpans,
          gapText: action.gapText,
          prediction: action.prediction,
        }
        const tailCleared = t.tail && t.tail.blockId === action.blockId ? null : t.tail
        return {
          ...t,
          blocks: [...t.blocks, committed],
          tail: tailCleared,
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'citation.define': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return {
          ...t,
          citations: { ...t.citations, [action.citation.n]: action.citation },
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'flag': {
      return updateTurn(state, action.turnId, (t) => ({ ...t, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }))
    }

    case 'grade': {
      return updateTurn(state, action.turnId, (t) => ({ ...t, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }))
    }

    case 'reading_depth.received': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return { ...t, readingDepthReceived: action.depth, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'receipt.define': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return {
          ...t,
          receipt: action.receipt,
          // G3-E's existing consumer (InterpretationSetsSection.tsx) reads
          // this projection specifically — see this field's own doc comment
          // in types.ts for why both fields are set from the same object.
          // `?? null`: the receipt schema's own field is `.optional()`
          // (undefined-shaped), TurnState's is `| null` — an honest absence
          // either way, just two different schemas' own conventions for it.
          interpretationSets: action.receipt.interpretation_sets ?? null,
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'turn.commit': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        // P2-D back-compat seed (see PersistenceStatus's doc comment): only
        // seeds from 'unknown' — never regresses a value a real
        // turn.persisted event already refined, which matters if a
        // reconnect/replay ever re-delivers turn.commit after turn.persisted
        // (defensive; today's ordering never does this).
        const persistence: TurnState['persistence'] =
          t.persistence !== 'unknown' ? t.persistence : action.persistStatus === 'error' ? 'failed' : action.persistStatus === 'ok' ? 'durable' : 'unknown'
        return { ...t, status: 'settling', grounding: action.grounding, persistence, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'turn.persisted': {
      // P2-D (PPR-10, FD-9). Latest-wins, not append-only — a turn may
      // legitimately go pending -> durable, or pending -> failed -> (retried)
      // -> durable, and each new signal is the most current truth. Not gated
      // by the seen-event dedup alone: a SECOND turn.persisted for the same
      // turn is a real state transition, not a duplicate, so only an EXACT
      // eventId repeat (a genuine redelivery) is dropped.
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return { ...t, persistence: action.status, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'turn.close': {
      return updateTurn(state, action.turnId, (t) => {
        if (t.status === 'settling') return { ...t, status: 'settled', lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
        return { ...t, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'error': {
      return updateTurn(state, action.turnId, (t) => ({ ...t, status: 'errored', error: action.error, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }))
    }

    case 'reconnecting': {
      return updateTurn(state, action.turnId, (t) => ({ ...t, status: 'reconnecting', reconnectHollowCaret: true, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }))
    }

    case 'reconnected': {
      return updateTurn(state, action.turnId, (t) => ({ ...t, status: 'streaming', reconnectHollowCaret: false, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }))
    }

    case 'interrupted': {
      return updateTurn(state, action.turnId, (t) => {
        const blocks = t.tail
          ? [...t.blocks, { id: t.tail.blockId, kind: t.tail.kind, role: t.tail.role, html: t.tail.text }]
          : t.blocks
        return { ...t, status: 'interrupted', tail: null, blocks, lastEventId: action.eventId, seenEventIds: addSeen(t, action.eventId) }
      })
    }

    case 'snapshot.apply': {
      // PB-2/M-5: a gap-fallback snapshot REPLACES the turn's blocks/tail
      // wholesale — the client cannot trust its own partial block list after
      // a buffer-eviction gap (it may be missing commits it never saw), so
      // this is a full replace, applied as ONE write (no replay animation),
      // never an append onto whatever was already there.
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        const citations = { ...t.citations }
        for (const c of action.citations) citations[c.n] = c
        const status: TurnState['status'] =
          action.turnStatus === 'interrupted' ? 'interrupted' : action.turnStatus === 'closed' ? 'settling' : 'streaming'
        return {
          ...t,
          status,
          tail: null,
          activeSeam: null,
          blocks: action.text ? [{ id: `snapshot-${action.turnId}`, kind: 'paragraph' as const, html: action.text }] : t.blocks,
          citations,
          reconnectHollowCaret: false,
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    case 'prediction_card': {
      return updateTurn(state, action.turnId, (t) => {
        if (isDuplicateEvent(t, action.eventId)) return t
        return {
          ...t,
          pendingPredictionCandidates: [
            ...t.pendingPredictionCandidates,
            { partId: action.partId, conversationId: action.conversationId, candidate: action.candidate },
          ],
          lastEventId: action.eventId,
          seenEventIds: addSeen(t, action.eventId),
        }
      })
    }

    default:
      return state
  }
}
