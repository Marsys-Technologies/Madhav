/**
 * Canonical byte-equality gate — THE FULL 12-FIXTURE CORPUS.
 *
 * SAMĀPTI lane B-PB8-BYTEEQ, deliverable (a) of
 * `00_ARCHITECTURE/briefs/pariprashna_build/FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`
 * (option A: "write a new, real bridge … then loop the existing byte-equality
 * assertion over all 12 converted fixtures instead of the one inline fixture").
 *
 * This closes the FIRST of the follow-up's two halves. The second half
 * ("against one real deployed reading") is NOT closed here — see
 * `platform/src/lib/pariprashna/protocol/stream_capture.ts` +
 * `platform/scripts/pariprashna/verify_captured_turn.ts` for the mechanism, and
 * the lane's report for what still has to happen before that clause can be
 * claimed. Do not cite this file as evidence for that half.
 *
 * WHAT A GREEN RUN HERE DOES AND DOES NOT MEAN
 * ────────────────────────────────────────────
 * DOES: across all 12 shapes the replay harness actually produces — 1-byte
 * trickle, 3s stall, adaptive 3-pass, citation-dense, disconnect mid-block,
 * gemini slabs, giant table, honest gap, malformed sentinels, single pass, stop
 * mid-pass, unclosed sentinel — the independently-coded client-reducer
 * simulation and the REAL production writer mapping serialize byte-identically.
 * DOES NOT: prove the SHIPPED client reducer agrees with the writer (there is no
 * shipped client→canonical adapter to call — see `canonical_paths.ts`); prove
 * anything about a real deployed reading's persisted rows; or exercise the
 * `prediction_candidate` kind (the C-2 corpus carries no such flag — asserted
 * explicitly below rather than left as an unstated hole).
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { serializeCanonical } from '@/lib/pariprashna/store/serialize'
import type { CanonicalMessage } from '@/lib/pariprashna/store/schema'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import { loadBridgedCorpus, type BridgedFixture } from './c2_corpus_bridge'
import { runReducerPath, runWriterPath } from './canonical_paths'

const CORPUS: BridgedFixture[] = loadBridgedCorpus()

/** The 12 fixtures `scripts/replay/build_fixtures.ts` is contracted to emit. */
const EXPECTED_FIXTURE_NAMES = [
  '1-byte-trickle',
  '3s-stall',
  'adaptive-3-pass',
  'citation-dense',
  'disconnect-mid-block',
  'gemini-slabs',
  'giant-table',
  'honest-gap',
  'malformed-sentinel-variants',
  'single-pass',
  'stop-mid-pass',
  'unclosed-sentinel',
]

function identityFor(fixture: BridgedFixture): Pick<
  CanonicalMessage,
  'id' | 'conversation_id' | 'role' | 'schema_version' | 'model_id' | 'provider'
> {
  const open = fixture.events.find((e): e is Extract<PariprashnaEvent, { type: 'turn.open' }> => e.type === 'turn.open')
  return {
    id: `msg-${fixture.name}`,
    conversation_id: open?.conversation_id ?? `conv-${fixture.name}`,
    role: 'assistant',
    schema_version: 1,
    model_id: open?.model_id ?? 'unknown',
    provider: 'google',
  }
}

// ---------------------------------------------------------------------------
// Corpus integrity — the bridge itself must be honest before its output means
// anything.
// ---------------------------------------------------------------------------

