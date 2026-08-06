/**
 * explain_contrast.test.ts — ṢAḌ-DARŚANA W3 Item 34: Contrastive EXPLAIN (field diffs).
 *
 * Tests the pure field-diff logic exported from explain.ts:
 * `computeFieldDiff(current, baseline)` → { new_windows, closed_windows,
 * intensified_windows, weakened_windows } — each a list of typed window-diff rows.
 *
 * Property test:
 * contrast(A→B).new_windows == contrast(B→A).closed_windows  (anti-symmetry)
 *
 * This is the serving-layer counterpart to the Python `compute_field_diff` in
 * stage65_insights.py. The TypeScript version is used by `kala_explain_get`'s
 * `contrast` response section when a `contrast_baseline` parameter is supplied.
 * TDD: these tests are written BEFORE the implementation (§N.8 / brief item 34).
 */
import { describe, it, expect } from 'vitest'
import { computeFieldDiff, type FieldWindowSlice } from './explain.js'

function win(
  window_id: string,
  event_class: string,
  lambda_peak: number,
  fact_ids: string[] = [],
): FieldWindowSlice {
  return { window_id, event_class, lambda_peak, fact_ids }
}

describe('computeFieldDiff — Item 34 (contrastive EXPLAIN)', () => {
  it('detects a new window present in current but not in baseline', () => {
    const diff = computeFieldDiff([win('wA', 'career_change', 0.05)], [])
    const ids = diff.new_windows.map((w) => w.window_id)
    expect(ids).toContain('wA')
    expect(diff.closed_windows).toHaveLength(0)
  })

  it('detects a closed window present in baseline but not in current', () => {
    const diff = computeFieldDiff([], [win('wOld', 'career_change', 0.05)])
    const ids = diff.closed_windows.map((w) => w.window_id)
    expect(ids).toContain('wOld')
    expect(diff.new_windows).toHaveLength(0)
  })

  it('detects an intensified window when lambda rose significantly', () => {
    // current lambda = 0.20, baseline lambda = 0.05 → ln(0.20/0.05) ≈ 1.39 > 0.5
    const diff = computeFieldDiff(
      [win('wX', 'marriage', 0.20)],
      [win('wX', 'marriage', 0.05)],
    )
    const ids = diff.intensified_windows.map((w) => w.window_id)
    expect(ids).toContain('wX')
    expect(diff.new_windows).toHaveLength(0)
    expect(diff.closed_windows).toHaveLength(0)
  })

  it('detects a weakened window when lambda dropped significantly', () => {
    // current lambda = 0.02, baseline lambda = 0.15 → ln(0.15/0.02) ≈ 2.01 > 0.5
    const diff = computeFieldDiff(
      [win('wY', 'wealth', 0.02)],
      [win('wY', 'wealth', 0.15)],
    )
    const ids = diff.weakened_windows.map((w) => w.window_id)
    expect(ids).toContain('wY')
    expect(diff.new_windows).toHaveLength(0)
    expect(diff.closed_windows).toHaveLength(0)
  })

  it('a window with unchanged lambda does not appear in any list', () => {
    const diff = computeFieldDiff(
      [win('wZ', 'health', 0.05)],
      [win('wZ', 'health', 0.05)],
    )
    expect(diff.new_windows).toHaveLength(0)
    expect(diff.closed_windows).toHaveLength(0)
    expect(diff.intensified_windows).toHaveLength(0)
    expect(diff.weakened_windows).toHaveLength(0)
  })

  it('fact_ids from the current window ride the new_windows row (B.3 provenance)', () => {
    const diff = computeFieldDiff([win('wN', 'career_change', 0.05, ['f1', 'f2'])], [])
    const row = diff.new_windows.find((w) => w.window_id === 'wN')!
    expect(row).toBeDefined()
    expect(row.fact_ids).toContain('f1')
    expect(row.fact_ids).toContain('f2')
  })

  it('fact_ids from the baseline window ride the closed_windows row', () => {
    const diff = computeFieldDiff([], [win('wC', 'marriage', 0.05, ['bF'])])
    const row = diff.closed_windows.find((w) => w.window_id === 'wC')!
    expect(row).toBeDefined()
    expect(row.fact_ids).toContain('bF')
  })

  it('the result always has all four keys, even when all lists are empty', () => {
    const diff = computeFieldDiff([], [])
    expect(diff).toHaveProperty('new_windows')
    expect(diff).toHaveProperty('closed_windows')
    expect(diff).toHaveProperty('intensified_windows')
    expect(diff).toHaveProperty('weakened_windows')
    expect(diff.new_windows).toEqual([])
    expect(diff.closed_windows).toEqual([])
    expect(diff.intensified_windows).toEqual([])
    expect(diff.weakened_windows).toEqual([])
  })

  it('property: anti-symmetry — new in A→B equals closed in B→A', () => {
    const wA = win('wA', 'career_change', 0.05)
    const wB = win('wB', 'marriage', 0.08)
    const diffAtoB = computeFieldDiff([wB], [wA])
    const diffBtoA = computeFieldDiff([wA], [wB])
    const newIds = diffAtoB.new_windows.map((w) => w.window_id).sort()
    const closedIds = diffBtoA.closed_windows.map((w) => w.window_id).sort()
    expect(newIds).toEqual(closedIds)
  })

  it('intensified_window row carries the delta_ln_lambda field', () => {
    const diff = computeFieldDiff(
      [win('wX', 'career_change', 0.20)],
      [win('wX', 'career_change', 0.05)],
    )
    const row = diff.intensified_windows.find((w) => w.window_id === 'wX')!
    expect(row).toBeDefined()
    expect(typeof row.delta_ln_lambda).toBe('number')
    // ln(0.20/0.05) ≈ 1.386
    expect(Math.abs(row.delta_ln_lambda - Math.log(0.20 / 0.05))).toBeLessThan(1e-9)
  })

  it('weakened_window row carries the delta_ln_lambda field (negative)', () => {
    const diff = computeFieldDiff(
      [win('wY', 'wealth', 0.02)],
      [win('wY', 'wealth', 0.15)],
    )
    const row = diff.weakened_windows.find((w) => w.window_id === 'wY')!
    expect(row.delta_ln_lambda).toBeLessThan(0)
    expect(Math.abs(row.delta_ln_lambda - Math.log(0.02 / 0.15))).toBeLessThan(1e-9)
  })
})
