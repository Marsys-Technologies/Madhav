/**
 * shape_scoring.ts — model-agnostic, curve-input DR-13-shaped hit-rate
 * scoring (legacy SECONDARY metric per DIS.028/DR-15(b)).
 *
 * checks.ts's `scoreShapeAwareEvent` family (D-4a Lane A-1) is the
 * authoritative shape-aware matcher, but it is coupled to
 * `periods`+`significators` (it calls `buildCurve` internally) — that
 * couples every caller to the `pratyantar_lord` proxy model specifically.
 * This module re-expresses the SAME DR-13(a)-(d) shape/tolerance rules
 * (point / interval / chain; date_confidence-scaled tolerance) against an
 * already-built `CurvePoint[]`, so it works for ANY model's curve output
 * (model_interface.ts) — real or control. checks.ts is left untouched
 * (Lane A-1's file; not this lane's to modify) and is NOT imported here for
 * its curve-building path — only its pure math primitives are reused from
 * curve.ts, which both modules already share.
 */
import { percentileThreshold, localMax, type CurvePoint } from '../curve'
import { daysBetween } from '../dates'

export type EventShape = 'point' | 'interval' | 'chain'
export type DateConfidence = 'exact' | 'month_known' | 'year_only'

export const DEFAULT_PROXIMITY_DAYS = 45 // DR-11, unchanged by DR-13

/** DR-13(d): exact=±45d, month_known=±75d. year_only is never point-scored (see isSecondaryBattery) — this function is not called for it. */
export function toleranceDaysFor(dateConfidence: DateConfidence): number {
  if (dateConfidence === 'exact') return DEFAULT_PROXIMITY_DAYS
  if (dateConfidence === 'month_known') return 75
  return DEFAULT_PROXIMITY_DAYS
}

/** DR-13(d): year_only routes to the secondary battery, never silently folded into the primary hit-rate. */
export function isSecondaryBattery(dateConfidence: DateConfidence): boolean {
  return dateConfidence === 'year_only'
}

export type CurveEvent = {
  eventId: string
  shape: EventShape
  dateConfidence: DateConfidence
  eventDate?: Date // point shape (or a chain milestone whose own shape is 'point')
  intervalStart?: Date // interval shape
  intervalEnd?: Date
  milestones?: CurveEvent[] // chain shape — each independently scoreable, DR-13(c)
}

export type CurveEventScore = {
  eventId: string
  shape: EventShape
  dateConfidence: DateConfidence
  secondaryBattery: boolean
  thresholdPercentile: number
  thresholdValue: number
  peak?: { date: string; intensity: number }
  peakLagDays?: number
  withinProximity: boolean
  atOrAboveThreshold: boolean
  pass: boolean
  overlapFraction?: number // interval only, DR-13(b)
  milestoneScores?: CurveEventScore[] // chain only
}

function scorePoint(curve: CurvePoint[], event: CurveEvent, percentile: number): CurveEventScore {
  if (!event.eventDate) throw new Error(`scorePoint: event ${event.eventId} has shape='point' but no eventDate`)
  const proximityDays = toleranceDaysFor(event.dateConfidence)
  const threshold = percentileThreshold(curve, percentile)
  const peak = localMax(curve, event.eventDate, proximityDays)
  const withinProximity = peak !== undefined
  const atOrAbove = peak !== undefined && peak.intensity > 0 && peak.intensity >= threshold
  return {
    eventId: event.eventId,
    shape: 'point',
    dateConfidence: event.dateConfidence,
    secondaryBattery: isSecondaryBattery(event.dateConfidence),
    thresholdPercentile: percentile,
    thresholdValue: threshold,
    peak: peak ? { date: peak.date.toISOString().slice(0, 10), intensity: peak.intensity } : undefined,
    peakLagDays: peak ? daysBetween(event.eventDate, peak.date) : undefined,
    withinProximity,
    atOrAboveThreshold: atOrAbove,
    pass: withinProximity && atOrAbove,
  }
}

