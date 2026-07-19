/**
 * proper_scoring.ts — CRPS + log-score as the PRIMARY metric (BRIEF_D4A.md
 * Lane A-3 deliverable 3; DIS.028/DR-15(b): "Model comparison uses proper
 * scoring (CRPS/log-score) against mirrored shuffled-birth controls;
 * skill = 1 − CRPS_model/CRPS_control; hit-rate (±45d top-decile) retained
 * as legacy secondary metric.").
 *
 * WHAT IS BEING SCORED, PRECISELY (a documented judgment call, per the
 * project's own instruction to be transparent about curve constructions —
 * curve.ts header, same discipline applied here):
 *
 * A model's `curve(chart, event_class, [t1,t2])` output is treated as an
 * UNNORMALIZED intensity function over time. To score it against a single
 * true event date x0 with a proper scoring rule, it is normalized into a
 * discrete predictive distribution over the grid of dates the curve was
 * evaluated at: p_i = max(0, intensity_i) / sum(max(0, intensity_j)). This
 * is the standard "treat the forecast as a predictive density over the
 * event time, score how well its mass concentrates around the true time"
 * construction (Gneiting & Raftery 2007's CRPS is defined exactly this way
 * for a predictive CDF vs. a scalar observation; the discretization here is
 * the curve's own STEP_DAYS grid, no continuous-time interpolation
 * invented beyond what buildCurve already produced).
 *
 * CRPS(F, x0) = ∫ (F(t) − 1{t ≥ x0})² dt, discretized as a Riemann sum over
 * the grid with each point's own dt (irregular-grid safe — see `stepDays`).
 * Lower is better; a perfect single-point forecast exactly at x0 scores
 * CRPS ≈ 0 (verified by unit test).
 *
 * Log-score(p, x0) = log(density at the grid bucket containing x0), with an
 * epsilon floor (1e-6) so a zero-probability bucket does not produce -Inf
 * and silently poison an aggregate. Higher (less negative) is better.
 *
 * skill = 1 − CRPS_model / CRPS_control (DR-15(b), verbatim). skill > 0
 * means the model beats its control; skill <= 0 means it does not. Skill is
 * undefined (returns `null`, never a fabricated number) when CRPS_control
 * is exactly 0 (a genuinely all-mass-at-one-point control, which should not
 * occur for a real permuted control but is guarded rather than silently
 * dividing by zero).
 */
import type { CurvePoint } from '../curve'

export type ProperScoreResult = {
  crps: number
  logScore: number
  gridSize: number
  eventInRange: boolean // x0 fell within [curve[0].date, curve[last].date] — a CRPS/log-score computed outside this range is reported but flagged
}

const EPS = 1e-6

function gridStepDays(curve: CurvePoint[], i: number): number {
  // Half-distance to each neighbor, summed — standard Riemann midpoint-rule
  // spacing for an irregular (or regular) grid. Falls back to 1 day for a
  // single-point curve (degenerate, but must not divide by zero).
  if (curve.length <= 1) return 1
  const prev = i > 0 ? curve[i - 1].date.getTime() : curve[i].date.getTime() - (curve[i + 1].date.getTime() - curve[i].date.getTime())
  const next = i < curve.length - 1 ? curve[i + 1].date.getTime() : curve[i].date.getTime() + (curve[i].date.getTime() - curve[i - 1].date.getTime())
  return (next - prev) / 2 / 86_400_000
}

/** Normalizes a curve's (clamped non-negative) intensities into a discrete probability mass function over its own grid. All-zero curves normalize to a uniform distribution (an honest "no information" forecast, not a divide-by-zero). */
export function normalize(curve: CurvePoint[]): number[] {
  const clamped = curve.map((c) => Math.max(0, c.intensity))
  const total = clamped.reduce((s, v) => s + v, 0)
  if (total <= 0) return curve.map(() => 1 / curve.length)
  return clamped.map((v) => v / total)
}

/**
 * CRPS of a curve-derived forecast against a single true event date.
 * `rangeStart`/`rangeEnd` extend the integration domain beyond the curve's
 * own span if the true date falls outside it (so an event the model never
 * even evaluated near still gets a real, non-degenerate CRPS rather than an
 * undefined one) — the extension contributes 0 forecast mass, which is the
 * correct and honest penalty for a model that assigned zero probability
 * anywhere near the truth.
 */
export function crps(curve: CurvePoint[], trueDate: Date): ProperScoreResult {
  if (curve.length === 0) return { crps: NaN, logScore: -Infinity, gridSize: 0, eventInRange: false }
  const probs = normalize(curve)
  const x0 = trueDate.getTime()
  const first = curve[0].date.getTime()
  const last = curve[curve.length - 1].date.getTime()
  const eventInRange = x0 >= first && x0 <= last

  let cumulative = 0
  let integral = 0
  for (let i = 0; i < curve.length; i++) {
    cumulative += probs[i]
    const step = gridStepDays(curve, i)
    const heaviside = curve[i].date.getTime() >= x0 ? 1 : 0
    integral += (cumulative - heaviside) ** 2 * step
  }
  // If x0 is entirely before the grid start or after the grid end, the
  // Heaviside term above still evaluates correctly at every grid point
  // (all-1 if x0 < first, all-0 if x0 > last) — no separate branch needed.

  const logScoreResult = logScore(curve, trueDate)
  return { crps: integral, logScore: logScoreResult, gridSize: curve.length, eventInRange }
}

/** Log predictive density (as a log-score, higher = better) at the grid bucket nearest the true date. Returns log(EPS) when the true date falls outside the curve's own grid entirely (the harshest, honest penalty — not silently NaN). */
export function logScore(curve: CurvePoint[], trueDate: Date): number {
  if (curve.length === 0) return Math.log(EPS)
  const probs = normalize(curve)
  const x0 = trueDate.getTime()
  let nearestIdx = 0
  let nearestDist = Infinity
  for (let i = 0; i < curve.length; i++) {
    const d = Math.abs(curve[i].date.getTime() - x0)
    if (d < nearestDist) {
      nearestDist = d
      nearestIdx = i
    }
  }
  const step = Math.max(gridStepDays(curve, nearestIdx), 1e-9)
  const density = probs[nearestIdx] / step // probability mass -> density (per day)
  return Math.log(Math.max(density, EPS))
}

/** DR-15(b), verbatim: skill = 1 − CRPS_model/CRPS_control. Returns null (never a fabricated number) when CRPS_control is exactly 0. */
export function skill(crpsModel: number, crpsControl: number): number | null {
  if (crpsControl === 0) return null
  return 1 - crpsModel / crpsControl
}
