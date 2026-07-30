/**
 * Canonical byte-equality golden test — PB-2 (SMṚTI) lane M-2, wave PB-2's
 * [integrity] centerpiece.
 *
 * UPGRADE of lane C-2's golden reducer scaffold (`./golden.test.ts` +
 * `./reducer.mjs`) for the M-1/M-2 era. C-2's `reducer.mjs` replays a
 * PRE-LOCK harness event shape (`citation_id`, `final_text`, `flag_key`,
 * `block_count`, …) that predates S-1's real merged wire protocol — see
 * `events.ts`'s own header ("Event vocabulary … C-2 had not yet drafted the
 * module") and `c2ProtocolAdapter.ts`'s header (documents the C-2-fixture ->
 * real-wire field mapping). That format is retained untouched as a historical
 * artifact; it is not a fit for testing M-1's REAL canonical schema, which is
 * keyed to the REAL, merged `@/lib/pariprashna/protocol/events` wire.
 *
 * This test authors ONE representative fixture directly in the real
 * `PariprashnaEvent` shape (Zod-validated on load, so the fixture itself
 * cannot silently drift from the live protocol) and proves the wave's core
 * integrity claim:
 *
 *   (a) REDUCER PATH — an independently-coded, test-owned simulation of a
 *       CLIENT reducer (mirroring what `state/s1LiveAdapter.ts` does in spirit:
 *       accumulate block text per block_id, track citation.define, and derive
 *       whatever it CAN from a `flag{code:'prediction_candidate'}` event —
 *       the only prediction-candidate signal the real wire carries) replays
 *       the fixture and is converted to canonical parts by a small adapter
 *       (`reducerStateToCanonicalParts`, below).
 *
 *   (b) WRITER PATH — the SAME fixture (plus the one piece of data the real
 *       wire does NOT carry: the server's own structured prediction-candidate
 *       detection — see the "disclosed asymmetry" note below) is traced
 *       through lane M-2's REAL PRODUCTION mapping functions
 *       (`route_writer_adapter.ts` — the exact functions
 *       `app/api/pariprashna/route.ts` calls at its persistence seam).
 *
 *   (c) Both are serialized via M-1's `serializeCanonical` and asserted
 *       BYTE-IDENTICAL.
 *
 * DISCLOSED ASYMMETRY (prediction_candidate): the real wire has no dedicated
 * prediction-candidate event — the route surfaces a candidate to the CLIENT
 * only as a formatted `flag` info string:
 *   `${text} (score=${score}[, horizon=${horizon}])`
 * (see `app/api/pariprashna/route.ts`'s bridgeWriter `data-prediction-candidate`
 * case). The WRITER path is fed the server's own structured detection
 * directly (richer than the wire, exactly as the live route is). The REDUCER
 * path can only regex-parse the flag's human-formatted string back apart —
 * fragile and format-coupled, not a robust round-trip. This test's reducer
 * does that regex-parse (proving it CAN be made to agree, for a
 * well-behaved claim/score/horizon), and a companion test below
 * (`prediction_candidate fidelity is wire-format-coupled, not a true
 * round-trip`) demonstrates the fragility directly — a claim containing the
 * literal substring the format uses as its own delimiter breaks the
 * reducer-side parse while the writer path (fed structured data) is
 * unaffected. This is the honest, disclosed gap noted in the M-2 report: a
 * future protocol lane should add a dedicated
 * `prediction_candidate.define` structured event.
 *
 * SCOPE NOTE (SAMĀPTI lane B-PB8-BYTEEQ, 2026-07-30). This file remains the
 * ONE-FIXTURE gate, and a green run here proves ONLY that this fixture's event
 * sequence round-trips. The full 12-fixture corpus assertion the PB-2 brief
 * §G-1 actually demanded now lives in `./canonical_serialization_corpus.test.ts`
 * (via `./c2_corpus_bridge.ts`); the two reducer/writer drivers were extracted
 * to `./canonical_paths.ts` so both gates drive the SAME code, not two copies.
 * Extraction surfaced two driver bugs this single fixture could never see — an
 * uncommitted block wrongly persisting, and interleaved-vs-kind-grouped part
 * ordering; both are fixed in `canonical_paths.ts` and gated in the corpus
 * file. The "against one real deployed reading" half of §G-1 is still OPEN.
 */
