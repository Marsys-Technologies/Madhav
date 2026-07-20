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

// ---------------------------------------------------------------------------
// Shape-aware matcher (CR-47 root-cause fix, DR-13/DIS.026-speced,
// D-4a Lane A-1). The pre-D-4a harness scored every LEL event as a bare
// point matched to a served curve's local peak within a FIXED ±45-day
// window, regardless of what shape the event actually is in reality (see
// `scoreEvent` above, kept unmodified as the point-shaped primitive it
// always was — DR-13(a) default). DR-13/DIS.026 ratified three event
// shapes plus a confidence-scaled tolerance; this section implements (b)
// interval overlap scoring, (c) chain per-milestone scoring, and (d)
// date_confidence-scaled point tolerance, with (e) control-mirroring: every
// function here takes the SAME `periods` argument whether real or
// shuffled-control, so a caller scoring a control through
// `scoreShapeAwareEvent` gets the identical shape/tolerance treatment as
// the real chart — there is no code path here that special-cases "real".
// ---------------------------------------------------------------------------

export type EventShape = 'point' | 'interval' | 'chain'
export type DateConfidence = 'exact' | 'month_known' | 'year_only'

/** DR-13(d): exact=±45d (DR-11's figure, unchanged), month_known=±75d. year_only never reaches this function directly — it is scored as an interval (LEL_SCHEMA_V2_PROPOSAL "Year-only secondary battery") and routed to the secondary battery by the caller, never silently folded into the primary hit-rate. */
export function toleranceDaysFor(dateConfidence: DateConfidence): number {
  if (dateConfidence === 'exact') return PROXIMITY_DAYS // 45
  if (dateConfidence === 'month_known') return 75
  return PROXIMITY_DAYS // year_only is not point-scored; see isSecondaryBattery
}

/** DR-13(d): year_only events are never scored in the primary hit-rate — they run in a clearly-labeled secondary battery. */
export function isSecondaryBattery(dateConfidence: DateConfidence): boolean {
  return dateConfidence === 'year_only'
}

export type ShapeAwareEvent = {
  event_id: string
  shape: EventShape
  date_confidence: DateConfidence
  /** point shape: the anchor date. Also used as the milestone anchor for a chain milestone whose own shape is 'point'. */
  event_date?: Date
  /** interval shape (incl. year_only, whose bounds are the calendar-year span per the schema proposal). */
  interval_start?: Date
  interval_end?: Date
  /** chain shape: the milestone rows belonging to this chain, each independently scoreable (DR-13(c) — "collapsing a chain to one fuzzy date is a recording error"). Each milestone carries its own shape/date_confidence/dates, exactly like any point or interval event. */
  milestones?: ShapeAwareEvent[]
}

export type ShapeAwareScore = SingleEventScore & {
  shape: EventShape
  date_confidence: DateConfidence
  secondary_battery: boolean
  /** interval only: fraction of the interval's curve-points at/above the percentile threshold — DR-13(b)'s "score by overlap", not a single distance number. */
  overlap_fraction?: number
  /** chain only: per-milestone scores, each independently pass/fail. */
  milestone_scores?: ShapeAwareScore[]
}

/** DR-13(a)/(d): a point event, scored exactly like the pre-existing `scoreEvent`, but with proximityDays scaled by date_confidence instead of the hardcoded DR-11 constant. */
export function scorePointEvent(
  periods: DashaPeriod[],
  significators: Record<string, number>,
  event: ShapeAwareEvent,
  boundsStart: Date,
  boundsEnd: Date,
  percentile: number
): ShapeAwareScore {
  if (!event.event_date) throw new Error(`scorePointEvent: event ${event.event_id} has shape='point' but no event_date`)
  const proximityDays = toleranceDaysFor(event.date_confidence)
  const base = scoreEvent(periods, significators, event.event_id, event.event_date, boundsStart, boundsEnd, percentile, proximityDays)
  return { ...base, shape: 'point', date_confidence: event.date_confidence, secondary_battery: isSecondaryBattery(event.date_confidence) }
}

/**
 * DR-13(b): an interval-shaped event scores by OVERLAP with a served
 * top-decile curve window, not distance-to-a-point. Curve is built over the
 * interval padded by ±WINDOW_YEARS/2 (same window discipline as the point
 * case) so the percentile threshold has enough surrounding context to be
 * meaningful; overlap is then measured strictly within [interval_start,
 * interval_end]. `pass` requires at least one in-interval curve point at or
 * above the percentile threshold (mirrors the point case's
 * at_or_above_threshold, generalized from "the one nearby peak" to "any
 * point inside the interval").
 */
