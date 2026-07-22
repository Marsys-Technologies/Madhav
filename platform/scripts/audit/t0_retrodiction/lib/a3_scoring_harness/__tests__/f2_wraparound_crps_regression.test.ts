/**
 * f2_wraparound_crps_regression.test.ts — SYNTHETIC fixtures only, all dates
 * pre-2020 (sealed-test-split discipline, per model_interface.test.ts header).
 *
 * Verifier-grade proof for the F-2 fix (2026-07-22): `circularShiftCurve()`
 * (curve_controls.ts) was not re-sorting its output by date after wraparound,
 * corrupting `proper_scoring.ts`'s `crps()` Riemann-sum integral (its
 * `gridStepDays()` treats array-adjacent points as date-adjacent neighbors;
 * fed an unsorted grid it can compute a NEGATIVE per-cell step, producing
 * mathematically impossible negative CRPS values). Live-reproduced in
 * PR #694's B-1 bakeoff run — see that PR + this fix's own PR for the full
 * account. PR #694's run numbers (scores/rankings/deltas) are VOID: their
 * only value was surfacing this defect, and they must never be cited as a
 * real result.
 *
 * Three proofs, per the fix's own acceptance bar:
 *   1. Property test — CRPS >= 0 across many randomized shifts/curves/bounds/
 *      true-dates (deterministic seeded PRNG, reproducible in CI). The
 *      "impossible negative CRPS" class must die permanently, not just for
 *      the one shape reproduced in PR #694.
 *   2. Independent re-derivation — one control integral recomputed via a
 *      genuinely separate code path (different iteration structure, boundary-
 *      midpoint cell widths instead of `gridStepDays()`'s neighbor-averaging,
 *      the expanded Brier-score decomposition instead of the direct squared
 *      term) and confirmed to match `crps()`'s own output on the fixed
 *      function's real (sorted) output.
 *   3. Unshifted-segment regression — a shift small enough that no point
 *      crosses `boundsEnd` (no wraparound to correct) must produce byte-
 *      identical dates to a naive shift-with-no-sort, proving the sort added
 *      by the fix is a genuine no-op when there is nothing to fix.
 */
import { describe, it, expect } from 'vitest'
import { circularShiftCurve } from '../curve_controls'
import { crps } from '../proper_scoring'
import type { CurvePoint } from '../../curve'

const MS_PER_DAY = 86_400_000

