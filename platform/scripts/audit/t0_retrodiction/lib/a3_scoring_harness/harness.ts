/**
 * harness.ts — the model-agnostic scoring harness itself (BRIEF_D4A.md
 * Lane A-3, deliverable 4: "control-mirroring ENFORCED IN THE HARNESS —
 * a scoring rule not applied to the control refuses to run").
 *
 * DIS.026/DR-13(e): "every scoring loosening applies IDENTICALLY to the
 * shuffled-birth negative control — a looser real-chart criterion without
 * an identically-loosened control is gate-gaming by definition."
 * DIS.028/DR-15(d): "Pre-registration of thresholds/event-sets/win-criteria
 * to the ledger BEFORE any scoring run is mandatory; post-hoc adjustment is
 * gate-gaming."
 *
 * STRUCTURAL enforcement (not a comment, not a convention): the harness
 * takes exactly ONE `MirroredScoringParams` object and applies the SAME
 * object reference to both the real curve and every control curve inside
 * `runMirroredScoringHarness`. There is no code path here that accepts two
 * separately-authored params objects for real vs. control — the only way
 * to run an asymmetric config is to call the lower-level pieces directly
 * and bypass this module, which `assertMirrored` (used by
 * `runComparativeHarness`, the entry point that DOES accept two params
 * objects — for the one legitimate use case of a caller explicitly
 * auditing two configs against each other) catches and rejects.
 */
import type { CurvePoint } from '../curve'
import type { TemporalCurveModel, ChartContext, EventClass } from './model_interface'
import { shuffledBirthControlCurve, antiphaseControlCurve } from './curve_controls'
import { runBlindBattery, type CurveEvent, type BlindBatteryResult } from './shape_scoring'
import { crps, skill } from './proper_scoring'
import { assertNoSealedSplitEvents } from './sealed_split_guard'

export type MirroredScoringParams = {
  /** DR-13(a) percentile threshold: 0.9 top-decile (point checks), 2/3 top-tercile (blind battery). */
  percentile: number
  /** How many evenly-spaced shuffled-birth control shifts to run (mirrors checks.ts's SHUFFLE_COUNT discipline). */
  shuffleCount: number
  /** Whether to include DR-13(d) year_only events in a secondary battery pass. */
  includeSecondaryBattery: boolean
}

export class ControlMirroringViolationError extends Error {
  constructor(diffs: string[]) {
    super(`Control-mirroring violation (DR-13(e)/DIS.026, non-negotiable): the real-chart scoring config and the control scoring config differ on: ${diffs.join(', ')}. Every scoring loosening must apply IDENTICALLY to the control. This run is REFUSED, not silently scored unfairly.`)
    this.name = 'ControlMirroringViolationError'
  }
}

/**
 * Deep-compares two `MirroredScoringParams` and throws
 * `ControlMirroringViolationError` naming every differing field if they are
 * not identical. This is the structural check the brief requires — a
 * one-sided config attempt is rejected here, not by convention.
 */
export function assertMirrored(realParams: MirroredScoringParams, controlParams: MirroredScoringParams): void {
  const diffs: string[] = []
  if (realParams.percentile !== controlParams.percentile) diffs.push(`percentile (real=${realParams.percentile}, control=${controlParams.percentile})`)
  if (realParams.shuffleCount !== controlParams.shuffleCount) diffs.push(`shuffleCount (real=${realParams.shuffleCount}, control=${controlParams.shuffleCount})`)
  if (realParams.includeSecondaryBattery !== controlParams.includeSecondaryBattery)
    diffs.push(`includeSecondaryBattery (real=${realParams.includeSecondaryBattery}, control=${controlParams.includeSecondaryBattery})`)
  if (diffs.length > 0) throw new ControlMirroringViolationError(diffs)
}

export type HarnessInput = {
  model: TemporalCurveModel
  chart: ChartContext
  eventClass: EventClass
  events: CurveEvent[]
  boundsStart: Date
  boundsEnd: Date
  params: MirroredScoringParams
}

export type HarnessResult = {
  modelId: string
  eventClass: EventClass
  params: MirroredScoringParams
  primary: {
    metric: 'CRPS/log-score'
    perEventReal: { eventId: string; crps: number; logScore: number; eventInRange: boolean }[]
    perEventControlShuffled: { eventId: string; crps: number; logScore: number }[][] // outer = per shift, inner = per event
    perEventControlAntiphase: { eventId: string; crps: number; logScore: number }[]
    meanCrpsReal: number
    meanCrpsControlShuffled: number // averaged across shifts and events
    meanCrpsControlAntiphase: number
    skillVsShuffled: number | null
    skillVsAntiphase: number | null
  }
  secondary: {
    metric: 'hit-rate (±45d top-decile, legacy)'
    real: BlindBatteryResult
    shuffledMeanHitRate: number
    antiphaseHitRate: BlindBatteryResult
    controlGapShuffled: number
    controlGapAntiphase: number
  }
  note: string
}

/** Point-in-time "true date" for CRPS/log-score. Point events use eventDate; interval events use intervalStart (the onset); chain events use the earliest milestone's true date. Documented judgment call — CRPS needs a scalar observation, DR-13's shape typology does not define one for interval/chain, so this module picks the onset/earliest-milestone convention consistently for real and control alike (never differently). */
function trueDateFor(event: CurveEvent): Date {
  if (event.eventDate) return event.eventDate
  if (event.intervalStart) return event.intervalStart
  if (event.milestones && event.milestones.length > 0) {
    return event.milestones.map(trueDateFor).sort((a, b) => a.getTime() - b.getTime())[0]
  }
  throw new Error(`trueDateFor: event ${event.eventId} has no resolvable date (shape=${event.shape})`)
}

