/**
 * curve_controls.ts — REAL negative controls for the model-agnostic scoring
 * harness (BRIEF_D4A.md Lane A-3, deliverables 1-2; DIS.028/DR-15(b)/(c)).
 *
 * Both controls operate on the CURVE a `TemporalCurveModel.curve()` call
 * already produced, not on model-internal substrate. This is deliberate:
 * because the transform is applied to the model's own real output (a
 * deterministic, reproducible date-axis permutation — never a fabricated
 * or randomly-drawn intensity value), it works identically for
 * `pratyantar_lord` today and for `midpoint_triangle`/`transit_kernel` once
 * those ship (model_interface.ts), with zero coupling to what substrate
 * produced the curve. This is what makes the controls genuinely reusable
 * across models rather than a one-off built for the dasha-lord-confluence
 * proxy.
 *
 * SHUFFLED-BIRTH CONTROL (deliverable 1): a circular time-shift of the
 * curve's date axis by a fixed offset, wrapping within [boundsStart,
 * boundsEnd). This is the same real-data permutation T-0's
 * `circularShiftPeriods` (curve.ts) already established as the project's
 * accepted shuffled-birth proxy: B.10 forbids fabricating a new ephemeris
 * run for a synthetic birth time, so "shuffled birth" is approximated by
 * permuting the chart's OWN already-computed intensity structure onto a
 * different position in the life-arc — never a stub, never a mock, never a
 * flat/random curve. `shuffledBirthControlCurve` is the curve-level
 * generalization of that same idea so it applies to any model's output.
 *
 * ANTIPHASE CONTROL (deliverable 2): BRIEF_D4A.md's own hint text is
 * "shift the curve 180° out of phase, or invert peak/trough" — no more
 * specific ratified definition exists anywhere in DR-13/DR-15/ARC_PLAN
 * (searched: DISAGREEMENT_REGISTER, BRIEF_D3, BRIEF_D4, ARC_PLAN — none
 * name a formula beyond that sentence). This module implements BOTH
 * readings, both real (same permutation discipline as shuffled-birth, no
 * fabrication), and treats the half-period circular shift as PRIMARY
 * because it reuses the exact same verified, reproducible mechanism as the
 * shuffled-birth control (just one specific, non-arbitrary shift amount —
 * exactly half the bounds span, i.e. the curve's own mirror-in-time point)
 * rather than introducing a second, structurally different transform. The
 * peak/trough inversion is exported as the documented alternate reading —
 * a caller doctrine-directed to prefer it can use it instead — but is not
 * wired into the default harness pipeline. This choice is a documented
 * judgment call, not a hidden one, exactly as B.10/CLAUDE.md require for
 * an underspecified construction.
 */
import type { CurvePoint } from '../curve'

const MS_PER_DAY = 86_400_000

/**
 * Circularly shifts every point's DATE by `shiftDays`, wrapping within
 * [boundsStart, boundsEnd). Intensities travel with their point unchanged —
 * only the date axis is permuted. Points that wrap past `boundsEnd` land
 * back at `boundsStart` plus the remainder, exactly mirroring
 * `circularShiftPeriods`'s wrap arithmetic in curve.ts.
 *
 * BUG FIX (F-2, 2026-07-22): the wraparound modulo arithmetic moves a
 * point's DATE but `.map()` preserves the point's original ARRAY INDEX. Any
 * point whose shift crosses `boundsEnd` lands back near `boundsStart` while
 * staying at its old (now too-late) array position, so the output is no
 * longer sorted ascending by date whenever `shiftDays` is not an exact
 * multiple of the bounds span. `proper_scoring.ts`'s `crps()`/`gridStepDays()`
 * treat array-adjacent points as date-adjacent neighbors (their Riemann-sum
 * step is `(next.date - prev.date) / 2`); fed an unsorted grid, `next` can
 * precede `prev` in time, producing a NEGATIVE step for that grid cell and,
 * with it, mathematically impossible negative CRPS values (CRPS is an
 * integral of squared terms and must be >= 0). Re-sorting by date after the
 * wrap restores the grid invariant every downstream consumer of
 * `CurvePoint[]` assumes. See PR #694 for the live reproduction that
 * surfaced this (that PR's run numbers are VOID — see its own follow-up
 * fix PR for the disclosure).
 */
export function circularShiftCurve(curve: CurvePoint[], shiftDays: number, boundsStart: Date, boundsEnd: Date): CurvePoint[] {
  const totalMs = boundsEnd.getTime() - boundsStart.getTime()
  if (totalMs <= 0) return curve
  const shifted = curve.map((pt) => {
    const offset = (((pt.date.getTime() - boundsStart.getTime() + shiftDays * MS_PER_DAY) % totalMs) + totalMs) % totalMs
    return { date: new Date(boundsStart.getTime() + offset), intensity: pt.intensity }
  })
  shifted.sort((a, b) => a.date.getTime() - b.date.getTime())
  return shifted
}

/**
 * Shuffled-birth control (deliverable 1): a single circular shift by
 * `shiftDays` (caller supplies — the harness's `K` evenly-spaced shifts,
 * mirroring `runShuffledControls`'s discipline in checks.ts, live in
 * harness.ts which calls this once per shift).
 */
export function shuffledBirthControlCurve(curve: CurvePoint[], shiftDays: number, boundsStart: Date, boundsEnd: Date): CurvePoint[] {
  return circularShiftCurve(curve, shiftDays, boundsStart, boundsEnd)
}

/**
 * Antiphase control, PRIMARY reading (deliverable 2): shifts the curve by
 * exactly half the bounds span — the curve's own time-mirror point, i.e.
 * "180° out of phase" read literally against the full life-arc as one
 * period. Deterministic, reproducible, no arbitrary shift-count choice
 * (unlike the K-shuffle shuffled-birth control, there is exactly one
 * antiphase shift).
 */
export function antiphaseControlCurve(curve: CurvePoint[], boundsStart: Date, boundsEnd: Date): CurvePoint[] {
  const totalDays = Math.round((boundsEnd.getTime() - boundsStart.getTime()) / MS_PER_DAY)
  const halfShift = Math.round(totalDays / 2)
  return circularShiftCurve(curve, halfShift, boundsStart, boundsEnd)
}

/**
 * Antiphase control, ALTERNATE reading: peak<->trough inversion in place
 * (dates unchanged, intensities reflected around the curve's own max so a
 * former peak becomes a trough and vice versa). Documented but not wired
 * into the default harness — see module header. `max(0, ...)` floor keeps
 * intensities non-negative (matches every other intensity in this codebase
 * being >= 0, e.g. curve.ts's `DEPTH_WEIGHT` sums).
 */
export function antiphaseInvertPeakTrough(curve: CurvePoint[]): CurvePoint[] {
  if (curve.length === 0) return curve
  const maxIntensity = Math.max(...curve.map((c) => c.intensity))
  return curve.map((pt) => ({ date: pt.date, intensity: Math.max(0, maxIntensity - pt.intensity) }))
}
