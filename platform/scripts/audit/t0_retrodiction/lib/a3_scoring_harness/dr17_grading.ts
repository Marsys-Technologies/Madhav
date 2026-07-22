/**
 * dr17_grading.ts — D-4b B-1 FULL RE-RUN lane (wave/D-4b/B1-full-rerun).
 *
 * Implements DR-17's graded manifestation-acceptance scale
 * (DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md §1/§2), ratified for B-1
 * consumption by NP-D4B-001 (six grade weights, RATIFIED VERBATIM) and
 * NP-D4B-003 (tie-band widths, ADOPTED with mandatory DR-13(d)-substitute
 * sensitivity check, condition (d)).
 *
 * PROVENANCE: this module did not exist before this lane.
 * `B1_NARROWED_STATUS_v1_0.md` §8 confirmed (grep for
 * `sub_peak|tie_band|anti_hit`, zero hits anywhere in `platform/`, this
 * session's own fresh grep against the F-1/F-2-merged tree reconfirmed the
 * same zero-hit result) that no DR-17 grading harness existed anywhere in
 * the codebase as of the narrowed run. Neither F-1 (PR #699, event_class
 * resolution) nor F-2 (PR #697, `circularShiftCurve` sort) touched this gap
 * — both fixed pre-existing defects in the CRPS/hit-rate path, not the
 * DR-17 grading path. Building it is this lane's own required work, per the
 * governing task's explicit "DR-17 grading per NP-D4B-001" instruction —
 * not a rebuild of anything "now-fixed" elsewhere, and not silently skipped
 * either.
 *
 * ── Judgment calls, documented (house style: curve_controls.ts's antiphase
 * docstring, proper_scoring.ts's CRPS-construction docstring) ────────────
 *
 * 1. **"Live-active" / structural-prior baseline (DR-17 §1's `peak`
 *    condition: "the mechanism... is a real, live-active system at that
 *    date, not a structural-prior placeholder").** Operationalized as: the
 *    curve's intensity at that grid index exceeds `mean + 1·stddev` of the
 *    SAME grid index across this run's own N=1000 DR-15(c) shuffled-birth
 *    control curves (the harness's own already-computed primary control,
 *    never the refused circular-shift null — NP-D4B-002). This directly
 *    operationalizes DR-17 §1's `neutral` grade's own language
 *    ("statistically indistinguishable from its coverage-matched
 *    shuffled-birth control") as the SAME baseline `peak`/`elevated`
 *    measure against, rather than inventing an unrelated second baseline
 *    concept. A flat/degenerate curve (e.g. a PERMISSION system saturated
 *    at a constant intensity because its target_count resolved to 0 before
 *    F-1) has mean≈control-mean and effectively NEVER clears this bar —
 *    which is the intended, honest consequence: `B1_NARROWED_STATUS_v1_0.md`
 *    §6 named exactly this degenerate-flat-curve failure mode ("a flat
 *    curve trivially 'hits' under percentile-threshold matching... real vs.
 *    control gap is exactly 0") as a real problem for the legacy hit-rate
 *    metric; this baseline check is DR-17 grading's structural guard against
 *    the same failure mode recurring here.
 * 2. **Local-maxima definition (packet §5: "K is not specimen-tuned and not
 *    a fixed numeric cap... every genuine local maximum").** A point whose
 *    intensity is >= both neighbors, with a maximal contiguous equal-value
 *    plateau collapsed to ONE local maximum located at the plateau's onset
 *    (earliest) index — consistent with `elevated`'s own plateau framing in
 *    DR-17 §1.
 * 3. **Tie-band dedup (DR-17 §2 mechanism, NP-D4B-003 widths):** local
 *    maxima are sorted by intensity descending; a maximum within the
 *    active tie-band width of an ALREADY-KEPT (higher-ranked) maximum is
 *    dropped (never separately graded/summed) — this module's own
 *    `dedupeByTieBand`.
 * 4. **Anti-hit double-weight (DR-17 §1, NP-D4B-001 condition (d): "per-event
 *    valence classification happens at grading time... a contested
 *    classification routes to the Fable doctrine seat").** DR-17 §1 defines
 *    the anti-hit condition as the model calling "a GAIN-valence peak where
 *    the truth was a loss, or vice versa" — a VALENCE call. None of B-1's 14
 *    contenders (pratyantar_lord's dasha-lord-confluence proxy; the 12
 *    PERMISSION standalone activation generators; their unweighted
 *    point-sum ensemble) emit a gain/loss polarity signal at all — every one
 *    of them outputs a single non-negative "how active/confluent is this
 *    mechanism" intensity, never a valence-typed direction. Inventing a
 *    valence classifier ON TOP of an activation-only curve, so this module
 *    could claim an anti-hit fired, would be exactly the "invents a signal
 *    the model didn't emit" failure B.10 forbids. **Disposition: anti-hit
 *    double-weight is therefore STRUCTURALLY INERT for this run's full
 *    contender roster — `contra` always scores at its ordinary DR-17 §1
 *    weight (−0.5), `antiHitApplied` is `false` on every graded row, with
 *    `antiHitInertReason` naming this exact reasoning.** This is disclosed
 *    per-row (§N.6 density discipline — never silently substituted, never
 *    hidden in an aggregate), not silently defaulted. NP-D4B-001 condition
 *    (d)'s "contested classification routes to Fable" is honored by NOT
 *    contesting a classification this module has no basis to assert in the
 *    first place.
 * 5. **`elevated` vs `neutral` vs `contra` at the true date/window.** Let
 *    `windowPeak` = the curve's own highest intensity within the event's
 *    matching window (point: ±tolerance; interval: [start,end]).
 *    - If `windowPeak` is above baseline (live-active, per judgment call 1)
 *      but is NOT itself one of the deduped local maxima (i.e. sits on a
 *      broader above-baseline plateau/slope rather than a distinct peak) →
 *      `elevated`.
 *    - Else if `windowPeak` is within the same baseline band (not
 *      distinguishably above OR below control) → `neutral`.
 *    - Else (`windowPeak` is at-or-below baseline, i.e. the model is
 *      genuinely quiet at the true date) AND the model has at least one
 *      deduped, live-active local maximum OUTSIDE the matching window
 *      (elsewhere in the scored range) → `contra` (DR-17 §1: "serves an
 *      ACTIVE peak/window for a DIFFERENT, non-overlapping date... while the
 *      true date scores neutral or below").
 *    - Else (quiet at the true date AND quiet everywhere else too — an
 *      honest, uniform non-finding, not a wrong-elsewhere call) → `neutral`.
 *      DR-17 §1's `contra` text requires an ACTIVE elsewhere-call; a model
 *      that found nothing anywhere is graded as an honest miss, not
 *      penalized as if it had pointed somewhere specific and wrong. This
 *      reading is a documented judgment call, not stated in so many words
 *      by DR-17 §1 itself, flagged here rather than silently assumed.
 *
 * ── Harness-refusal guard (DR-17 §2, NP-D4B-001(a), NP-D4B-003(b)) ───────
 * The six grade weights and four tie-band widths below are the packet
 * (D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §4)-committed values, verbatim.
 * `gradeCurveEvent`/`gradeDr17Batch` never accept a caller-supplied weight
 * or tie-band override — the only parameterization exposed is `tieBandSet`,
 * which selects between the two PRE-REGISTERED tables (`adopted` vs
 * `dr13d_sensitivity`, NP-D4B-003 condition (d)'s mandatory comparator),
 * never an arbitrary third value. This is the structural enforcement
 * pattern `harness.ts`'s `assertMirrored` and `roster_bind.ts`'s
 * `assertRosterBindable` already establish in this codebase — a mismatch is
 * impossible to construct through this module's own public surface, not
 * merely discouraged by convention.
 */