/** DR-13(b): interval-shaped events score by OVERLAP with the top-decile window, not distance-to-a-point. `curve` must already span the interval (the caller/harness is responsible for requesting the right [t1,t2] range from the model). */
function scoreInterval(curve: CurvePoint[], event: CurveEvent, percentile: number): CurveEventScore {
  const { intervalStart, intervalEnd, dateConfidence } = event
  if (!intervalStart || !intervalEnd) throw new Error(`scoreInterval: event ${event.eventId} has shape='interval' but missing interval bounds`)
  const threshold = percentileThreshold(curve, percentile)
  const inInterval = curve.filter((pt) => pt.date.getTime() >= intervalStart.getTime() && pt.date.getTime() <= intervalEnd.getTime())
  const overlapping = inInterval.filter((pt) => pt.intensity > 0 && pt.intensity >= threshold)
  const overlapFraction = inInterval.length > 0 ? overlapping.length / inInterval.length : 0
  const peak = inInterval.reduce<CurvePoint | undefined>((best, pt) => (!best || pt.intensity > best.intensity ? pt : best), undefined)
  const atOrAbove = overlapping.length > 0
  return {
    eventId: event.eventId,
    shape: 'interval',
    dateConfidence,
    secondaryBattery: isSecondaryBattery(dateConfidence),
    thresholdPercentile: percentile,
    thresholdValue: threshold,
    peak: peak ? { date: peak.date.toISOString().slice(0, 10), intensity: peak.intensity } : undefined,
    peakLagDays: undefined,
    withinProximity: inInterval.length > 0,
    atOrAboveThreshold: atOrAbove,
    pass: inInterval.length > 0 && atOrAbove,
    overlapFraction,
  }
}

/** DR-13(c): a chain "hits" if any named milestone hits — never collapsed to one fuzzy date. */
function scoreChain(curve: CurvePoint[], event: CurveEvent, percentile: number): CurveEventScore {
  const milestones = event.milestones ?? []
  if (milestones.length === 0) throw new Error(`scoreChain: event ${event.eventId} has shape='chain' but no milestones`)
  const milestoneScores = milestones.map((m) => scoreCurveEvent(curve, m, percentile))
  const anyPass = milestoneScores.some((s) => s.pass)
  return {
    eventId: event.eventId,
    shape: 'chain',
    dateConfidence: event.dateConfidence,
    secondaryBattery: false, // per-milestone, carried in milestoneScores
    thresholdPercentile: percentile,
    thresholdValue: milestoneScores[0]?.thresholdValue ?? 0,
    withinProximity: milestoneScores.some((s) => s.withinProximity),
    atOrAboveThreshold: anyPass,
    pass: anyPass,
    milestoneScores,
  }
}

/** Single dispatch point, mirroring checks.ts's `scoreShapeAwareEvent` but curve-input (model-agnostic). */
export function scoreCurveEvent(curve: CurvePoint[], event: CurveEvent, percentile: number): CurveEventScore {
  if (event.shape === 'point') return scorePoint(curve, event, percentile)
  if (event.shape === 'interval') return scoreInterval(curve, event, percentile)
  return scoreChain(curve, event, percentile)
}

export type BlindBatteryResult = {
  scoredCount: number
  hitCount: number
  hitRate: number
  perEvent: CurveEventScore[]
}

/** DR-13(d): year_only events are excluded from the primary battery here — caller runs them through a separate secondary-battery pass with the same function, kept distinct per the ratified rule. */
export function runBlindBattery(curveFor: (event: CurveEvent) => CurvePoint[], events: CurveEvent[], percentile: number, includeSecondary = false): BlindBatteryResult {
  const eligible = events.filter((e) => includeSecondary || !isSecondaryBattery(e.dateConfidence))
  const perEvent = eligible.map((e) => scoreCurveEvent(curveFor(e), e, percentile))
  const hits = perEvent.filter((s) => s.pass)
  return {
    scoredCount: perEvent.length,
    hitCount: hits.length,
    hitRate: perEvent.length > 0 ? hits.length / perEvent.length : 0,
    perEvent,
  }
}
