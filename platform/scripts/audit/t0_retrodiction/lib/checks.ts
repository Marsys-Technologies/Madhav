/**
 * checks.ts — the T-0 retrodiction gate's three scoring checks + the
 * anti-gaming pass (BRIEF_D3.md §F1 Lane T-0, §G; DR-11/DIS.024 thresholds).
 * Pure functions over already-fetched dasha periods — no network here,
 * so this is fully unit-testable against fixtures (CONDUCTOR_PROTOCOL
 * §3.1(b)).
 */
import { buildCurve, percentileThreshold, localMax, fractionAtOrAbove, variance, circularShiftPeriods, type DashaPeriod, type CurvePoint } from './curve'
import { daysBetween } from './dates'

export const PROXIMITY_DAYS = 45 // DR-11 (DIS.024)
export const WINDOW_YEARS = 5
export const STEP_DAYS = 5 // curve resolution — well under the ~2-3 month Pratyantar granularity this chart's dasha table serves

export type SingleEventScore = {
  event_id: string
  event_date: string
  window_start: string
  window_end: string
  threshold_percentile: number
  threshold_value: number
  peak: { date: string; intensity: number } | undefined
  peak_lag_days: number | undefined // signed: peak.date - event_date
  within_proximity: boolean
  at_or_above_threshold: boolean
  pass: boolean
  peak_basis: 'dasha_lord_confluence_v1'
}

function windowFor(eventDate: Date, boundsStart: Date, boundsEnd: Date): { start: Date; end: Date } {
  const halfMs = (WINDOW_YEARS / 2) * 365 * 86_400_000
  let start = new Date(eventDate.getTime() - halfMs)
  let end = new Date(eventDate.getTime() + halfMs)
  if (start.getTime() < boundsStart.getTime()) start = boundsStart
  if (end.getTime() > boundsEnd.getTime()) end = boundsEnd
  return { start, end }
}

/**
 * Scores one event against one mechanism's significator set. `percentile`
 * is 0.9 for checks (a)/(b) (top-decile) and 2/3 for check (c) (top-tercile)
 * per DR-11.
 */
export function scoreEvent(
  periods: DashaPeriod[],
  significators: Record<string, number>,
  eventId: string,
  eventDate: Date,
  boundsStart: Date,
  boundsEnd: Date,
  percentile: number,
  proximityDays: number = PROXIMITY_DAYS
): SingleEventScore {
  const { start, end } = windowFor(eventDate, boundsStart, boundsEnd)
  const curve = buildCurve(periods, significators, start, end, STEP_DAYS)
  const threshold = percentileThreshold(curve, percentile)
  const peak = localMax(curve, eventDate, proximityDays)
  const withinProximity = peak !== undefined
  // A "peak" of 0 is not a real peak — on a fully degenerate (all-zero, no
  // significator ever runs in-window) curve, percentileThreshold is also 0
  // and a trivial 0>=0 would otherwise read as a false hit. Requiring a
  // strictly positive intensity closes that edge case; checkCurveNotDegenerate
  // is the broader guard against near-degenerate (low-variance) curves.
  const atOrAbove = peak !== undefined && peak.intensity > 0 && peak.intensity >= threshold
  return {
    event_id: eventId,
    event_date: eventDate.toISOString().slice(0, 10),
    window_start: start.toISOString().slice(0, 10),
    window_end: end.toISOString().slice(0, 10),
    threshold_percentile: percentile,
    threshold_value: threshold,
    peak: peak ? { date: peak.date.toISOString().slice(0, 10), intensity: peak.intensity } : undefined,
    peak_lag_days: peak ? daysBetween(eventDate, peak.date) : undefined,
    within_proximity: withinProximity,
    at_or_above_threshold: atOrAbove,
    pass: withinProximity && atOrAbove,
    peak_basis: 'dasha_lord_confluence_v1',
  }
}

export type AntiGamingResult = {
  variance: number
  variance_ok: boolean
  top_decile_fraction: number
  top_decile_fraction_ok: boolean // DR-11/§G: "top-decile is <15% of days"
  pass: boolean
}

/** §G anti-gaming pass, applied to a single mechanism curve: variance floor + top-decile-day-fraction < 15%. */
export function checkCurveNotDegenerate(curve: CurvePoint[]): AntiGamingResult {
  const v = variance(curve)
  const topDecile = percentileThreshold(curve, 0.9)
  const frac = fractionAtOrAbove(curve, topDecile)
  const varianceOk = v > 0
  const fracOk = frac < 0.15
  return { variance: v, variance_ok: varianceOk, top_decile_fraction: frac, top_decile_fraction_ok: fracOk, pass: varianceOk && fracOk }
}

export type BlindBatteryResult = {
  scored_count: number
  hit_count: number
  hit_rate: number
  per_event: SingleEventScore[]
  lead_lag_distribution: number[] // peak_lag_days for hits only
}

export function runBlindBattery(
  periods: DashaPeriod[],
  events: { event_id: string; date: Date; significators: Record<string, number> }[],
  boundsStart: Date,
  boundsEnd: Date
): BlindBatteryResult {
  const perEvent = events.map((e) => scoreEvent(periods, e.significators, e.event_id, e.date, boundsStart, boundsEnd, 2 / 3))
  const hits = perEvent.filter((s) => s.pass)
  return {
    scored_count: perEvent.length,
    hit_count: hits.length,
    hit_rate: perEvent.length > 0 ? hits.length / perEvent.length : 0,
    per_event: perEvent,
    lead_lag_distribution: hits.map((h) => h.peak_lag_days as number).filter((v) => v !== undefined),
  }
}

export type ShuffleControlResult = {
  shift_days: number
  hit_rate: number
}

/**
 * DR-11's anti-gaming rule: score the SAME blind battery against K
 * circular-shifted (shuffled-birth-proxy, see curve.ts circularShiftPeriods)
 * copies of the real dasha timeline, and confirm the real chart's hit rate
 * beats the shuffled distribution. Shift magnitudes are deterministic
 * (evenly spaced across the life-arc length) so the control is
 * reproducible, not cherry-picked.
 */
export function runShuffledControls(
  periods: DashaPeriod[],
  events: { event_id: string; date: Date; significators: Record<string, number> }[],
  boundsStart: Date,
  boundsEnd: Date,
  shiftCount: number
): ShuffleControlResult[] {
  const totalDays = daysBetween(boundsStart, boundsEnd)
  const out: ShuffleControlResult[] = []
  for (let i = 1; i <= shiftCount; i++) {
    const shiftDays = Math.round((totalDays / (shiftCount + 1)) * i)
    const shifted = circularShiftPeriods(periods, shiftDays, boundsStart, boundsEnd)
    const result = runBlindBattery(shifted, events, boundsStart, boundsEnd)
    out.push({ shift_days: shiftDays, hit_rate: result.hit_rate })
  }
  return out
}