import type { CurvePoint } from '../curve'
import { daysBetween } from '../dates'

export type Grade = 'peak' | 'sub_peak' | 'elevated' | 'neutral' | 'contra'

/** NP-D4B-001: RATIFIED VERBATIM. Frozen at first scoring call (condition (b)) — not exported as mutable. */
export const DR17_GRADE_WEIGHTS: Readonly<Record<Grade, number>> = Object.freeze({
  peak: 1.0,
  sub_peak: 0.75,
  elevated: 0.5,
  neutral: 0.0,
  contra: -0.5,
})

/** NP-D4B-001 §1: proposed −1.0 double-weight for a valence-crossing contra. Structurally inert this run — see module docstring, judgment call 4. Exported for completeness/tests, never applied by `gradeCurveEvent` below. */
export const DR17_ANTI_HIT_WEIGHT = -1.0

export type DateConfidenceTier = 'day' | 'week' | 'month' | 'year'

/** Maps this codebase's existing `shape_scoring.ts` `DateConfidence` vocabulary onto DR-17's four-tier tie-band vocabulary. 'week' has no DB-schema representative pre-2020 (it was introduced by a post-2020 native date-tightening item) — included for completeness and tested, but never exercised by this run's TRAIN-side event set (disclosed in the run report, not silently assumed absent). */
export function tierForDateConfidence(dc: 'exact' | 'month_known' | 'year_only'): DateConfidenceTier {
  if (dc === 'exact') return 'day'
  if (dc === 'month_known') return 'month'
  return 'year'
}

