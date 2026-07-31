/**
 * SAMĀPTI B-WATCHDOG-LIT · DVA Ruling 10 · finding F3.
 *
 * Regression guard for the falsely-lit build-state watchdog defect: the stuck-asset
 * reaper in platform/src/app/api/cockpit/watchdog/route.ts promoted ANY 'building'
 * asset with a stale (>15 min) heartbeat to 'lit' as soon as it saw rows present,
 * with zero consultation of substep-plan completeness. A multi-substep writer
 * commits per substep, so rows exist from substep 1 of N onward — a 303-substep
 * sweep dead at substep 78 was reported as complete and unblocked its downstream.
 *
 * These tests pin the predicate itself (classifyStuckCandidate). The first test in
 * each pair is the one that FAILS against the pre-fix code — the pre-fix predicate
 * was literally `rowsPresent ? 'rescue-lit' : 'error'`, with no has_substeps arm.
 *
 * A live-DB counterpart driving the real route handler + real SQL against a real
 * Postgres lives in tests/integration/watchdog_substep_lit_guard.db.test.ts.
 */
import { describe, it, expect } from 'vitest'
import {
  classifyStuckCandidate,
  type StuckCandidate,
} from '@/app/api/cockpit/watchdog/classifyStuckCandidate'

const heavy: StuckCandidate = { has_substeps: true, target_floor: 100 }
const light: StuckCandidate = { has_substeps: false, target_floor: 100 }
const planless: StuckCandidate = { has_substeps: null, target_floor: 100 }

describe('classifyStuckCandidate — the F3 falsely-lit guard', () => {
  it('NEVER promotes a plan-bearing asset to lit, even with many rows present', () => {
    // The exact reported shape: ka_gochara_sweep-class writer, 78/303 substeps in,
    // rows already committed by those 78, heartbeat stale. Pre-fix: 'rescue-lit'.
    expect(classifyStuckCandidate(heavy, 25_000)).toBe('withhold-incomplete')
  })

  it('withholds regardless of how many rows the probe found', () => {
    for (const rows of [1, 42, 25_000, 1_000_000]) {
      expect(classifyStuckCandidate(heavy, rows)).toBe('withhold-incomplete')
    }
  })

  it('withholds for a plan-bearing asset whose target_floor=0 declares zero rows complete', () => {
    // target_floor=0 is enough to call a PLANLESS asset complete (§N.4), but it
    // still says nothing about whether a substep plan finished.
    expect(classifyStuckCandidate({ has_substeps: true, target_floor: 0 }, 0))
      .toBe('withhold-incomplete')
  })

  it('still marks a plan-bearing asset with NO data as error, not incomplete', () => {
    // Unchanged behaviour: no data present is a genuine stuck writer.
    expect(classifyStuckCandidate(heavy, 0)).toBe('error')
    expect(classifyStuckCandidate(heavy, null)).toBe('error')
  })
})

describe('classifyStuckCandidate — planless assets keep the D-3 Part B rescue', () => {
  it('rescues a has_substeps=false asset with rows present (unchanged)', () => {
    expect(classifyStuckCandidate(light, 500)).toBe('rescue-lit')
  })

  it('rescues a has_substeps=NULL asset with rows present (unchanged)', () => {
    expect(classifyStuckCandidate(planless, 500)).toBe('rescue-lit')
  })

  it('rescues a planless target_floor=0 asset reporting zero rows (unchanged, §N.4)', () => {
    expect(classifyStuckCandidate({ has_substeps: false, target_floor: 0 }, 0))
      .toBe('rescue-lit')
  })

  it('marks a planless asset with no data as error (unchanged)', () => {
    expect(classifyStuckCandidate(light, 0)).toBe('error')
    expect(classifyStuckCandidate(light, null)).toBe('error')
  })

  it('never treats an unknown row count (failed probe) as evidence of completion', () => {
    expect(classifyStuckCandidate(light, null)).toBe('error')
    expect(classifyStuckCandidate(heavy, null)).toBe('error')
  })
})

describe('classifyStuckCandidate is strictly more conservative than rows-present', () => {
  it('promotes to lit only on inputs the pre-fix predicate also promoted', () => {
    // Exhaustive sweep of the input space. The pre-fix predicate, verbatim from
    // origin/main@5f5033a5:
    //     const dataConfirmedComplete =
    //       actualRows != null && (actualRows > 0 || c.target_floor === 0)
    //     if (dataConfirmedComplete) { rescued.push(...) } else { trulyStuck.push(...) }
    const preFixPromotesToLit = (c: StuckCandidate, rows: number | null) =>
      rows != null && (rows > 0 || c.target_floor === 0)

    for (const has_substeps of [true, false, null]) {
      for (const target_floor of [0, 1, 100, null]) {
        for (const rows of [null, 0, 1, 999]) {
          const c: StuckCandidate = { has_substeps, target_floor }
          const nowLit = classifyStuckCandidate(c, rows) === 'rescue-lit'
          if (nowLit) {
            expect(
              preFixPromotesToLit(c, rows),
              `regression: has_substeps=${has_substeps} target_floor=${target_floor} ` +
                `rows=${rows} is promoted to 'lit' by the new predicate but was NOT ` +
                `promoted by the old one — the fix must only ever promote fewer assets`
            ).toBe(true)
          }
        }
      }
    }
  })
})