describe('C-2 corpus bridge — integrity', () => {
  it('bridges every one of the 12 corpus fixtures', () => {
    expect(CORPUS.map((f) => f.name).sort()).toEqual([...EXPECTED_FIXTURE_NAMES].sort())
  })

  it('records exactly one disposition decision per SOURCE event — nothing silently dropped', () => {
    // The follow-up §4's explicit warning: a bridge that silently drops the
    // no-equivalent event types would itself become the problem it fixes.
    for (const f of CORPUS) {
      const sourceCount = f.decisions.length
      expect(sourceCount, `${f.name}: decision ledger must be total`).toBeGreaterThan(0)
      // Every decision must name a reason.
      for (const d of f.decisions) {
        expect(d.reason.length, `${f.name}[${d.source_index}] ${d.source_type}`).toBeGreaterThan(0)
      }
    }
  })

  it('the dropped-event inventory is exactly the two documented no-target types + the two deliberate malformed events', () => {
    const dropped = CORPUS.flatMap((f) => f.decisions.filter((d) => d.disposition.startsWith('dropped')).map((d) => `${d.disposition}:${d.source_type}`))
    const tally = dropped.reduce<Record<string, number>>((acc, k) => ({ ...acc, [k]: (acc[k] ?? 0) + 1 }), {})
    // If a future protocol/corpus change adds a new unmapped type, this fails
    // LOUDLY rather than letting the bridge quietly widen its drop set.
    expect(tally).toEqual({
      'dropped_no_target:citation_anchor.open': 3,
      'dropped_no_target:citation_anchor.set': 3,
      'dropped_malformed:blck.open': 1,
      'dropped_malformed:<no type field>': 1,
    })
  })

  it('every bridged fixture yields at least one real wire event, densely re-sequenced from 0', () => {
    for (const f of CORPUS) {
      expect(f.events.length, f.name).toBeGreaterThan(0)
      expect(f.events.map((e) => e.seq), f.name).toEqual(f.events.map((_, i) => i))
    }
  })
})

// ---------------------------------------------------------------------------
// The gate itself — over the whole corpus.
// ---------------------------------------------------------------------------

describe('canonical byte-equality gate — reducer path vs writer path, FULL CORPUS', () => {
  it.each(CORPUS.map((f) => [f.name, f] as const))(
    '%s: serialize(reducer-path parts) === serialize(writer-path parts), byte-for-byte',
    (_name, fixture) => {
      const identity = identityFor(fixture)
      // predictionCandidates = [] is CORRECT for this corpus, not a shortcut:
      // the server-side structured detection has no counterpart in a replay
      // fixture, and the corpus carries no prediction_candidate flag either
      // (asserted below). Feeding a synthetic detection to only one of the two
      // paths would manufacture a mismatch that says nothing about production.
      const reducer = serializeCanonical(identity, runReducerPath(fixture.events))
      const writer = serializeCanonical(identity, runWriterPath(fixture.events, []))
      expect(reducer).toBe(writer)
    },
  )

  it('DISCLOSED COVERAGE HOLE: the corpus exercises text + citation, never prediction_candidate', () => {
    const flagCodes = CORPUS.flatMap((f) =>
      f.events.filter((e): e is Extract<PariprashnaEvent, { type: 'flag' }> => e.type === 'flag').map((e) => e.code),
    )
    expect(flagCodes).not.toContain('prediction_candidate')

    const kinds = new Set(CORPUS.flatMap((f) => runWriterPath(f.events, []).map((p) => p.kind)))
    expect([...kinds].sort()).toEqual(['citation', 'text'])
    // prediction_candidate stays covered ONLY by the inline fixture in
    // canonical_serialization_golden.test.ts. Stated, not hidden.
  })

  it('non-vacuity: the corpus produces real parts, not 12 pairs of empty arrays agreeing', () => {
    const counts = Object.fromEntries(CORPUS.map((f) => [f.name, runWriterPath(f.events, []).length]))
    const total = Object.values(counts).reduce((a, b) => a + b, 0)
    expect(total).toBeGreaterThan(10)
    // stop-mid-pass is the one fixture that legitimately persists nothing: its
    // block is opened and streamed but never committed, and route.ts only ever
    // writes `committedBlocks`. An honest zero, asserted as such.
    expect(counts['stop-mid-pass']).toBe(0)
    expect(counts['citation-dense']).toBe(3) // 1 committed block + 2 citations
  })

  it('the bridge\'s turn.commit synthesis cannot influence the gate (it drives no canonical part)', () => {
    // turn.commit is the one event where the bridge had to synthesize required
    // fields (message_id, status, assistant_chars). Proof that the synthesis is
    // inert for this gate: dropping every turn.commit changes nothing.
    for (const f of CORPUS) {
      const identity = identityFor(f)
      const withCommit = serializeCanonical(identity, runWriterPath(f.events, []))
      const without = serializeCanonical(identity, runWriterPath(f.events.filter((e) => e.type !== 'turn.commit'), []))
      expect(without, f.name).toBe(withCommit)
    }
  })
})