function scoreProperAgainstCurve(curveFor: (e: CurveEvent) => CurvePoint[], events: CurveEvent[]): { perEvent: { eventId: string; crps: number; logScore: number; eventInRange: boolean }[]; meanCrps: number } {
  const perEvent = events.map((e) => {
    const c = crps(curveFor(e), trueDateFor(e))
    return { eventId: e.eventId, crps: c.crps, logScore: c.logScore, eventInRange: c.eventInRange }
  })
  const meanCrps = perEvent.length > 0 ? perEvent.reduce((s, p) => s + p.crps, 0) / perEvent.length : NaN
  return { perEvent, meanCrps }
}

/**
 * The single-params entry point (structurally mirroring by construction —
 * one `params` object is applied to real and every control, no asymmetric
 * config is even representable through this function's signature).
 */
export function runMirroredScoringHarness(input: HarnessInput): HarnessResult {
  // CR-123/DR-20: structural sealed-test-split enforcement. This is the ONE function every
  // contender's scoring call funnels through (pratyantar_lord, every PERMISSION system, and
  // the ensemble alike) — placing the gate here, first, means no driver/batch/contender type
  // can produce a score without passing this check, regardless of what its own dispatch
  // instructions said. See sealed_split_guard.ts's module docstring for the incident this
  // fixes (the D-4b B-1 chunked re-run's quarantined sealed-split breach).
  assertNoSealedSplitEvents(input.events)
  const { model, chart, eventClass, events, boundsStart, boundsEnd, params } = input
  const range: [Date, Date] = [boundsStart, boundsEnd]
  const realCurve = model.curve(chart, eventClass, range)

  // ── Primary: CRPS/log-score ────────────────────────────────────────
  const realProper = scoreProperAgainstCurve(() => realCurve, events)

  const totalDays = Math.round((boundsEnd.getTime() - boundsStart.getTime()) / 86_400_000)
  const shuffledResults: { eventId: string; crps: number; logScore: number }[][] = []
  const shuffledMeans: number[] = []
  for (let i = 1; i <= params.shuffleCount; i++) {
    const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * i)
    const shuffledCurve = shuffledBirthControlCurve(realCurve, shiftDays, boundsStart, boundsEnd)
    const r = scoreProperAgainstCurve(() => shuffledCurve, events)
    shuffledResults.push(r.perEvent)
    shuffledMeans.push(r.meanCrps)
  }
  const meanCrpsControlShuffled = shuffledMeans.length > 0 ? shuffledMeans.reduce((s, v) => s + v, 0) / shuffledMeans.length : NaN

  const antiphaseCurve = antiphaseControlCurve(realCurve, boundsStart, boundsEnd)
  const antiphaseProper = scoreProperAgainstCurve(() => antiphaseCurve, events)

  // ── Secondary: hit-rate (legacy) ───────────────────────────────────
  const realHits = runBlindBattery(() => realCurve, events, params.percentile, params.includeSecondaryBattery)
  const shuffledHitRates = Array.from({ length: params.shuffleCount }, (_, idx) => {
    const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * (idx + 1))
    const shuffledCurve = shuffledBirthControlCurve(realCurve, shiftDays, boundsStart, boundsEnd)
    return runBlindBattery(() => shuffledCurve, events, params.percentile, params.includeSecondaryBattery).hitRate
  })
  const shuffledMeanHitRate = shuffledHitRates.length > 0 ? shuffledHitRates.reduce((s, v) => s + v, 0) / shuffledHitRates.length : 0
  const antiphaseHits = runBlindBattery(() => antiphaseCurve, events, params.percentile, params.includeSecondaryBattery)

  return {
    modelId: model.modelId,
    eventClass,
    params,
    primary: {
      metric: 'CRPS/log-score',
      perEventReal: realProper.perEvent,
      perEventControlShuffled: shuffledResults,
      perEventControlAntiphase: antiphaseProper.perEvent,
      meanCrpsReal: realProper.meanCrps,
      meanCrpsControlShuffled,
      meanCrpsControlAntiphase: antiphaseProper.meanCrps,
      skillVsShuffled: skill(realProper.meanCrps, meanCrpsControlShuffled),
      skillVsAntiphase: skill(realProper.meanCrps, antiphaseProper.meanCrps),
    },
    secondary: {
      metric: 'hit-rate (±45d top-decile, legacy)',
      real: realHits,
      shuffledMeanHitRate,
      antiphaseHitRate: antiphaseHits,
      controlGapShuffled: realHits.hitRate - shuffledMeanHitRate,
      controlGapAntiphase: realHits.hitRate - antiphaseHits.hitRate,
    },
    note: 'CRPS/log-score is PRIMARY per DIS.028/DR-15(b); hit-rate is retained SECONDARY per the same ruling. skill = 1 - CRPS_model/CRPS_control (null if control CRPS is exactly 0, never fabricated). Every control shares this run\'s single `params` object by construction — see runComparativeHarness for the (guarded) two-params entry point.',
  }
}

/**
 * The two-params entry point — the ONLY place in this module a caller can
 * supply separately-authored real vs. control configs, for the legitimate
 * case of explicitly auditing whether two configs are mirrored. Calls
 * `assertMirrored` FIRST; a mismatched pair never reaches the scoring
 * logic. This is the function the acceptance-proof test drives to
 * demonstrate a live refusal.
 */
export function runComparativeHarness(input: Omit<HarnessInput, 'params'> & { realParams: MirroredScoringParams; controlParams: MirroredScoringParams }): HarnessResult {
  assertMirrored(input.realParams, input.controlParams) // throws ControlMirroringViolationError on any asymmetry — the run does not proceed past this line
  return runMirroredScoringHarness({ ...input, params: input.realParams })
}
