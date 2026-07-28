/**
 * Golden protocol test — recorded event stream -> reducer -> final client
 * state.
 *
 * Asserts:
 *  1. Determinism: replaying the same fixture twice yields byte-identical
 *     final-state snapshots.
 *  2. Idempotent duplicate handling: re-delivering an already-applied event
 *     id (redelivery, at-least-once relay) is a no-op — it must NOT be
 *     double-applied (e.g. a duplicated block.delta must not appear twice in
 *     the accumulated text).
 *  3. Per-fixture structural sanity (block counts, commit state, honest-gap
 *     surfacing, malformed-frame tolerance) as a regression net for the
 *     fixture set itself.
 *
 * Run: `npm run pariprashna:reducer:test` (or plain `vitest run` picks this
 * up as part of the normal suite — see vitest.config.ts `exclude` list,
 * which does NOT exclude tests/pariprashna/**, only tests/e2e/**).
 */
import { describe, expect, it } from 'vitest'
import { readFileSync, readdirSync } from 'fs'
import { join } from 'path'
import { applyEvent, createInitialState, reduceAll, snapshot } from './reducer.mjs'
import type { FixtureSpec } from '../../../scripts/replay/fixture_types'

const FIXTURES_DIR = join(__dirname, '..', 'fixtures')

function loadFixture(name: string): FixtureSpec {
  const raw = readFileSync(join(FIXTURES_DIR, `${name}.json`), 'utf8')
  return JSON.parse(raw) as FixtureSpec
}

function allFixtureNames(): string[] {
  return readdirSync(FIXTURES_DIR)
    .filter((f) => f.endsWith('.json'))
    .map((f) => f.replace(/\.json$/, ''))
    .sort()
}

describe('golden protocol — determinism', () => {
  for (const name of allFixtureNames()) {
    it(`${name}: replaying twice yields identical final state`, () => {
      const fixture = loadFixture(name)
      const events = fixture.events.map((e) => e.event)

      const runA = snapshot(reduceAll(events, { strict: false }))
      const runB = snapshot(reduceAll(events, { strict: false }))

      expect(JSON.stringify(runB)).toBe(JSON.stringify(runA))
    })
  }
})

describe('golden protocol — idempotent duplicate-id handling', () => {
  for (const name of allFixtureNames()) {
    it(`${name}: re-delivering every event id a second time changes nothing`, () => {
      const fixture = loadFixture(name)
      const events = fixture.events.map((e) => e.event)

      const baseline = snapshot(reduceAll(events, { strict: false }))

      // Interleave a duplicate of every event immediately after itself —
      // the harshest possible redelivery pattern.
      const withDuplicates = events.flatMap((e) => [e, e])
      const afterDuplicates = snapshot(reduceAll(withDuplicates, { strict: false }))

      // Structural state must be identical...
      expect(afterDuplicates.blocks).toEqual(baseline.blocks)
      expect(afterDuplicates.activities).toEqual(baseline.activities)
      expect(afterDuplicates.citation_anchors).toEqual(baseline.citation_anchors)
      expect(afterDuplicates.citations).toEqual(baseline.citations)
      expect(afterDuplicates.turn_commit).toEqual(baseline.turn_commit)
      expect(afterDuplicates.turn_close).toEqual(baseline.turn_close)
      // ...and the reducer must have visibly recognized and dropped exactly
      // one duplicate per original event (proves this isn't passing by
      // accident because the events were no-ops to begin with).
      expect(afterDuplicates.duplicates_dropped).toBe(events.length)
      expect(afterDuplicates.events_applied).toBe(baseline.events_applied)
    })
  }
})

describe('golden protocol — specific negative-space assertion', () => {
  it('a genuinely different event stream produces a genuinely different snapshot (sanity check on the equality assertions above)', () => {
    const a = loadFixture('single-pass')
    const b = loadFixture('honest-gap')
    const snapA = snapshot(reduceAll(a.events.map((e) => e.event), { strict: false }))
    const snapB = snapshot(reduceAll(b.events.map((e) => e.event), { strict: false }))
    expect(JSON.stringify(snapA)).not.toBe(JSON.stringify(snapB))
  })
})