import { describe, expect, it } from 'vitest'
import { PariprashnaEventSchema, type PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import { serializeCanonical } from '@/lib/pariprashna/store/serialize'
import type { CanonicalMessage } from '@/lib/pariprashna/store/schema'
import { parsePredictionFlagDetail, runReducerPath, runWriterPath } from './canonical_paths'

// ---------------------------------------------------------------------------
// Fixture — one representative turn, authored directly in the REAL wire shape.
// ---------------------------------------------------------------------------

const MESSAGE_ID = '11111111-1111-1111-1111-111111111111'
const CONVERSATION_ID = '22222222-2222-2222-2222-222222222222'
const TURN_ID = 'turn-canonical-golden-1'
const ASSISTANT_TEXT =
  'Your Moon sits in Purva Bhadrapada, a placement referenced at SIG.MSR.042.'

/** The server-side structured prediction-candidate detection (NOT on the wire
 *  — see the disclosed-asymmetry note above). This is what
 *  `detectPredictionCandidates()` would return; the route feeds it directly
 *  to the writer path and ALSO flattens it into the `flag` below for the
 *  client. */
const PREDICTION_CANDIDATE_DETECTION = {
  text: 'Saturn transit will complete by 2027',
  score: 0.85,
  horizon: '2027',
} as const

/** MUST match route.ts's exact flag-detail format string
 *  (`${d.text} (score=${d.score}${d.horizon ? `, horizon=${d.horizon}` : ''})`)
 *  — this is what the client ACTUALLY receives for a prediction candidate. */
const PREDICTION_FLAG_DETAIL = `${PREDICTION_CANDIDATE_DETECTION.text} (score=${PREDICTION_CANDIDATE_DETECTION.score}, horizon=${PREDICTION_CANDIDATE_DETECTION.horizon})`

function ev<T extends PariprashnaEvent>(raw: T): T {
  // Validate against the REAL protocol schema so a fixture typo/drift is
  // caught here, not silently laundered through two independent paths that
  // both happen to agree on a malformed event.
  return PariprashnaEventSchema.parse(raw) as T
}

const FIXTURE_EVENTS: PariprashnaEvent[] = [
  ev({ type: 'turn.open', seq: 0, t: 0, turn_id: TURN_ID, conversation_id: CONVERSATION_ID, chart_id: '482012f1-710e-4a25-994a-93821f5871aa', model_id: 'claude-opus-4-8[1m]', reading_depth: 'auto', length_tier: 'standard' }),
  ev({ type: 'phase', seq: 1, t: 5, phase: 'plan', status: 'start' }),
  ev({ type: 'phase', seq: 2, t: 120, phase: 'plan', status: 'end', ms: 115 }),
  ev({ type: 'phase', seq: 3, t: 125, phase: 'retrieve', status: 'start', pass_id: 1 }),
  ev({ type: 'activity.upsert', seq: 4, t: 400, key: 'retrieve:ganita_nakshatra_get', label_key: 'Retrieved — Nakshatra', pass_id: 1, status: 'done', count: 2, ms: 275 }),
  ev({ type: 'phase', seq: 5, t: 405, phase: 'retrieve', status: 'end', pass_id: 1, ms: 280 }),
  ev({ type: 'phase', seq: 6, t: 410, phase: 'synthesize', status: 'start', pass_id: 1 }),
  ev({ type: 'block.open', seq: 7, t: 415, block_id: 'blk-1-1', pass_id: 1, role: 'prose' }),
  ev({ type: 'block.delta', seq: 8, t: 460, block_id: 'blk-1-1', delta: 'Your Moon sits in Purva Bhadrapada, ' }),
  ev({ type: 'block.delta', seq: 9, t: 520, block_id: 'blk-1-1', delta: 'a placement referenced at SIG.MSR.042.' }),
  ev({ type: 'block.commit', seq: 10, t: 525, block_id: 'blk-1-1', text: ASSISTANT_TEXT }),
  ev({ type: 'phase', seq: 11, t: 900, phase: 'synthesize', status: 'end', pass_id: 1, ms: 490 }),
  // Note (fidelity to current route.ts behavior): the live route's own
  // `em.citationDefine` call does NOT yet populate reader_label/grade (S-3's
  // richer citation pipeline exists but isn't wired into THIS route today —
  // a separate, pre-existing gap, out of M-2's scope). Fixture mirrors that.
  ev({ type: 'citation.define', seq: 12, t: 905, index: 1, signal_id: 'SIG.MSR.042', layer: 'L2.5', snippet: 'Moon–Purva Bhadrapada placement' }),
  ev({ type: 'grade', seq: 13, t: 910, subject: 'citation_gate', grade: 'PASS' }),
  ev({ type: 'flag', seq: 14, t: 915, code: 'prediction_candidate', level: 'info', detail: PREDICTION_FLAG_DETAIL }),
  ev({ type: 'phase', seq: 15, t: 920, phase: 'finalize', status: 'start' }),
  ev({ type: 'turn.commit', seq: 16, t: 950, turn_id: TURN_ID, conversation_id: CONVERSATION_ID, message_id: MESSAGE_ID, status: 'ok', assistant_chars: ASSISTANT_TEXT.length }),
  ev({ type: 'phase', seq: 17, t: 955, phase: 'finalize', status: 'end' }),
  ev({ type: 'turn.close', seq: 18, t: 960, turn_id: TURN_ID, status: 'ok', ms: 960 }),
]

/** Shared identity — NOT the interesting part of this proof (both a real
 *  client and the real writer derive it from turn.open + fixed constants);
 *  the substantive claim is about the PARTS array. */
const IDENTITY: Pick<CanonicalMessage, 'id' | 'conversation_id' | 'role' | 'schema_version' | 'model_id' | 'provider'> = {
  id: MESSAGE_ID,
  conversation_id: CONVERSATION_ID,
  role: 'assistant',
  schema_version: 1,
  model_id: 'claude-opus-4-8[1m]',
  provider: 'anthropic',
}

// ---------------------------------------------------------------------------
// The gate.
// ---------------------------------------------------------------------------

describe('canonical byte-equality gate — reducer path vs writer path', () => {
  it('serialize(reducer-path parts) === serialize(writer-path parts), byte-for-byte', () => {
    const reducerParts = runReducerPath(FIXTURE_EVENTS)
    const writerParts = runWriterPath(FIXTURE_EVENTS, [PREDICTION_CANDIDATE_DETECTION])

    const reducerSerialized = serializeCanonical(IDENTITY, reducerParts)
    const writerSerialized = serializeCanonical(IDENTITY, writerParts)

    expect(reducerSerialized).toBe(writerSerialized)
  })

  it('sanity: the fixture actually produces non-trivial content (not two empty arrays agreeing vacuously)', () => {
    const writerParts = runWriterPath(FIXTURE_EVENTS, [PREDICTION_CANDIDATE_DETECTION])
    const kinds = writerParts.map((p) => p.kind).sort()
    expect(kinds).toEqual(['citation', 'prediction_candidate', 'text'])
  })

  it('sanity: a genuinely different turn produces a genuinely different serialization', () => {
    const golden = serializeCanonical(IDENTITY, runWriterPath(FIXTURE_EVENTS, [PREDICTION_CANDIDATE_DETECTION]))
    const differentEvents: PariprashnaEvent[] = [
      ev({ type: 'block.open', seq: 0, t: 0, block_id: 'blk-x', pass_id: 1, role: 'prose' }),
      ev({ type: 'block.commit', seq: 1, t: 10, block_id: 'blk-x', text: 'A completely different reading.' }),
    ]
    const different = serializeCanonical(IDENTITY, runWriterPath(differentEvents, []))
    expect(different).not.toBe(golden)
  })

  it('DISCLOSED GAP: prediction_candidate reconstruction is coupled to the flag-detail STRING FORMAT, not a schema-validated round-trip', () => {
    // Simulate a plausible, low-risk-looking future tweak to `em.flag`'s
    // detail string (e.g. a trailing period added for readability). Because
    // this kind's client-side reconstruction is a bespoke regex over free
    // text (not a dedicated, Zod-validated event like `citation.define`), a
    // change like this would silently break EVERY client's reconstruction
    // with zero compile-time signal — while the writer path (fed the
    // server's own structured detection directly, never the flattened wire
    // string) is completely unaffected. This is the concrete, reproducible
    // demonstration of the module header's "disclosed asymmetry": proof,
    // not assertion, of why prediction_candidate is not given the same
    // forever-round-trips guarantee as text/citation.
    const candidate = { text: 'Career growth accelerates', score: 0.72, horizon: '2028' }
    const hypotheticalFutureDetailFormat = `${candidate.text} (score=${candidate.score}, horizon=${candidate.horizon}).`

    const reducerParsed = parsePredictionFlagDetail(hypotheticalFutureDetailFormat)
    expect(reducerParsed).toBeNull() // silently unparseable — reducerStateToCanonicalParts drops it (honest drop, not a crash)

    const writerParts = runWriterPath([], [candidate])
    expect(writerParts).toHaveLength(1) // writer path: unaffected — never touches the wire string at all
    expect((writerParts[0].body as { claim: string }).claim).toBe(candidate.text)
  })
})
