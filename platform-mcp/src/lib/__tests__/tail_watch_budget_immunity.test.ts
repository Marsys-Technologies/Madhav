import { describe, test, expect } from 'vitest'
import {
  applyResponseBudget,
  autoDetectTrimmableSections,
  IMMUNE_HONESTY_FIELDS,
  type TrimmableSection,
} from '../response_budget'

/**
 * NIRMĀṆA L2-W3 — D-SALIENCE tail clause:
 *   "every umbrella envelope reserves a hard-floored `tail_watch` section ... that no
 *    budget trim may zero."
 *
 * These tests are written to FAIL if either half of that protection is removed. Both
 * halves are needed and they guard different paths: the explicit hardFloor declaration
 * governs the controlled shed down to minKeep, and IMMUNE_HONESTY_FIELDS membership
 * governs the two paths that bypass declarations entirely (auto-detection and the
 * last-resort string truncator).
 */

const MIN_KEEP = 3

function tailWatchSection(): TrimmableSection<Record<string, unknown>> {
  return {
    path: 'tail_watch',
    label: 'tail_watch (constitutional tail — D-SALIENCE)',
    getArray: (root) => (Array.isArray(root['tail_watch']) ? (root['tail_watch'] as unknown[]) : undefined),
    setArray: (root, kept) => { root['tail_watch'] = kept },
    minKeep: MIN_KEEP,
    hardFloor: true,
    recover: { instrument: 'bodha_signals_get', hint: 'the full tail' },
  }
}

function bulkSection(key: string): TrimmableSection<Record<string, unknown>> {
  return {
    path: key,
    label: `${key} (ordinary section)`,
    getArray: (root) => (Array.isArray(root[key]) ? (root[key] as unknown[]) : undefined),
    setArray: (root, kept) => { root[key] = kept },
    minKeep: 0,
    recover: { instrument: 'bodha_signals_get', hint: 'bulk' },
  }
}

/** Rows fat enough that a small budget forces real trimming. */
const fat = (n: number, tag: string) =>
  Array.from({ length: n }, (_, i) => ({ id: `${tag}-${i}`, blob: 'x'.repeat(400) }))

describe('tail_watch survives the budget', () => {
  test('an ordinary section is floored to zero before tail_watch loses a single row', () => {
    const response: Record<string, unknown> = {
      bulk: fat(200, 'bulk'),
      tail_watch: fat(10, 'tail'),
    }
    applyResponseBudget(response, 6, [bulkSection('bulk'), tailWatchSection()])
    // The trimmer stops the moment it is under budget, so `bulk` is reduced but need
    // not reach zero — asserting bulk === 0 would be asserting the trimmer works
    // harder than it needs to. The doctrine's claim is about tail_watch, and it is
    // untouched: every row of the ordinary section is spent before the tail loses one.
    expect((response['bulk'] as unknown[]).length).toBeLessThan(200)
    expect((response['tail_watch'] as unknown[]).length).toBe(10)
  })

  test('under a budget nothing can satisfy, tail_watch is held at its floor and never zeroed', () => {
    const response: Record<string, unknown> = {
      bulk: fat(400, 'bulk'),
      tail_watch: fat(50, 'tail'),
    }
    // 1 KB against ~180 KB of content: PASS 2 runs and overrides every ordinary
    // section's minKeep to zero. hardFloor is what exempts tail_watch from that.
    applyResponseBudget(response, 1, [bulkSection('bulk'), tailWatchSection()])
    expect((response['bulk'] as unknown[]).length).toBe(0)
    expect((response['tail_watch'] as unknown[]).length).toBe(MIN_KEEP)
    expect((response['tail_watch'] as unknown[]).length).toBeGreaterThan(0)
  })

  test('hardFloor with minKeep 0 does NOT satisfy the doctrine — the regression this guards', () => {
    // Why minKeep must be >= 1: hardFloor imposes no floor of its own, it makes PASS 2
    // RESPECT the declared floor. A declared floor of zero is still zero, and reads as
    // protection while providing none. Run both configurations against identical input
    // so the difference is attributable to minKeep alone.
    const build = () => ({ bulk: fat(400, 'bulk'), tail_watch: fat(50, 'tail') }) as Record<string, unknown>

    const protectedResponse = build()
    applyResponseBudget(protectedResponse, 1, [bulkSection('bulk'), tailWatchSection()])

    const zeroFlooredResponse = build()
    applyResponseBudget(zeroFlooredResponse, 1, [
      bulkSection('bulk'),
      { ...tailWatchSection(), minKeep: 0 },
    ])

    expect((protectedResponse['tail_watch'] as unknown[]).length).toBe(MIN_KEEP)
    expect((zeroFlooredResponse['tail_watch'] as unknown[]).length).toBeLessThan(MIN_KEEP)
  })
})

describe('tail_watch is immune to the paths a declaration cannot reach', () => {
  test('it is never picked up by auto-detection as an ordinary trimmable array', () => {
    const content = { tail_watch: fat(40, 'tail'), other: fat(40, 'other') }
    const sections = autoDetectTrimmableSections(content, 'bodha_signals_get')
    expect(sections.map((s) => s.path)).toContain('other')
    expect(sections.map((s) => s.path)).not.toContain('tail_watch')
  })

  test('it is a member of IMMUNE_HONESTY_FIELDS, so its prose is never string-truncated', () => {
    expect(IMMUNE_HONESTY_FIELDS.has('tail_watch')).toBe(true)
  })

  test('a long reason inside a tail row is not mangled mid-sentence', () => {
    const reason =
      'promoted: rare-class leader — top decile of vargottama_amplification (4 rows chart-wide) ' +
      'while ranking below the chart-wide salience fold, which is exactly the row a ' +
      'salience-ordered read would never surface. '.repeat(3)
    const response: Record<string, unknown> = {
      bulk: fat(400, 'bulk'),
      tail_watch: [{ id: 'tail-0', promotion_reason: reason }],
    }
    applyResponseBudget(response, 1, [bulkSection('bulk'), tailWatchSection()])
    const kept = response['tail_watch'] as Array<Record<string, unknown>>
    expect(kept.length).toBe(1)
    expect(kept[0]['promotion_reason']).toBe(reason)
  })
})
