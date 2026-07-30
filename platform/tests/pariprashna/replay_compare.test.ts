/**
 * SAMĀPTI lane B-PB8-BYTEEQ — the real-reading comparator core
 * (`src/lib/pariprashna/store/replay_compare.ts` + `replay_paths.ts`).
 *
 * These exercise the comparator against hand-built stand-ins for a captured
 * stream and its persisted rows. They are NOT, and must never be cited as, the
 * "against one real deployed reading" run BRIEF_PB-2 §G-1 demands — that run
 * requires the capture flag on in a deployed environment and a real reading to
 * have streamed through it. What they DO prove is that the instrument works:
 * it says byte-identical when the two sides agree, it says diverged with a real
 * per-part diff when they don't, and it never reports "couldn't check" as a
 * pass.
 */
import { describe, expect, it } from 'vitest'
import {
  compareReplayAgainstPersisted,
  exitCodeFor,
  formatReplayComparison,
  notComparable,
  type ComparatorIdentity,
} from '@/lib/pariprashna/store/replay_compare'
import {
  PREDICTION_SCORE_FLOOR,
  predictionCandidatesFromWireFlags,
  replayCanonicalParts,
} from '@/lib/pariprashna/store/replay_paths'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import type { PersistedMessagePart } from '@/lib/pariprashna/store/schema'

const MESSAGE_ID = '33333333-3333-3333-3333-333333333333'
const IDENTITY: ComparatorIdentity = {
  id: MESSAGE_ID,
  conversation_id: '44444444-4444-4444-4444-444444444444',
  role: 'assistant',
  schema_version: 1,
  model_id: 'claude-opus-4-8[1m]',
  provider: 'anthropic',
}

const STREAM: PariprashnaEvent[] = [
  { type: 'turn.open', seq: 0, t: 0, turn_id: 'real-turn-1', conversation_id: IDENTITY.conversation_id, chart_id: '482012f1-710e-4a25-994a-93821f5871aa', model_id: IDENTITY.model_id, reading_depth: 'auto', length_tier: 'standard' },
  { type: 'block.open', seq: 1, t: 10, block_id: 'b1', pass_id: 1, role: 'prose' },
  { type: 'block.delta', seq: 2, t: 20, block_id: 'b1', delta: 'Saturn is transiting ' },
  { type: 'block.commit', seq: 3, t: 30, block_id: 'b1', text: 'Saturn is transiting the 11th from the Moon (SIG.MSR.042).' },
  { type: 'citation.define', seq: 4, t: 40, index: 1, signal_id: 'SIG.MSR.042', layer: 'L2.5', snippet: 'Moon–Purva Bhadrapada placement' },
  { type: 'flag', seq: 5, t: 50, code: 'prediction_candidate', level: 'info', detail: 'A window opens in 2027 (score=0.81, horizon=2027)' },
  { type: 'flag', seq: 6, t: 55, code: 'prediction_candidate', level: 'info', detail: 'A weaker signal (score=0.2)' },
  { type: 'turn.commit', seq: 7, t: 60, turn_id: 'real-turn-1', conversation_id: IDENTITY.conversation_id, message_id: MESSAGE_ID, status: 'ok', assistant_chars: 58 },
  { type: 'turn.close', seq: 8, t: 70, turn_id: 'real-turn-1', status: 'ok', ms: 70 },
]

/** Persisted rows built from the SAME replay — the "everything agrees" baseline. */
function persistedFrom(events: readonly PariprashnaEvent[]): PersistedMessagePart[] {
  const preds = predictionCandidatesFromWireFlags(events)
  return replayCanonicalParts(events, preds.kept).map((p, i) => ({
    id: `part-${i}`,
    message_id: MESSAGE_ID,
    seq: p.seq,
    kind: p.kind,
    body: p.body,
    model_visible: p.model_visible,
    created_at: '2026-07-30T00:00:00Z',
  })) as PersistedMessagePart[]
}