// --- deterministic seeded PRNG (mulberry32) — reproducible in CI, no flakiness ---
function mulberry32(seed: number): () => number {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function makeRandomCurve(rng: () => number, boundsStart: Date, spanDays: number, stepDays: number): CurvePoint[] {
  const out: CurvePoint[] = []
  for (let d = 0; d <= spanDays; d += stepDays) {
    // Intensities are non-negative real numbers, some exactly zero — never a
    // fabricated chart value, this is purely synthetic test-fixture data.
    const raw = rng() < 0.3 ? 0 : rng() * 100
    out.push({ date: new Date(boundsStart.getTime() + d * MS_PER_DAY), intensity: raw })
  }
  return out
}

describe('F-2 regression — proof 1: property test, CRPS >= 0 across many randomized shifts', () => {
  it('never produces a negative CRPS across 500 randomized (curve, bounds, shift, trueDate) combinations', () => {
    const rng = mulberry32(0xf2c2b5)
    let tested = 0
    let wraparoundCasesTested = 0

    for (let trial = 0; trial < 500; trial++) {
      const boundsStart = new Date(Date.UTC(1980 + Math.floor(rng() * 30), 0, 1))
      const spanDays = 200 + Math.floor(rng() * 3000) // 200 .. ~3200 day bounds span
      const boundsEnd = new Date(boundsStart.getTime() + spanDays * MS_PER_DAY)
      const stepDays = 1 + Math.floor(rng() * 20)
      const curveSpanDays = Math.min(spanDays - 1, 50 + Math.floor(rng() * 500))
      const curve = makeRandomCurve(rng, boundsStart, curveSpanDays, stepDays)
      if (curve.length === 0) continue

      const shiftDays = Math.floor(rng() * spanDays * 2) - Math.floor(spanDays / 2) // can be negative, can exceed span (forces wraparound)
      const shifted = circularShiftCurve(curve, shiftDays, boundsStart, boundsEnd)

      // Structural invariant the fix restores: output must be sorted ascending by date.
      for (let i = 1; i < shifted.length; i++) {
        expect(shifted[i].date.getTime()).toBeGreaterThanOrEqual(shifted[i - 1].date.getTime())
      }

      // Did this trial actually exercise a wraparound? (informational tally only —
      // the assertion below must hold regardless, but this confirms the property
      // test isn't accidentally only covering the non-wrapping case.)
      const originalOrderDates = curve.map((c) => c.date.getTime())
      const wouldWrapUnsorted = shifted.some((pt, i) => i > 0 && pt.date.getTime() < shifted[i - 1].date.getTime())
      void originalOrderDates
      if (!wouldWrapUnsorted) {
        // can't detect post-sort; use a direct span check instead
      }
      const totalMs = boundsEnd.getTime() - boundsStart.getTime()
      const anyPointWraps = curve.some((pt) => {
        const raw = pt.date.getTime() - boundsStart.getTime() + shiftDays * MS_PER_DAY
        return raw < 0 || raw >= totalMs
      })
      if (anyPointWraps) wraparoundCasesTested++

      const trueDateOffsetDays = Math.floor(rng() * (spanDays + 200)) - 100 // sometimes outside range entirely
      const trueDate = new Date(boundsStart.getTime() + trueDateOffsetDays * MS_PER_DAY)

      const result = crps(shifted, trueDate)
      tested++
      // CRPS is an integral of squared terms times a (now-guaranteed-positive
      // post-sort) step — it is mathematically impossible for it to be
      // negative. Tiny floating-point slack only.
      expect(result.crps).toBeGreaterThanOrEqual(-1e-9)
      expect(Number.isFinite(result.crps)).toBe(true)
    }

    expect(tested).toBeGreaterThan(400) // sanity: the trial loop actually ran
    expect(wraparoundCasesTested).toBeGreaterThan(50) // sanity: this genuinely exercised the wraparound path, not just the trivial case
  })
})

describe('F-2 regression — proof 2: independent re-derivation of one control integral', () => {
  /**
   * A from-scratch CRPS computation, deliberately structured differently
   * from proper_scoring.ts's `crps()`/`gridStepDays()`:
   *  - cell widths via explicit left/right MIDPOINT BOUNDARIES (not
   *    `gridStepDays`'s next/prev neighbor-averaging formula);
   *  - the expanded Brier-score decomposition (F_i^2 - 2*F_i*h_i + h_i) summed
   *    via `reduce`, instead of the direct `(cumulative - heaviside)^2` term
   *    computed in an indexed for-loop.
   * Both approaches target the SAME documented quantity (proper_scoring.ts's
   * own header: "Riemann sum over the grid with each point's own dt",
   * heaviside evaluated once per grid point) — this is not a different
   * formula, it is an independently-written arithmetic path over the same
   * spec, which is exactly what catches a coding-level bug (there is none
   * here; this proves the closed-form implementation is arithmetically
   * sound on correctly-sorted input, complementing proof 1's structural
   * invariant check).
   */
  function independentCrps(curve: CurvePoint[], trueDate: Date): number {
    const sorted = [...curve].sort((a, b) => a.date.getTime() - b.date.getTime())
    const n = sorted.length
    if (n === 0) return NaN
    const t = sorted.map((c) => c.date.getTime())
    const clamped = sorted.map((c) => Math.max(0, c.intensity))
    const total = clamped.reduce((s, v) => s + v, 0)
    const probs = total > 0 ? clamped.map((v) => v / total) : clamped.map(() => 1 / n)

    // cumulative mass AT each point (F_i)
    const cumF: number[] = []
    probs.reduce((run, p) => {
      const next = run + p
      cumF.push(next)
      return next
    }, 0)

    // heaviside per grid point (owning-point convention, matches the spec)
    const x0 = trueDate.getTime()
    const h = t.map((ti) => (ti >= x0 ? 1 : 0))

    // cell width via explicit midpoint boundaries
    const widthsDays = t.map((ti, i) => {
      const left = i > 0 ? (t[i - 1] + ti) / 2 : ti - (n > 1 ? (t[1] - t[0]) / 2 : 0.5 * MS_PER_DAY)
      const right = i < n - 1 ? (ti + t[i + 1]) / 2 : ti + (n > 1 ? (t[n - 1] - t[n - 2]) / 2 : 0.5 * MS_PER_DAY)
      return (right - left) / MS_PER_DAY
    })

    // expanded Brier decomposition: (F - h)^2 = F^2 - 2*F*h + h^2, h in {0,1} so h^2 = h
    return cumF.reduce((s, F, i) => s + (F * F - 2 * F * h[i] + h[i]) * widthsDays[i], 0)
  }

  it('matches crps() exactly on a real (fixed) control curve output — a genuinely wrapping shift', () => {
    const boundsStart = new Date(Date.UTC(1991, 0, 1))
    const boundsEnd = new Date(Date.UTC(1996, 0, 1)) // 5-year bounds
    const rng = mulberry32(0xa3c012)
    const curve = makeRandomCurve(rng, boundsStart, 900, 7)
    const totalDays = Math.round((boundsEnd.getTime() - boundsStart.getTime()) / MS_PER_DAY)
    const shiftDays = totalDays - 30 // deliberately forces wraparound near boundsEnd
    const shifted = circularShiftCurve(curve, shiftDays, boundsStart, boundsEnd)
    const trueDate = new Date(boundsStart.getTime() + 400 * MS_PER_DAY)

    const official = crps(shifted, trueDate)
    const independent = independentCrps(shifted, trueDate)

    expect(official.crps).toBeGreaterThanOrEqual(0) // proof-1 property restated concretely for this specific case
    expect(independent).toBeCloseTo(official.crps, 9)
  })
})

describe('F-2 regression — proof 3: unshifted-segment behavior unchanged (no wraparound to correct)', () => {
  it('a shift that never crosses boundsEnd produces dates identical to a naive (unsorted) shift — the fix\'s sort is a true no-op here', () => {
    const boundsStart = new Date(Date.UTC(1990, 0, 1))
    const boundsEnd = new Date(Date.UTC(2000, 0, 1)) // 10-year bounds — plenty of headroom
    const curve: CurvePoint[] = []
    for (let d = 0; d <= 200; d += 10) {
      curve.push({ date: new Date(boundsStart.getTime() + d * MS_PER_DAY), intensity: d === 100 ? 10 : 1 })
    }
    const shiftDays = 50 // curve spans day 0..200; shifted spans day 50..250, bounds span is ~3653 days -- no wraparound possible

    const naiveShift = curve.map((pt) => ({ date: new Date(pt.date.getTime() + shiftDays * MS_PER_DAY), intensity: pt.intensity }))
    const fixed = circularShiftCurve(curve, shiftDays, boundsStart, boundsEnd)

    expect(fixed.map((c) => c.date.getTime())).toEqual(naiveShift.map((c) => c.date.getTime()))
    expect(fixed.map((c) => c.intensity)).toEqual(naiveShift.map((c) => c.intensity))

    // and CRPS on this never-wrapped case is identical whether or not the
    // (here, no-op) sort ran -- confirms zero behavior change for the
    // already-correctly-ordered case.
    const trueDate = new Date(boundsStart.getTime() + 150 * MS_PER_DAY)
    expect(crps(fixed, trueDate).crps).toBeCloseTo(crps(naiveShift, trueDate).crps, 9)
  })

  it('shiftDays=0 remains an exact date no-op (pre-existing invariant, still holds post-fix)', () => {
    const boundsStart = new Date(Date.UTC(1990, 0, 1))
    const boundsEnd = new Date(Date.UTC(2000, 0, 1))
    const curve: CurvePoint[] = []
    for (let d = 0; d <= 200; d += 10) {
      curve.push({ date: new Date(boundsStart.getTime() + d * MS_PER_DAY), intensity: d === 100 ? 10 : 1 })
    }
    const shifted = circularShiftCurve(curve, 0, boundsStart, boundsEnd)
    expect(shifted.map((c) => c.date.getTime())).toEqual(curve.map((c) => c.date.getTime()))
  })
})