/** NP-D4B-003: ADOPTED, packet §4 v1.1/v1.2 table, verbatim. */
export const TIE_BAND_WIDTHS_DAYS: Readonly<Record<DateConfidenceTier, number>> = Object.freeze({ day: 3, week: 7, month: 45, year: 180 })

/** NP-D4B-003 condition (d): the MANDATORY DR-13(d)-substitute sensitivity comparator (day/month replaced by DR-13(d)'s own point-tolerance figures; week/year unchanged — DR-13(d) defines no value for either tier). Diagnostic/comparator ONLY — never the primary graded result on its own (condition (d): "may make a result look WORSE... never better"). */
export const DR13D_SUBSTITUTE_TIE_BAND_WIDTHS_DAYS: Readonly<Record<DateConfidenceTier, number>> = Object.freeze({ day: 45, week: 7, month: 75, year: 180 })

export type TieBandSet = 'adopted' | 'dr13d_sensitivity'

function tieBandTableFor(set: TieBandSet): Record<DateConfidenceTier, number> {
  return set === 'adopted' ? TIE_BAND_WIDTHS_DAYS : DR13D_SUBSTITUTE_TIE_BAND_WIDTHS_DAYS
}

export type GradingEvent = {
  eventId: string
  shape: 'point' | 'interval'
  dateConfidenceTier: DateConfidenceTier
  /** DR-13(d)/packet §3 point-match tolerance in days. Ignored for interval shape. */
  matchToleranceDays: number
  eventDate?: Date // point
  intervalStart?: Date // interval
  intervalEnd?: Date // interval
}

export type ControlBaseline = { meanByIndex: number[]; stdByIndex: number[] }

/** Computes the per-grid-index mean/stddev across a set of control curves (all assumed grid-aligned to the same length/dates as the real curve they will be compared against — caller's responsibility, mirrors `ensemble_model.ts`'s own grid-alignment contract). This is this run's OWN DR-15(c) shuffled-birth control set — never the refused circular-shift null (NP-D4B-002). */
export function computeControlBaseline(controlCurves: CurvePoint[][]): ControlBaseline {
  if (controlCurves.length === 0) throw new Error('computeControlBaseline: at least one control curve is required')
  const n = controlCurves[0].length
  const meanByIndex: number[] = new Array(n).fill(0)
  for (const c of controlCurves) {
    if (c.length !== n) throw new Error(`computeControlBaseline: control curve grid-length mismatch (expected ${n}, got ${c.length}) — every control must be grid-aligned to the real curve.`)
    for (let i = 0; i < n; i++) meanByIndex[i] += c[i].intensity
  }
  for (let i = 0; i < n; i++) meanByIndex[i] /= controlCurves.length
  const stdByIndex: number[] = new Array(n).fill(0)
  for (const c of controlCurves) {
    for (let i = 0; i < n; i++) stdByIndex[i] += (c[i].intensity - meanByIndex[i]) ** 2
  }
  for (let i = 0; i < n; i++) stdByIndex[i] = Math.sqrt(stdByIndex[i] / controlCurves.length)
  return { meanByIndex, stdByIndex }
}

export type LocalMaximum = { index: number; date: Date; intensity: number }