export function scoreIntervalEvent(
  periods: DashaPeriod[],
  significators: Record<string, number>,
  event: ShapeAwareEvent,
  boundsStart: Date,
  boundsEnd: Date,
  percentile: number
): ShapeAwareScore {
  const { event_id, interval_start, interval_end, date_confidence } = event
  if (!interval_start || !interval_end) throw new Error(`scoreIntervalEvent: event ${event_id} has shape='interval' but missing interval bounds`)
  const { start, end } = windowFor(interval_start, boundsStart, boundsEnd)
  const paddedEnd = new Date(Math.max(end.getTime(), windowFor(interval_end, boundsStart, boundsEnd).end.getTime()))
  const curve = buildCurve(periods, significators, start, paddedEnd, STEP_DAYS)
  const threshold = percentileThreshold(curve, percentile)
  const inInterval = curve.filter((pt) => pt.date.getTime() >= interval_start.getTime() && pt.date.getTime() <= interval_end.getTime())
  const overlapping = inInterval.filter((pt) => pt.intensity > 0 && pt.intensity >= threshold)
  const overlapFraction = inInterval.length > 0 ? overlapping.length / inInterval.length : 0
  const peak = inInterval.reduce<CurvePoint | undefined>((best, pt) => (!best || pt.intensity > best.intensity ? pt : best), undefined)
  const atOrAbove = overlapping.length > 0
  return {
    event_id,
    event_date: interval_start.toISOString().slice(0, 10),
    window_start: start.toISOString().slice(0, 10),
    window_end: paddedEnd.toISOString().slice(0, 10),
    threshold_percentile: percentile,
    threshold_value: threshold,
    peak: peak ? { date: peak.date.toISOString().slice(0, 10), intensity: peak.intensity } : undefined,
    peak_lag_days: undefined,
    within_proximity: inInterval.length > 0,
    at_or_above_threshold: atOrAbove,
    pass: inInterval.length > 0 && atOrAbove,
    peak_basis: 'dasha_lord_confluence_v1',
    shape: 'interval',
    date_confidence,
    secondary_battery: isSecondaryBattery(date_confidence),
    overlap_fraction: overlapFraction,
  }
}

/**
 * DR-13(c): a chain-shaped event is never scored as a single blob — each
 * named milestone anchor is independently scoreable via its own shape
 * (point or interval). `pass` on the chain summary is true iff at least one
 * milestone passes (a chain "hits" if any of its dateable moments lands in
 * a served high-activation window); `milestone_scores` carries the full
 * per-milestone breakdown so a caller never has to take the summary on
 * faith.
 */
export function scoreChainEvent(
  periods: DashaPeriod[],
  significators: Record<string, number>,
  event: ShapeAwareEvent,
  boundsStart: Date,
  boundsEnd: Date,
  percentile: number
): ShapeAwareScore {
  const milestones = event.milestones ?? []
  if (milestones.length === 0) throw new Error(`scoreChainEvent: event ${event.event_id} has shape='chain' but no milestones`)
  const milestoneScores = milestones.map((m) => scoreShapeAwareEvent(periods, significators, m, boundsStart, boundsEnd, percentile))
  const anyPass = milestoneScores.some((s) => s.pass)
  const best = milestoneScores.reduce((b, s) => (s.peak && (!b?.peak || s.peak.intensity > b.peak.intensity) ? s : b), milestoneScores[0])
  return {
    ...best,
    event_id: event.event_id,
    shape: 'chain',
    date_confidence: event.date_confidence,
    secondary_battery: false, // a chain's own secondary-battery status is per-milestone, carried in milestone_scores
    pass: anyPass,
    milestone_scores: milestoneScores,
  }
}

/** Single dispatch point: routes an event to its shape's scorer. This is the one function a caller (blind battery, dry-run harness) needs to know about. */
export function scoreShapeAwareEvent(
  periods: DashaPeriod[],
  significators: Record<string, number>,
  event: ShapeAwareEvent,
  boundsStart: Date,
  boundsEnd: Date,
  percentile: number
): ShapeAwareScore {
  if (event.shape === 'point') return scorePointEvent(periods, significators, event, boundsStart, boundsEnd, percentile)
  if (event.shape === 'interval') return scoreIntervalEvent(periods, significators, event, boundsStart, boundsEnd, percentile)
  return scoreChainEvent(periods, significators, event, boundsStart, boundsEnd, percentile)
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