describe('golden protocol — per-fixture structural assertions', () => {
  it('adaptive-3-pass: three passes reach done status, 2 blocks committed', () => {
    const fixture = loadFixture('adaptive-3-pass')
    const state = reduceAll(fixture.events.map((e) => e.event))
    const snap = snapshot(state)
    expect(snap.activities.filter((a: { status: string }) => a.status === 'done')).toHaveLength(3)
    expect(snap.blocks.every((b: { committed: boolean }) => b.committed)).toBe(true)
    expect(snap.turn_commit?.block_count).toBe(2)
  })

  it('disconnect-mid-block: block never commits (final commit event was never actually sent)', () => {
    const fixture = loadFixture('disconnect-mid-block')
    // Simulate the transport truncation the replay server performs: only
    // events up to and including abrupt_end_after_seq are ever delivered.
    const delivered = fixture.events
      .map((e) => e.event)
      .filter((e) => (e as { seq: number }).seq <= (fixture.abrupt_end_after_seq ?? Infinity))
    const snap = snapshot(reduceAll(delivered, { strict: false }))
    expect(snap.blocks.find((b: { id: string }) => b.id === 'b1')?.committed).toBe(false)
    expect(snap.turn_close).toBeNull()
  })

  it('unclosed-sentinel: block commits but turn never closes', () => {
    const fixture = loadFixture('unclosed-sentinel')
    const snap = snapshot(reduceAll(fixture.events.map((e) => e.event)))
    expect(snap.blocks.find((b: { id: string }) => b.id === 'b1')?.committed).toBe(true)
    expect(snap.turn_commit).toBeNull()
    expect(snap.turn_close).toBeNull()
  })

  it('malformed-sentinel-variants: malformed frames are dropped, valid frames after them still apply', () => {
    const fixture = loadFixture('malformed-sentinel-variants')
    // safeParse each raw payload the way a real client would, only feeding
    // schema-valid events to the reducer — this is the client-side contract
    // the fixture exists to exercise (see events.ts safeParseEvent).
    let state = createInitialState()
    let schemaRejected = 0
    for (const entry of fixture.events) {
      const raw = entry.event as Record<string, unknown>
      const looksValid =
        typeof raw.id === 'string' &&
        typeof raw.seq === 'number' &&
        typeof raw.type === 'string' &&
        [
          'turn.open', 'phase', 'activity.upsert', 'block.open', 'block.delta',
          'block.commit', 'citation_anchor.open', 'citation_anchor.set', 'citation.define', 'flag',
          'grade', 'turn.commit', 'turn.close', 'error',
        ].includes(raw.type as string)
      if (!looksValid) {
        schemaRejected += 1
        continue
      }
      state = applyEvent(state, raw, { strict: false })
    }
    const snap = snapshot(state)
    expect(schemaRejected).toBeGreaterThanOrEqual(3) // variants A, B(missing field slips this coarse check off; C, D do not)
    expect(snap.blocks.find((b: { id: string }) => b.id === 'b1')?.committed).toBe(true)
    expect(snap.turn_close?.reason).toBe('complete')
  })

  it('honest-gap: seam resolves to null citation AND a flag reports the gap (never silently dropped)', () => {
    const fixture = loadFixture('honest-gap')
    const snap = snapshot(reduceAll(fixture.events.map((e) => e.event)))
    const seam = snap.citation_anchors.find((s: { anchor_id: string }) => s.anchor_id === 's1')
    expect(seam?.citation_id).toBeNull()
    expect(snap.flags.some((f: { flag_key: string }) => f.flag_key === 'honest_gap.no_citation_found')).toBe(true)
  })

  it('stop-mid-pass: turn closes with reason "stopped", block and activity remain unresolved', () => {
    const fixture = loadFixture('stop-mid-pass')
    const snap = snapshot(reduceAll(fixture.events.map((e) => e.event)))
    expect(snap.turn_close?.reason).toBe('stopped')
    expect(snap.blocks.find((b: { id: string }) => b.id === 'b1')?.committed).toBe(false)
    expect(snap.activities.find((a: { key: string }) => a.key === 'pass-1-retrieval')?.status).toBe('active')
  })

  it('strict mode throws on a delta targeting an already-committed block (the G-TRANSMUTE enforcement point)', () => {
    let state = createInitialState()
    state = applyEvent(state, { id: '1', seq: 0, t: 0, type: 'turn.open', turn_id: 'x' })
    state = applyEvent(state, { id: '2', seq: 1, t: 0, type: 'block.open', block_id: 'b1', kind: 'paragraph', index: 0 })
    state = applyEvent(state, { id: '3', seq: 2, t: 0, type: 'block.delta', block_id: 'b1', text: 'hi' })
    state = applyEvent(state, { id: '4', seq: 3, t: 0, type: 'block.commit', block_id: 'b1', final_text: 'hi' })
    expect(() =>
      applyEvent(state, { id: '5', seq: 4, t: 0, type: 'block.delta', block_id: 'b1', text: ' more' }),
    ).toThrow(/ALREADY-COMMITTED/)
  })
})
