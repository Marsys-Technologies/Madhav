#!/usr/bin/env tsx
/**
 * Paripraśna replay harness — fixture builder.
 *
 * Generates the 12 named fixtures required by the PB-1/C-2 brief into
 * `platform/tests/pariprashna/fixtures/<name>.json`. Run via:
 *
 *   npm run pariprashna:fixtures:build
 *
 * Fixture content is deliberately generic/placeholder prose — these are
 * harness test fixtures, not real chart readings, and must never be mistaken
 * for production output (see CLAUDE.md B.10).
 */
import { mkdirSync, writeFileSync } from 'fs'
import { join } from 'path'
import { buildFixture, Turn } from './fixture_builder'
import type { FixtureSpec } from './fixture_types'

const OUT_DIR = join(__dirname, '..', '..', 'tests', 'pariprashna', 'fixtures')

const PLACEHOLDER_SENTENCES = [
  'The retrieval layer surfaces three corroborating signals for this window.',
  'A structural tension appears between the timing anchor and the natal placement.',
  'This pattern recurs across two independent sub-systems, which raises its weight.',
  'No contradiction was found against the prior turn\'s working hypothesis.',
  'The confidence band widens once the secondary corroboration is included.',
]

function sentence(i: number): string {
  return PLACEHOLDER_SENTENCES[i % PLACEHOLDER_SENTENCES.length]
}

// ─── 1. adaptive-3-pass ─────────────────────────────────────────────────────