describe('replay_paths — reconstruction from the wire', () => {
  it("applies route.ts's own score floor to wire prediction flags", () => {
    const r = predictionCandidatesFromWireFlags(STREAM)
    expect(PREDICTION_SCORE_FLOOR).toBe(0.5)
    expect(r.kept).toEqual([{ text: 'A window opens in 2027', score: 0.81, horizon: '2027' }])
    expect(r.belowFloor).toBe(1)
    expect(r.unparseable).toEqual([])
  })

  it('reports an unparseable flag detail rather than silently dropping it', () => {
    const r = predictionCandidatesFromWireFlags([
      { type: 'flag', seq: 0, t: 0, code: 'prediction_candidate', level: 'info', detail: 'Reformatted claim (score=0.9, horizon=2030).' },
    ])
    expect(r.kept).toEqual([])
    expect(r.unparseable).toHaveLength(1)
  })

  it('replays in route.ts kind-grouped order: text, then citation, then prediction', () => {
    const preds = predictionCandidatesFromWireFlags(STREAM)
    expect(replayCanonicalParts(STREAM, preds.kept).map((p) => p.kind)).toEqual([
      'text',
      'citation',
      'prediction_candidate',
    ])
  })
})

describe('replay_compare — the instrument itself', () => {
  it('reports BYTE-IDENTICAL when the persisted rows match the replay', () => {
    const c = compareReplayAgainstPersisted({
      turnId: 'real-turn-1',
      events: STREAM,
      message: IDENTITY,
      persistedParts: persistedFrom(STREAM),
    })
    expect(c.status).toBe('byte_identical')
    expect(c.diffs).toEqual([])
    expect(exitCodeFor(c)).toBe(0)
    expect(c.predictions_below_floor).toBe(1)
    expect(formatReplayComparison(c)).toContain('BYTE-IDENTICAL')
  })

  it('reports DIVERGED with a per-part diff when a persisted body differs (the citation asymmetry class)', () => {
    // Models the real, documented asymmetry: the WIRE's citation.define and the
    // WRITER's independent extractCitations + fetchMsrSnippets derivation can
    // disagree on the snippet. This is exactly what the tool exists to surface.
    const persisted = persistedFrom(STREAM).map((p) =>
      p.kind === 'citation'
        ? { ...p, body: { ...(p.body as Record<string, unknown>), snippet: 'a DIFFERENT snippet from the DB lookup' } }
        : p,
    ) as PersistedMessagePart[]

    const c = compareReplayAgainstPersisted({ turnId: 'real-turn-1', events: STREAM, message: IDENTITY, persistedParts: persisted })
    expect(c.status).toBe('diverged')
    expect(exitCodeFor(c)).toBe(1)
    expect(c.diffs).toHaveLength(1)
    expect(c.diffs[0].kind).toBe('citation')
    expect(c.diffs[0].replayed).toContain('Moon–Purva Bhadrapada placement')
    expect(c.diffs[0].persisted).toContain('a DIFFERENT snippet from the DB lookup')
    expect(formatReplayComparison(c)).toContain('DIVERGED')
  })

  it('reports DIVERGED when the DB holds a part the replay does not produce', () => {
    const persisted = [
      ...persistedFrom(STREAM),
      { id: 'extra', message_id: MESSAGE_ID, seq: 99, kind: 'text', body: { text: 'an orphan row' }, model_visible: true, created_at: '2026-07-30T00:00:00Z' },
    ] as PersistedMessagePart[]
    const c = compareReplayAgainstPersisted({ turnId: 'real-turn-1', events: STREAM, message: IDENTITY, persistedParts: persisted })
    expect(c.status).toBe('diverged')
    expect(c.diffs.at(-1)?.replayed).toBeNull()
  })

  it('NOT-COMPARABLE is exit code 2, never 0 — "we could not check" must not read as "it passed"', () => {
    const c = notComparable('real-turn-1', 'no captured stream for this turn')
    expect(c.status).toBe('not_comparable')
    expect(exitCodeFor(c)).toBe(2)
    expect(formatReplayComparison(c)).toContain('NOT COMPARABLE')
  })
})