/**
 * Judgment call 2 (module docstring): every genuine local maximum,
 * plateau-collapsed to its onset index.
 *
 * BOUNDARY NOTE: a monotonically-non-increasing run reaching the curve's
 * final index is always locally-maximal at its own onset (there is no
 * later neighbor to disqualify it) — a mostly-zero curve's trailing flat
 * tail therefore always registers its own (typically intensity-0) maximum.
 * This is intentional (the all-zero-curve test below documents it as the
 * degenerate case) and harmless to grading: `gradeCurveEvent` only acts on
 * a maximum that also clears `isAboveBaseline`, which a trailing intensity-0
 * tail essentially never does against a real (non-negative-mean) control
 * baseline — it can inflate the raw `dedupedMaximaCount` reported alongside
 * a grade, never change the grade itself.
 */
export function findLocalMaxima(curve: CurvePoint[]): LocalMaximum[] {
  const out: LocalMaximum[] = []
  let i = 0
  while (i < curve.length) {
    const prev = i > 0 ? curve[i - 1].intensity : -Infinity
    if (curve[i].intensity < prev) {
      i++
      continue
    }
    // Walk forward through a maximal equal-value plateau.
    let j = i
    while (j + 1 < curve.length && curve[j + 1].intensity === curve[i].intensity) j++
    const next = j + 1 < curve.length ? curve[j + 1].intensity : -Infinity
    if (curve[i].intensity >= prev && curve[i].intensity >= next) {
      out.push({ index: i, date: curve[i].date, intensity: curve[i].intensity })
    }
    i = j + 1
  }
  return out
}

/** Judgment call 3: tie-band dedup. Highest-intensity maxima kept first; any lower-ranked maximum within `tieBandDays` of an already-kept one is dropped. */
export function dedupeByTieBand(maxima: LocalMaximum[], tieBandDays: number): LocalMaximum[] {
  const sorted = [...maxima].sort((a, b) => b.intensity - a.intensity)
  const kept: LocalMaximum[] = []
  for (const m of sorted) {
    const nearAKept = kept.some((k) => Math.abs(daysBetween(k.date, m.date)) <= tieBandDays)
    if (!nearAKept) kept.push(m)
  }
  return kept
}

function matchesEvent(date: Date, event: GradingEvent): boolean {
  if (event.shape === 'point') {
    if (!event.eventDate) throw new Error(`matchesEvent: point event ${event.eventId} missing eventDate`)
    return Math.abs(daysBetween(event.eventDate, date)) <= event.matchToleranceDays
  }
  if (!event.intervalStart || !event.intervalEnd) throw new Error(`matchesEvent: interval event ${event.eventId} missing bounds`)
  return date.getTime() >= event.intervalStart.getTime() && date.getTime() <= event.intervalEnd.getTime()
}

export type GradeResult = {
  eventId: string
  modelId: string
  grade: Grade
  weight: number
  antiHitApplied: false
  antiHitInertReason: string
  matchedPeakRank: number | null
  matchedPeakDate: string | null
  tieBandSet: TieBandSet
  tieBandWidthDaysUsed: number
  dedupedMaximaCount: number
  reason: string
}

const ANTI_HIT_INERT_REASON =
  "B-1's 14 contenders emit activation-only (non-negative, valence-free) intensity curves; DR-17 §1's anti-hit double-weight requires a GAIN/LOSS valence call this contender class structurally cannot make (module docstring, judgment call 4) — contra always scores at its ordinary -0.5 weight this run."

/**
 * Grades one (curve, event) pair per DR-17 §1's scale, using `baseline`
 * (this event's own already-computed DR-15(c) control summary — see
 * `computeControlBaseline`) as the "live-active"/structural-prior reference.
 * `curve` and every control curve feeding `baseline` MUST already be
 * grid-aligned (same dates/length) — this function does not re-grid.
 */
