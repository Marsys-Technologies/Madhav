/**
 * The two canonical-parts drivers the byte-equality gate compares — extracted
 * from `canonical_serialization_golden.test.ts` (PB-2 lane M-2) so that the
 * single-fixture gate and the 12-fixture corpus gate
 * (`canonical_serialization_corpus.test.ts`, SAMĀPTI lane B-PB8-BYTEEQ) drive
 * the SAME two code paths rather than each re-implementing them. A third
 * reimplementation would be exactly the failure mode this whole follow-up
 * exists to correct.
 *
 *   (a) REDUCER PATH — an independently-coded, test-owned simulation of a
 *       CLIENT reducer. Deliberately does NOT import
 *       `route_writer_adapter.ts`, so a bug in either this function or the
 *       production mapping surfaces as a byte mismatch, not as a shared bug.
 *
 *       DISCLOSED (unchanged from M-2, and NOT closed by this lane): the real
 *       shipped client reducer (`state/reducer.ts` + `state/s1LiveAdapter.ts`)
 *       produces UI turn state (`WireEvent`/`TurnState`), never canonical
 *       parts — there is no shipped client→canonical adapter to call. Until one
 *       exists, "the reducer path" is necessarily a simulation. See the lane's
 *       residuals.
 *
 *   (b) WRITER PATH — the REAL production mapping functions from
 *       `route_writer_adapter.ts`, driven in the SAME ORDER
 *       `app/api/pariprashna/route.ts` drives them at its persistence seam.
 *
 * ORDERING CONTRACT (corrected by lane B-PB8-BYTEEQ — see the corpus test's
 * can-fail note). `route.ts`'s `writeMessages` builds parts GROUPED BY KIND:
 * every committed prose block first (`for (const b of committedBlocks)`), then
 * every citation, then every prediction candidate. The original M-2 driver
 * instead interleaved text and citation parts in wire order. Both agreed on the
 * one inline fixture (its single block commits before its single citation is
 * defined), so the divergence was invisible to a one-fixture gate. Both paths
 * here now group by kind, matching the route.
 *
 * COMMIT CONTRACT (also corrected by lane B-PB8-BYTEEQ). Only a COMMITTED prose
 * block becomes a canonical `text` part — `route.ts` iterates `committedBlocks`,
 * so an opened-but-never-committed block (a stopped or disconnected turn)
 * persists nothing. The original reducer-path driver emitted a text part for
 * every OPENED prose block; again invisible to a fixture whose only block always
 * commits.
 */

import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import type { MessagePartInput } from '@/lib/pariprashna/store/schema'
import { parsePredictionFlagDetail, replayCanonicalParts } from '@/lib/pariprashna/store/replay_paths'

export { parsePredictionFlagDetail }

// ---------------------------------------------------------------------------
// (a) REDUCER PATH — independently-coded client-side simulation.
// ---------------------------------------------------------------------------

export interface ReducerBlockState {
  role: 'prose' | 'thinking'
  text: string
  /** Mirrors route.ts's `committedBlocks`: only a committed block persists. */
  committed: boolean
}
export interface ReducerCitationState {
  index: number
  signal_id: string
  layer: string
  snippet: string
  reader_label?: string
  grade?: string
}
export interface ReducerState {
  blockOrder: string[]
  blocks: Map<string, ReducerBlockState>
  citations: ReducerCitationState[]
  predictionFlagDetails: string[]
}

export function createReducerState(): ReducerState {
  return { blockOrder: [], blocks: new Map(), citations: [], predictionFlagDetails: [] }
}

export function applyToReducerState(state: ReducerState, event: PariprashnaEvent): void {
  switch (event.type) {
    case 'block.open':
      state.blockOrder.push(event.block_id)
      state.blocks.set(event.block_id, { role: event.role, text: '', committed: false })
      break
    case 'block.delta': {
      const b = state.blocks.get(event.block_id)
      if (b) b.text += event.delta
      break
    }
    case 'block.commit': {
      const b = state.blocks.get(event.block_id)
      if (b) {
        b.text = event.text // final_text is authoritative, per the real protocol
        b.committed = true
      }
      break
    }
    case 'citation.define':
      state.citations.push({
        index: event.index,
        signal_id: event.signal_id,
        layer: event.layer,
        snippet: event.snippet,
        ...(event.reader_label !== undefined ? { reader_label: event.reader_label } : {}),
        ...(event.grade !== undefined ? { grade: event.grade } : {}),
      })
      break
    case 'flag':
      if (event.code === 'prediction_candidate' && event.detail) {
        state.predictionFlagDetails.push(event.detail)
      }
      break
    default:
      break // other event types don't drive canonical-part state
  }
}

/**
 * Reducer-state → canonical `MessagePartInput[]`. Independently coded from
 * `route_writer_adapter.ts` — reimplements the SAME intended mapping rule
 * (committed prose block → text; citation.define → citation;
 * prediction_candidate flag → prediction_candidate), grouped by kind exactly as
 * route.ts groups them — not a call-through to the production functions.
 */
export function reducerStateToCanonicalParts(state: ReducerState): MessagePartInput[] {
  const parts: MessagePartInput[] = []
  let seq = 0
  for (const blockId of state.blockOrder) {
    const b = state.blocks.get(blockId)
    if (b && b.role === 'prose' && b.committed) {
      parts.push({ seq: seq++, kind: 'text', body: { text: b.text, block_id: blockId }, model_visible: true })
    }
  }
  for (const c of state.citations) {
    parts.push({
      seq: seq++,
      kind: 'citation',
      body: {
        index: c.index,
        signal_id: c.signal_id,
        layer: c.layer,
        snippet: c.snippet,
        ...(c.reader_label !== undefined ? { reader_label: c.reader_label } : {}),
        ...(c.grade !== undefined ? { grade: c.grade } : {}),
      },
      model_visible: false,
    })
  }
  for (const detail of state.predictionFlagDetails) {
    const parsed = parsePredictionFlagDetail(detail)
    if (!parsed) continue // honest drop — a malformed/unparseable flag can't be reconstructed
    parts.push({
      seq: seq++,
      kind: 'prediction_candidate',
      body: {
        claim: parsed.claim,
        confidence: Math.max(0, Math.min(1, parsed.score)),
        ...(parsed.horizon !== null ? { window: parsed.horizon } : {}),
        source_flag_code: 'prediction_candidate',
      },
      model_visible: false,
    })
  }
  return parts
}

export function runReducerPath(events: readonly PariprashnaEvent[]): MessagePartInput[] {
  const state = createReducerState()
  for (const event of events) applyToReducerState(state, event)
  return reducerStateToCanonicalParts(state)
}

// ---------------------------------------------------------------------------
// (b) WRITER PATH — the PRODUCTION replay module, re-exported under the name
// the two gate files use. Deliberately not redefined here.
// ---------------------------------------------------------------------------

export function runWriterPath(
  events: readonly PariprashnaEvent[],
  predictionCandidates: readonly { text: string; score: number; horizon: string | null }[],
): MessagePartInput[] {
  return replayCanonicalParts(events, predictionCandidates)
}