function adaptive3Pass(): FixtureSpec {
  return buildFixture(
    'adaptive-3-pass',
    'Three sequential retrieval passes (adaptive depth escalation) followed by a two-block synthesis.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'deep_dive' }, 0)
      t.push('phase', { phase: 'planning', label: 'Scoping the question' }, 30)

      for (let pass = 1; pass <= 3; pass++) {
        const passId = `pass-${pass}`
        t.push('activity.upsert', {
          key: `${passId}-retrieval`,
          pass_id: passId,
          label_key: 'activity.retrieval.pass',
          status: 'pending',
        }, 20)
        t.push('activity.upsert', {
          key: `${passId}-retrieval`,
          pass_id: passId,
          label_key: 'activity.retrieval.pass',
          status: 'active',
          detail: `pass ${pass} of 3`,
        }, 40)
        t.push('activity.upsert', {
          key: `${passId}-retrieval`,
          pass_id: passId,
          label_key: 'activity.retrieval.pass',
          status: 'done',
          detail: `pass ${pass} of 3 — 4 signals`,
        }, 60)
      }

      t.push('phase', { phase: 'synthesizing' }, 30)

      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      for (let i = 0; i < 4; i++) {
        t.push('block.delta', { block_id: 'b1', text: sentence(i) + ' ' }, 15)
      }
      t.push('block.commit', {
        block_id: 'b1',
        final_text: [0, 1, 2, 3].map(sentence).map((s) => s + ' ').join(''),
      }, 10)

      t.push('block.open', { block_id: 'b2', kind: 'heading', index: 1 }, 20)
      t.push('block.delta', { block_id: 'b2', text: 'Summary across passes' }, 15)
      t.push('block.commit', { block_id: 'b2', final_text: 'Summary across passes' }, 10)

      t.push('turn.commit', { turn_id: t.turnId, block_count: 2, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 2. single-pass ─────────────────────────────────────────────────────────

function singlePass(): FixtureSpec {
  return buildFixture(
    'single-pass',
    'Minimal single retrieval pass, one paragraph block.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('activity.upsert', {
        key: 'pass-1-retrieval',
        pass_id: 'pass-1',
        label_key: 'activity.retrieval.pass',
        status: 'done',
        detail: 'pass 1 of 1 — 2 signals',
      }, 40)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(0) }, 20)
      t.push('block.commit', { block_id: 'b1', final_text: sentence(0) }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 3. gemini-slabs ────────────────────────────────────────────────────────

function geminiSlabs(): FixtureSpec {
  return buildFixture(
    'gemini-slabs',
    'Few large text "slabs" per delta (provider batches tokens), rather than token-by-token streaming.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      const slabs = [
        PLACEHOLDER_SENTENCES.slice(0, 3).join(' ') + ' ',
        PLACEHOLDER_SENTENCES.slice(3).join(' ') + ' ',
        PLACEHOLDER_SENTENCES.join(' '),
      ]
      for (const slab of slabs) {
        t.push('block.delta', { block_id: 'b1', text: slab }, 250)
      }
      t.push('block.commit', {
        block_id: 'b1',
        final_text: slabs.join(''),
      }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 4. 1-byte-trickle ──────────────────────────────────────────────────────

function oneByteTrickle(): FixtureSpec {
  return buildFixture(
    '1-byte-trickle',
    'Many single-character deltas, AND the transport itself dribbles bytes one at a time (chunk_bytes=1) — stresses SSE frame reassembly and render coalescing simultaneously.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 10)
      const text = sentence(0)
      let acc = ''
      for (const ch of text) {
        acc += ch
        t.push('block.delta', { block_id: 'b1', text: ch }, 4)
      }
      t.push('block.commit', { block_id: 'b1', final_text: acc }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
    { chunk_bytes: 1 },
  )
}

// ─── 5. 3s-stall ────────────────────────────────────────────────────────────

function threeSecondStall(): FixtureSpec {
  return buildFixture(
    '3s-stall',
    'A 3000ms gap mid-stream with no events — client must not shift layout, crash, or show a phantom commit while waiting.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(0).slice(0, 30) }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(0).slice(30) }, 3000)
      t.push('block.commit', { block_id: 'b1', final_text: sentence(0) }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 6. disconnect-mid-block ────────────────────────────────────────────────

function disconnectMidBlock(): FixtureSpec {
  const turn = new Turn('disconnect-mid-block')
  turn.push('turn.open', { turn_id: turn.turnId, reading_depth: 'standard' }, 0)
  turn.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
  turn.push('block.delta', { block_id: 'b1', text: sentence(0).slice(0, 20) }, 20)
  const cutSeq = turn.lastSeq
  turn.push('block.delta', { block_id: 'b1', text: sentence(0).slice(20, 40) }, 20)
  // Events after this point are defined so the fixture reads naturally, but
  // abrupt_end_after_seq means the server never actually sends them — the
  // socket is killed right after the delta above.
  turn.push('block.commit', { block_id: 'b1', final_text: sentence(0) }, 10)
  turn.push('turn.commit', { turn_id: turn.turnId, block_count: 1, citation_count: 0 }, 10)
  turn.push('turn.close', { turn_id: turn.turnId, reason: 'complete' }, 5)
  return {
    name: 'disconnect-mid-block',
    description:
      'Connection is killed mid-block (after a delta, before commit) — simulates a network drop. block.commit/turn.close are defined but never sent.',
    events: turn.entries,
    abrupt_end_after_seq: turn.lastSeq - 3, // right after the 2nd delta
  }
}

// ─── 7. unclosed-sentinel ───────────────────────────────────────────────────

function unclosedSentinel(): FixtureSpec {
  return buildFixture(
    'unclosed-sentinel',
    'Stream ends gracefully (server closes the HTTP response normally) but never emits turn.commit/turn.close — the "hung turn" case, distinct from a hard disconnect.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(0) }, 20)
      t.push('block.commit', { block_id: 'b1', final_text: sentence(0) }, 10)
      // Deliberately no turn.commit / turn.close.
    },
  )
}

// ─── 8. malformed-sentinel-variants ─────────────────────────────────────────

function malformedSentinelVariants(): FixtureSpec {
  const t = new Turn('malformed-sentinel-variants')
  t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
  t.push('activity.upsert', {
    key: 'pass-1-retrieval',
    pass_id: 'pass-1',
    label_key: 'activity.retrieval.pass',
    status: 'done',
  }, 20)

  // Variant A: unknown event type (typo'd discriminant).
  t.pushRaw({ id: `${t.turnId}-bad-a`, seq: t.lastSeq + 1, t: 999, type: 'blck.open', block_id: 'x' }, 15)

  // Variant B: known type, required field missing.
  t.pushRaw({ id: `${t.turnId}-bad-b`, seq: t.lastSeq + 1, t: 999, type: 'block.delta', text: 'orphan text' }, 15)

  // Variant C: known type, wrong field TYPE (seq as string, not number).
  t.pushRaw({
    id: `${t.turnId}-bad-c`,
    seq: 'not-a-number',
    t: 999,
    type: 'block.open',
    block_id: 'y',
    kind: 'paragraph',
    index: 0,
  }, 15)

  // Variant D: valid envelope shape, but `type` is entirely absent.
  t.pushRaw({ id: `${t.turnId}-bad-d`, seq: t.lastSeq + 1, t: 999, block_id: 'z', text: 'no type field' }, 15)

  // Recovery: a fully valid block after the noise — proves the reducer keeps
  // going instead of wedging on the first bad frame.
  t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
  t.push('block.delta', { block_id: 'b1', text: sentence(0) }, 20)
  t.push('block.commit', { block_id: 'b1', final_text: sentence(0) }, 10)
  t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
  t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)

  return {
    name: 'malformed-sentinel-variants',
    description:
      'Mixes 4 deliberately malformed event payloads among valid ones — reducer/client must skip malformed frames (safeParseEvent) and keep processing.',
    events: t.entries,
  }
}

// ─── 9. citation-dense ──────────────────────────────────────────────────────

function citationDense(): FixtureSpec {
  return buildFixture(
    'citation-dense',
    'One block with two inline citation seams, one confirmed and one catalog_only — exercises chip density + verification tiering.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(1) + ' ' }, 15)
      t.push('seam.open', { seam_id: 's1', block_id: 'b1', anchor_offset: sentence(1).length + 1 }, 10)
      t.push('block.delta', { block_id: 'b1', text: sentence(2) + ' ' }, 15)
      t.push('seam.open', {
        seam_id: 's2',
        block_id: 'b1',
        anchor_offset: sentence(1).length + 1 + sentence(2).length + 1,
      }, 10)
      const finalText = sentence(1) + ' ' + sentence(2) + ' '
      t.push('block.commit', { block_id: 'b1', final_text: finalText }, 10)
      t.push('citation.define', {
        citation_id: 'c1',
        label: 'BPHS 6.12 (fixture)',
        verification: 'confirmed',
        source_ref: 'fixture://citation-dense/c1',
      }, 10)
      t.push('seam.set', { seam_id: 's1', citation_id: 'c1' }, 10)
      t.push('citation.define', {
        citation_id: 'c2',
        label: 'Saravali 4.3 (fixture, unverified)',
        verification: 'catalog_only',
        source_ref: 'fixture://citation-dense/c2',
      }, 10)
      t.push('seam.set', { seam_id: 's2', citation_id: 'c2' }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 2 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 10. giant-table ────────────────────────────────────────────────────────

function giantTable(): FixtureSpec {
  return buildFixture(
    'giant-table',
    'A 30-row markdown table streamed row-by-row — exercises G-CLS/G-VIEWPORT/G-CARET under a large, growing block.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'tbl1', kind: 'table', index: 0 }, 20)
      let acc = '| Period | Ruler | Signal |\n|---|---|---|\n'
      t.push('block.delta', { block_id: 'tbl1', text: '| Period | Ruler | Signal |\n|---|---|---|\n' }, 10)
      for (let row = 1; row <= 30; row++) {
        const line = `| P${row} | R${(row % 9) + 1} | S${row} |\n`
        acc += line
        t.push('block.delta', { block_id: 'tbl1', text: line }, 8)
      }
      t.push('block.commit', { block_id: 'tbl1', final_text: acc }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 11. honest-gap ─────────────────────────────────────────────────────────

function honestGap(): FixtureSpec {
  return buildFixture(
    'honest-gap',
    'A seam resolves to citation_id: null (no source found) and a flag reports the gap — must render as an honest gap, never silently dropped.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(3) + ' ' }, 15)
      t.push('seam.open', { seam_id: 's1', block_id: 'b1', anchor_offset: sentence(3).length + 1 }, 10)
      t.push('block.commit', { block_id: 'b1', final_text: sentence(3) + ' ' }, 10)
      t.push('seam.set', { seam_id: 's1', citation_id: null }, 10)
      t.push('flag', {
        flag_key: 'honest_gap.no_citation_found',
        severity: 'notice',
        detail: 'No classical source located for this claim within the current pass budget.',
      }, 10)
      t.push('turn.commit', { turn_id: t.turnId, block_count: 1, citation_count: 0 }, 10)
      t.push('turn.close', { turn_id: t.turnId, reason: 'complete' }, 5)
    },
  )
}

// ─── 12. stop-mid-pass ──────────────────────────────────────────────────────

function stopMidPass(): FixtureSpec {
  return buildFixture(
    'stop-mid-pass',
    'User hits Stop while a retrieval pass is still active and a block is still open — turn.close(reason:"stopped") arrives with no commit for either.',
    (t) => {
      t.push('turn.open', { turn_id: t.turnId, reading_depth: 'standard' }, 0)
      t.push('activity.upsert', {
        key: 'pass-1-retrieval',
        pass_id: 'pass-1',
        label_key: 'activity.retrieval.pass',
        status: 'active',
        detail: 'pass 1 of 2',
      }, 20)
      t.push('block.open', { block_id: 'b1', kind: 'paragraph', index: 0 }, 20)
      t.push('block.delta', { block_id: 'b1', text: sentence(0).slice(0, 25) }, 20)
      // No block.commit, no further activity resolution, no turn.commit —
      // straight to a stopped close.
      t.push('turn.close', { turn_id: t.turnId, reason: 'stopped' }, 30)
    },
  )
}

// ─── main ───────────────────────────────────────────────────────────────────

const FIXTURES: (() => FixtureSpec)[] = [
  adaptive3Pass,
  singlePass,
  geminiSlabs,
  oneByteTrickle,
  threeSecondStall,
  disconnectMidBlock,
  unclosedSentinel,
  malformedSentinelVariants,
  citationDense,
  giantTable,
  honestGap,
  stopMidPass,
]

function main(): void {
  mkdirSync(OUT_DIR, { recursive: true })
  for (const build of FIXTURES) {
    const spec = build()
    const path = join(OUT_DIR, `${spec.name}.json`)
    writeFileSync(path, JSON.stringify(spec, null, 2) + '\n', 'utf8')
    console.log(`[build_fixtures] wrote ${spec.events.length} events -> ${path}`)
  }
  console.log(`[build_fixtures] ${FIXTURES.length} fixtures built.`)
}

main()