export function gradeCurveEvent(curve: CurvePoint[], event: GradingEvent, baseline: ControlBaseline, modelId: string, tieBandSet: TieBandSet = 'adopted'): GradeResult {
  if (curve.length === 0) throw new Error(`gradeCurveEvent: empty curve for event ${event.eventId}, model ${modelId}`)
  if (curve.length !== baseline.meanByIndex.length) {
    throw new Error(`gradeCurveEvent: curve length (${curve.length}) does not match control baseline length (${baseline.meanByIndex.length}) for event ${event.eventId}, model ${modelId} — grid misalignment.`)
  }
  const tieBandDays = tieBandTableFor(tieBandSet)[event.dateConfidenceTier]
  const isAboveBaseline = (idx: number) => curve[idx].intensity > baseline.meanByIndex[idx] + baseline.stdByIndex[idx]
  const isBelowOrAtBaseline = (idx: number) => curve[idx].intensity <= baseline.meanByIndex[idx] + baseline.stdByIndex[idx]

  const maxima = findLocalMaxima(curve)
  const deduped = dedupeByTieBand(maxima, tieBandDays).sort((a, b) => b.intensity - a.intensity)

  const mk = (grade: Grade, matchedPeakRank: number | null, matchedPeakDate: string | null, reason: string): GradeResult => ({
    eventId: event.eventId,
    modelId,
    grade,
    weight: DR17_GRADE_WEIGHTS[grade],
    antiHitApplied: false,
    antiHitInertReason: ANTI_HIT_INERT_REASON,
    matchedPeakRank,
    matchedPeakDate,
    tieBandSet,
    tieBandWidthDaysUsed: tieBandDays,
    dedupedMaximaCount: deduped.length,
    reason,
  })

  for (let rank = 0; rank < deduped.length; rank++) {
    const m = deduped[rank]
    if (isAboveBaseline(m.index) && matchesEvent(m.date, event)) {
      const grade: Grade = rank === 0 ? 'peak' : 'sub_peak'
      return mk(
        grade,
        rank + 1,
        m.date.toISOString().slice(0, 10),
        `deduped local maximum rank ${rank + 1}/${deduped.length} (intensity=${m.intensity.toFixed(4)}, control baseline mean+1sd=${(baseline.meanByIndex[m.index] + baseline.stdByIndex[m.index]).toFixed(4)}) matches event within its ${event.shape === 'point' ? `±${event.matchToleranceDays}d point tolerance` : 'interval bounds'}.`
      )
    }
  }

  // No matching live-active local maximum. Examine the event's own matching window.
  const inWindowIdx: number[] = []
  for (let i = 0; i < curve.length; i++) {
    if (matchesEvent(curve[i].date, event)) inWindowIdx.push(i)
  }
  if (inWindowIdx.length === 0) {
    return mk('neutral', null, null, `event's matching window contains zero curve grid points (out of the model's scored range) — honest miss, no distinguishable signal to grade.`)
  }
  let windowPeakIdx = inWindowIdx[0]
  for (const i of inWindowIdx) if (curve[i].intensity > curve[windowPeakIdx].intensity) windowPeakIdx = i

  if (isAboveBaseline(windowPeakIdx)) {
    return mk(
      'elevated',
      null,
      curve[windowPeakIdx].date.toISOString().slice(0, 10),
      `window peak (intensity=${curve[windowPeakIdx].intensity.toFixed(4)}) exceeds control baseline mean+1sd=${(baseline.meanByIndex[windowPeakIdx] + baseline.stdByIndex[windowPeakIdx]).toFixed(4)} but is not itself a tie-band-deduped local maximum matching the event — plateau/slope overlap, DR-17 §1 elevated case.`
    )
  }

  if (isBelowOrAtBaseline(windowPeakIdx)) {
    const elsewhereActive = deduped.find((m) => isAboveBaseline(m.index) && !matchesEvent(m.date, event))
    if (elsewhereActive) {
      return mk(
        'contra',
        null,
        elsewhereActive.date.toISOString().slice(0, 10),
        `true date/window scores at-or-below control baseline (window peak intensity=${curve[windowPeakIdx].intensity.toFixed(4)}) while the model serves a live-active, non-overlapping local maximum at ${elsewhereActive.date.toISOString().slice(0, 10)} (intensity=${elsewhereActive.intensity.toFixed(4)}) — DR-17 §1 contra: model pointed somewhere wrong with confidence. Anti-hit double-weight NOT applied: ${ANTI_HIT_INERT_REASON}`
      )
    }
  }

  return mk(
    'neutral',
    null,
    null,
    `window peak (intensity=${curve[windowPeakIdx].intensity.toFixed(4)}) is statistically indistinguishable from the control baseline (mean=${baseline.meanByIndex[windowPeakIdx].toFixed(4)}, sd=${baseline.stdByIndex[windowPeakIdx].toFixed(4)}) and the model has no live-active elsewhere-peak to call wrong — honest null result, DR-17 §1 neutral.`
  )
}