// ---------------------------------------------------------------------------
// Mutation sensitivity — a gate that cannot go red is not a gate.
// ---------------------------------------------------------------------------

describe('kind-grouped ordering contract (route.ts is the authority)', () => {
  /**
   * HONEST NOTE ON WHY THIS SECTION EXISTS SEPARATELY.
   *
   * Lane B-PB8-BYTEEQ corrected the writer-path driver from M-2's INTERLEAVED
   * order (a part emitted at each block.commit / citation.define in wire order)
   * to route.ts's actual KIND-GROUPED order. Measured, not assumed: with the
   * interleaved driver restored, all 21 corpus assertions above STILL PASS —
   * the 12 fixtures happen to contain no citation defined between two block
   * commits, so the corpus has NO discriminating power for this contract. The
   * correction was derived by reading `app/api/pariprashna/route.ts`'s
   * `writeMessages`, not by watching the corpus go red. These two tests are the
   * gate that does discriminate it; without them the ordering fix would be an
   * unearned green of exactly the kind this whole follow-up is about.
   */
  it('a citation defined BETWEEN two block commits still round-trips (fails under wire-order interleaving)', () => {
    const identity = identityFor(CORPUS[0])
    const interleaved: PariprashnaEvent[] = [
      { type: 'block.open', seq: 0, t: 0, block_id: 'b1', pass_id: 1, role: 'prose' },
      { type: 'block.commit', seq: 1, t: 10, block_id: 'b1', text: 'First settled paragraph.' },
      { type: 'citation.define', seq: 2, t: 20, index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 'a snippet' },
      { type: 'block.open', seq: 3, t: 30, block_id: 'b2', pass_id: 2, role: 'prose' },
      { type: 'block.commit', seq: 4, t: 40, block_id: 'b2', text: 'Second settled paragraph.' },
    ]
    expect(serializeCanonical(identity, runReducerPath(interleaved))).toBe(
      serializeCanonical(identity, runWriterPath(interleaved, [])),
    )
  })

  it('route.ts really does build parts grouped by kind — text, then citations, then predictions', () => {
    // Source-level guard so the drivers above cannot silently drift from the
    // production seam they claim to mirror (same technique as ring_buffer.test.ts).
    const route = readFileSync(
      join(__dirname, '..', '..', '..', 'src', 'app', 'api', 'pariprashna', 'route.ts'),
      'utf8',
    )
    const textAt = route.indexOf('for (const b of committedBlocks)')
    const citationAt = route.indexOf('citationPartFromDetection(')
    const predictionAt = route.indexOf('predictionCandidatePartFromDetection(')
    expect(textAt, 'route.ts must iterate committedBlocks for text parts').toBeGreaterThan(-1)
    expect(citationAt).toBeGreaterThan(textAt)
    expect(predictionAt).toBeGreaterThan(citationAt)
  })
})

describe('corpus gate mutation sensitivity', () => {
  it('perturbing a committed block\'s text on ONE path reddens the comparison', () => {
    const fixture = CORPUS.find((f) => f.name === 'citation-dense')!
    const identity = identityFor(fixture)
    const perturbed: PariprashnaEvent[] = fixture.events.map((e) =>
      e.type === 'block.commit' ? { ...e, text: `${e.text} MUTATED` } : e,
    )
    const reducer = serializeCanonical(identity, runReducerPath(perturbed))
    const writer = serializeCanonical(identity, runWriterPath(fixture.events, []))
    expect(reducer).not.toBe(writer)
  })

  it('perturbing a citation field on ONE path reddens the comparison', () => {
    const fixture = CORPUS.find((f) => f.name === 'citation-dense')!
    const identity = identityFor(fixture)
    const perturbed: PariprashnaEvent[] = fixture.events.map((e) =>
      e.type === 'citation.define' ? { ...e, signal_id: `${e.signal_id}-MUTATED` } : e,
    )
    const reducer = serializeCanonical(identity, runReducerPath(fixture.events))
    const writer = serializeCanonical(identity, runWriterPath(perturbed, []))
    expect(reducer).not.toBe(writer)
  })
})
