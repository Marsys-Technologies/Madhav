#!/usr/bin/env -S npx tsx
/**
 * b1_batch3_driver.ts — D-4b B-1 chunked re-run, BATCH 3/3 (key="batch3").
 *
 * Scores the 4 contenders assigned to batch3 by B1_RUN_MANIFEST_v1_0.json's
 * `batching.batches[2]`: guru_shani_double_transit, av_threshold,
 * planetary_return (PERMISSION_SYSTEM_IDS), then hierarchical_ensemble LAST
 * (per the manifest note: "build last, per BRIEF_D4B §1"), over whichever
 * of the 13 non-ensemble contenders (pratyantar_lord + all 12
 * PERMISSION_SYSTEM_IDS) are evaluable across all 3 batches. batch1
 * (pratyantar_lord, vimshottari, yogini, ashtottari, chara_karaka) and
 * batch2 (naisargika, mudda, kalachakra, narayana, sade_sati) both recorded
 * eventsErrored=0 for every one of their contenders
 * (batch_batch1.json/batch_batch2.json summaries, read this session) — this
 * batch's own 3 PERMISSION contenders below are checked the same way before
 * being fed into the ensemble. If any of the 13 errors here, it is EXCLUDED
 * from the ensemble's `contenders` list and the exclusion is recorded in
 * the artifact — never silently dropped or silently substituted.
 *
 * Against the manifest's cited D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §1
 * event set (56 events; 54 scored, per the same §0 recommendation batch1/2
 * already applied). The 54-row event list is copied VERBATIM from
 * b1_batch1_driver_v1_0.ts / b1_batch2_driver_v1_0.ts (not re-derived) —
 * BRIEF_D4B §1's "identical everything" rule.
 *
 * Live substrate this batch:
 *  - guru_shani_double_transit / av_threshold / planetary_return: each
 *    resolves its curve via ONE live HTTP call per (chart, eventClass,
 *    range) to the already-deployed Python sidecar's
 *    `/api/compute/permission_curve` route — same mechanism batch2 already
 *    confirmed reachable this session-day (200, real per-system intensity
 *    points).
 *  - hierarchical_ensemble: sums the OWN `curve()` output of every
 *    evaluable non-ensemble contender, unweighted, point-for-point
 *    (ensemble_model.ts's own documented design — no invented cross-model
 *    weighting). Needs pratyantar_lord's substrate (vimshottari dasha
 *    periods, levels<=3, already live-fetched by batch1 this session-day
 *    into vimshottari_periods_full.json — reused here, not re-fetched) PLUS
 *    all 12 PERMISSION models bound via the same sidecar route.
 *
 * Event-class resolution: SAME 3-of-54 resolved events as batch1/batch2
 * (EVT.2010.XX.XX.01 / EVT.2013.12.11.01 / EVT.2025.07.XX.01, both
 * resolving to 'major_gain' or 'marriage' per gochara_resonance_map's
 * already-live-verified 3-class scope for this chart), reused verbatim —
 * not re-queried a third time. All 3 batch3 PERMISSION contenders are
 * honestly SKIPPED (not fallback-scored) for the other 51 unresolved
 * events, matching F-1/batch1/batch2's established design. The ensemble is
 * necessarily scored on the SAME 3-event slice only, since 12 of its 13
 * constituents require a resolved event class to be evaluable at all — an
 * ensemble scored on fewer than all 13 available constituents would not be
 * this run's actual roster.
 *
 * J-ENSEMBLE-1 (new judgment call, this batch): the `hierarchicalEnsembleModel`
 * contract calls every constituent's `curve(chart, eventClass, range)` with
 * ONE SHARED `eventClass` value — but batch1's pratyantar_lord was always
 * scored with `eventClass = row.category` (an LEL free-text category, e.g.
 * 'finance'/'family'), while the PERMISSION contenders (batch1-3) were
 * always scored with `eventClass = row.resolvedEventClass` (a
 * gochara_resonance_map class, e.g. 'major_gain'/'marriage') — two
 * different value spaces for the same `EventClass = string` type. For the
 * ensemble ONLY, both families must receive the SAME argument, so this
 * driver extends batch1's own `eventClassSignificators` map (unchanged
 * DOMAIN_LORDS weights, zero new numbers invented) with two additional
 * KEY ALIASES pointing at the SAME pre-existing domain entries the
 * corresponding LEL category already maps to for these exact 3 rows:
 * 'major_gain' -> DOMAIN_LORDS.wealth (both EVT.2010.XX.XX.01 and
 * EVT.2025.07.XX.01 have category='finance', which CATEGORY_TO_DOMAIN
 * already maps to 'wealth'); 'marriage' -> DOMAIN_LORDS.marriage
 * (EVT.2013.12.11.01 has category='family', which CATEGORY_TO_DOMAIN
 * already maps to 'marriage', i.e. the SAME domain the class name itself
 * names). No new significator weight is introduced; this is a key-alias
 * extension of an already-committed table, not a new model design. Called
 * out explicitly, per house style (batch1's own J1-J7 discipline), rather
 * than silently assumed.
 *
 * Imports the REAL, already-merged harness modules (model_interface.ts,
 * permission_model.ts, harness.ts, dr17_grading.ts, curve_controls.ts,
 * ensemble_model.ts) — no reimplementation of any scoring math.
 */
import { writeFileSync, readFileSync } from 'node:fs'
import type { ChartContext, EventClass } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { pratyantarLordModel } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { allPermissionSystemModels, PERMISSION_SYSTEM_IDS } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/permission_model'
import { hierarchicalEnsembleModel } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/ensemble_model'
import { runMirroredScoringHarness, type MirroredScoringParams } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/harness'
import type { CurveEvent, DateConfidence, EventShape } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/shape_scoring'
import {
  gradeCurveEvent, computeControlBaseline, type GradingEvent, type DateConfidenceTier, type GradeResult,
} from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/dr17_grading'
import { shuffledBirthControlCurve } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/curve_controls'
import type { DashaPeriod, CurvePoint } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/curve'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const SIDECAR_URL = process.env.PYTHON_SIDECAR_URL || 'https://amjis-sidecar-938361928218.asia-south1.run.app'
const API_KEY = process.env.PYTHON_SIDECAR_API_KEY || ''
const SCRATCH = '/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/cb8619fb-b398-41cc-a7e7-6cc6c9eafb53/scratchpad'
const RUN_REF_DATE = '2026-07-22' // this session's own reference "now" (J3), same as batch1/2

type Row = {
  eventId: string
  category: string
  shape: EventShape
  tier: DateConfidenceTier
  eventDate?: string
  intervalStart?: string
  intervalEnd?: string
  resolvedEventClass: EventClass | null
  note: string
}

// D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §1, git blob 9b6713db8c2551a937ff2070e498da1f12526966.
// VERBATIM COPY of b1_batch1_driver_v1_0.ts / b1_batch2_driver_v1_0.ts's ROWS (54 of 56 rows) --
// cross-batch event-set identity, see module header.
const ROWS: Row[] = [
  { eventId: 'EVT.1995.XX.XX.01', category: 'health', shape: 'interval', tier: 'year', intervalStart: '1995-01-01', intervalEnd: '2021-12-31', resolvedEventClass: null, note: 'chain/interval hybrid, J1: scored as full onset-to-resolution interval' },
  { eventId: 'EVT.1998.02.16.01', category: 'relationship', shape: 'point', tier: 'day', eventDate: '1998-02-16', resolvedEventClass: null, note: 'R#1 start' },
  { eventId: 'EVT.2000.XX.XX.01', category: 'education', shape: 'interval', tier: 'month', intervalStart: '2000-06-01', intervalEnd: '2000-12-31', resolvedEventClass: null, note: '' },
  { eventId: 'EVT.2001.03.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2001-03-15', resolvedEventClass: null, note: 'IIT-prep start, chain milestone 1/2' },
  { eventId: 'EVT.2003.06.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2003-06-15', resolvedEventClass: null, note: 'IIT-prep end, chain milestone 2/2' },
  { eventId: 'EVT.2004.01.XX.01', category: 'relationship', shape: 'point', tier: 'month', eventDate: '2004-01-15', resolvedEventClass: null, note: 'R#2 start' },
  { eventId: 'EVT.2004.XX.XX.02', category: 'education', shape: 'point', tier: 'year', eventDate: '2004-07-01', resolvedEventClass: null, note: 'CMU declined, J4 midpoint' },
  { eventId: 'EVT.2007.06.XX.01', category: 'health', shape: 'point', tier: 'month', eventDate: '2007-06-15', resolvedEventClass: null, note: 'Knee arthroscopy, chain anchor' },
  { eventId: 'EVT.2007.XX.XX.03', category: 'health', shape: 'interval', tier: 'month', intervalStart: '2007-06-01', intervalEnd: '2025-12-31', resolvedEventClass: null, note: 'sleep-disorder onset->resolution, J1' },
  { eventId: 'EVT.2007.06.XX.02', category: 'education', shape: 'point', tier: 'month', eventDate: '2007-06-15', resolvedEventClass: null, note: 'Engineering completed' },
  { eventId: 'EVT.2007.06.10.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2007-06-10', resolvedEventClass: null, note: 'Cognizant joined' },
  { eventId: 'EVT.2008.06.09.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2008-06-09', resolvedEventClass: null, note: 'Cognizant exited' },
  { eventId: 'EVT.2009.06.XX.01', category: 'loss', shape: 'point', tier: 'month', eventDate: '2009-06-30', resolvedEventClass: null, note: "Grandfather's passing, point±bounds best_estimate" },
  { eventId: 'EVT.2002.XX.XX.01', category: 'psychological', shape: 'interval', tier: 'year', intervalStart: '2001-06-01', intervalEnd: '2005-06-30', resolvedEventClass: null, note: 'Vertigo peak' },
  { eventId: 'EVT.2002.XX.XX.02', category: 'spiritual', shape: 'interval', tier: 'year', intervalStart: '2002-01-01', intervalEnd: RUN_REF_DATE, resolvedEventClass: null, note: 'Shani Puja, open-ended, J3' },
  { eventId: 'EVT.1998.XX.XX.02', category: 'spiritual', shape: 'point', tier: 'year', eventDate: '1998-07-01', resolvedEventClass: null, note: "Father's dialogues, J4 midpoint, quarantine-item#3 NOT applied" },
  { eventId: 'EVT.2010.XX.XX.01', category: 'finance', shape: 'interval', tier: 'month', intervalStart: '2010-07-01', intervalEnd: '2011-03-31', resolvedEventClass: 'major_gain', note: 'Windfall, NAMED SPECIMEN, domain live-verified batch1 session (event_date<2020)' },
  { eventId: 'EVT.2010.12.XX.01', category: 'travel', shape: 'point', tier: 'month', eventDate: '2010-12-15', resolvedEventClass: null, note: 'Thailand trip' },
  { eventId: 'EVT.2011.01.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2011-01-15', resolvedEventClass: null, note: 'XIMB admission, chain 1/2' },
  { eventId: 'EVT.2011.06.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2011-06-15', resolvedEventClass: null, note: 'XIMB enrolled, chain 2/2' },
  { eventId: 'EVT.2012.09.XX.01', category: 'creative', shape: 'point', tier: 'month', eventDate: '2012-09-15', resolvedEventClass: null, note: 'Modeling' },
  { eventId: 'EVT.2012.XX.XX.02', category: 'education', shape: 'point', tier: 'year', eventDate: '2012-07-01', resolvedEventClass: null, note: 'IRC presidency, J4 midpoint' },
  { eventId: 'EVT.2012.10.XX.01', category: 'relationship', shape: 'point', tier: 'month', eventDate: '2012-10-15', resolvedEventClass: null, note: 'R#3 start, chain 1/2' },
  { eventId: 'EVT.2013.03.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2013-03-15', resolvedEventClass: null, note: 'MBA graduation' },
  { eventId: 'EVT.2013.05.XX.01', category: 'career', shape: 'point', tier: 'month', eventDate: '2013-05-15', resolvedEventClass: null, note: 'Mahindra Retail joined' },
  { eventId: 'EVT.2013.XX.XX.01', category: 'family', shape: 'interval', tier: 'year', intervalStart: '2013-01-01', intervalEnd: '2018-11-28', resolvedEventClass: null, note: "Father's illness onset->terminus, chain 1/2" },
  { eventId: 'EVT.2013.12.11.01', category: 'family', shape: 'point', tier: 'day', eventDate: '2013-12-11', resolvedEventClass: 'marriage', note: 'Marriage, NAMED SPECIMEN, domain live-verified batch1 session (event_date<2020)' },
  { eventId: 'EVT.1993.XX.XX.01', category: 'creative', shape: 'point', tier: 'year', eventDate: '1993-07-01', resolvedEventClass: null, note: 'Painting awards (M5A), J4 midpoint' },
  { eventId: 'EVT.2016.XX.XX.01', category: 'career', shape: 'point', tier: 'year', eventDate: '2016-07-01', resolvedEventClass: null, note: 'Mahindra Retail crash, J4 midpoint' },
  { eventId: 'EVT.2017.03.XX.01', category: 'career', shape: 'point', tier: 'month', eventDate: '2017-03-15', resolvedEventClass: null, note: 'Switch to Tech Mahindra' },
  { eventId: 'EVT.2018.11.28.01', category: 'loss', shape: 'point', tier: 'day', eventDate: '2018-11-28', resolvedEventClass: null, note: "Father's passing, chain terminus" },
  { eventId: 'EVT.2019.05.XX.01', category: 'residential+travel', shape: 'point', tier: 'month', eventDate: '2019-05-15', resolvedEventClass: null, note: 'US move, chain 1/2' },
  { eventId: 'EVT.2021.01.XX.01', category: 'health', shape: 'point', tier: 'month', eventDate: '2021-01-15', resolvedEventClass: null, note: 'Panic/anxiety episode' },
  { eventId: 'EVT.2021.XX.XX.02', category: 'career', shape: 'point', tier: 'year', eventDate: '2021-07-01', resolvedEventClass: null, note: 'Tepper selection, J4 midpoint, chain 2/3' },
  { eventId: 'EVT.2021.XX.XX.03', category: 'career', shape: 'point', tier: 'year', eventDate: '2021-07-01', resolvedEventClass: null, note: '2nd quarry stalled (tentative), J4 midpoint, chain 1/2' },
  { eventId: 'EVT.2022.01.03.01', category: 'family', shape: 'point', tier: 'day', eventDate: '2022-01-03', resolvedEventClass: null, note: 'Twins born' },
  { eventId: 'EVT.2022.XX.XX.02', category: 'relationship', shape: 'point', tier: 'week', eventDate: '2022-08-20', resolvedEventClass: null, note: 'Tepper-affair start, NAMED SPECIMEN, best_estimate' },
  { eventId: 'EVT.2022.10.XX.01', category: 'relationship', shape: 'point', tier: 'day', eventDate: '2022-07-14', resolvedEventClass: null, note: 'R#3 end, CORRECTED date, chain 2/2' },
  { eventId: 'EVT.2010.XX.XX.02', category: 'spiritual', shape: 'interval', tier: 'year', intervalStart: '2010-01-01', intervalEnd: RUN_REF_DATE, resolvedEventClass: null, note: 'Ugratara devotion, open-ended, J3' },
  { eventId: 'EVT.2015.XX.XX.01', category: 'spiritual', shape: 'point', tier: 'month', eventDate: '2021-04-15', resolvedEventClass: null, note: 'Mahadev/Shiva gravitation, CORRECTED to [2021-04->2021-05]' },
  { eventId: 'EVT.2023.05.XX.01', category: 'residential+travel', shape: 'point', tier: 'month', eventDate: '2023-05-15', resolvedEventClass: null, note: 'US return, chain 2/2' },
  { eventId: 'EVT.2023.06.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2023-06-15', resolvedEventClass: null, note: 'Tepper completed, chain terminus' },
  { eventId: 'EVT.2023.07.XX.01', category: 'career', shape: 'point', tier: 'month', eventDate: '2023-07-15', resolvedEventClass: null, note: 'Marsys founded' },
  { eventId: 'EVT.2024.02.16.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2024-02-16', resolvedEventClass: null, note: 'Kotadwara sand mine launch' },
  { eventId: 'EVT.2025.05.XX.01', category: 'loss', shape: 'point', tier: 'month', eventDate: '2025-05-15', resolvedEventClass: null, note: 'Financial deception/scam' },
  { eventId: 'EVT.2025.07.XX.01', category: 'finance', shape: 'point', tier: 'month', eventDate: '2025-07-15', resolvedEventClass: 'major_gain', note: 'First Marsys contract; domain by elimination, batch1 session -- NOT independently re-queried (>=2020-01-01)' },
  { eventId: 'EVT.2026.03.20.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2026-03-20', resolvedEventClass: null, note: 'Marsys Technology project closed' },
  { eventId: 'EVT.2026.04.08.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2026-04-08', resolvedEventClass: null, note: 'Quarry hearing cleared' },
  { eventId: 'EVT.2025.XX.XX.02', category: 'health', shape: 'point', tier: 'year', eventDate: '2025-07-01', resolvedEventClass: null, note: 'Sleep-disorder resolution, J4 midpoint, chain terminus' },
  { eventId: 'EVT.2025.XX.XX.01', category: 'spiritual', shape: 'point', tier: 'year', eventDate: '2025-07-01', resolvedEventClass: null, note: 'Shift toward Vishnu/Venkateshwara, J4 midpoint' },
  { eventId: 'EVT.2026.01.XX.01', category: 'other', shape: 'point', tier: 'month', eventDate: '2026-01-15', resolvedEventClass: null, note: 'Psychological focus shift' },
  { eventId: 'EVT.2024.XX.XX.01', category: 'spiritual', shape: 'point', tier: 'year', eventDate: '2024-07-01', resolvedEventClass: null, note: 'Practice intensification, J4 midpoint' },
  { eventId: 'EVT.2025.06.XX.01', category: 'spiritual', shape: 'point', tier: 'month', eventDate: '2025-06-15', resolvedEventClass: null, note: 'Yantra mandala milestone 2/2, J2 (milestone 1 excluded, undated)' },
  { eventId: 'EVT.2025.11.XX.01', category: 'spiritual', shape: 'point', tier: 'month', eventDate: '2025-11-15', resolvedEventClass: null, note: 'Ma Kamlatmika devotion' },
]

if (ROWS.length !== 54) throw new Error(`ROWS length mismatch: expected 54, got ${ROWS.length}`)

const RESOLVED_ROWS = ROWS.filter((r) => r.resolvedEventClass !== null)
if (RESOLVED_ROWS.length !== 3) throw new Error(`expected 3 resolved rows, got ${RESOLVED_ROWS.length}`)

function toleranceDaysForTier(tier: DateConfidenceTier): number {
  if (tier === 'day') return 45
  if (tier === 'week') return 7
  if (tier === 'month') return 75
  return 180 // year, J7
}

function bufferDaysForTier(tier: DateConfidenceTier): number {
  if (tier === 'year') return 200
  if (tier === 'month') return 90
  if (tier === 'week') return 20
  return 60
}

function rangeForRow(r: Row): [Date, Date] {
  const buf = bufferDaysForTier(r.tier) * 86_400_000
  if (r.shape === 'interval') {
    const s = new Date(r.intervalStart! + 'T00:00:00Z').getTime()
    const e = new Date(r.intervalEnd! + 'T00:00:00Z').getTime()
    return [new Date(s - buf), new Date(e + buf)]
  }
  const t = new Date(r.eventDate! + 'T00:00:00Z').getTime()
  return [new Date(t - buf), new Date(t + buf)]
}

function toCurveEvent(r: Row): CurveEvent {
  const dc: DateConfidence = r.tier === 'day' ? 'exact' : r.tier === 'week' ? 'exact' /* J5 */ : r.tier === 'month' ? 'month_known' : 'year_only'
  return {
    eventId: r.eventId,
    shape: r.shape,
    dateConfidence: dc,
    eventDate: r.eventDate ? new Date(r.eventDate + 'T00:00:00Z') : undefined,
    intervalStart: r.intervalStart ? new Date(r.intervalStart + 'T00:00:00Z') : undefined,
    intervalEnd: r.intervalEnd ? new Date(r.intervalEnd + 'T00:00:00Z') : undefined,
  }
}

function toGradingEvent(r: Row): GradingEvent {
  return {
    eventId: r.eventId,
    shape: r.shape === 'interval' ? 'interval' : 'point',
    dateConfidenceTier: r.tier,
    matchToleranceDays: r.shape === 'interval' ? 0 /* J6 */ : toleranceDaysForTier(r.tier),
    eventDate: r.eventDate ? new Date(r.eventDate + 'T00:00:00Z') : undefined,
    intervalStart: r.intervalStart ? new Date(r.intervalStart + 'T00:00:00Z') : undefined,
    intervalEnd: r.intervalEnd ? new Date(r.intervalEnd + 'T00:00:00Z') : undefined,
  }
}

// J-ENSEMBLE-1 (see module header): batch1's own DOMAIN_LORDS table, UNCHANGED, plus two
// key aliases so pratyantar_lord can be called with the SAME eventClass argument the
// ensemble hands every constituent for these exact 3 resolved rows.
const DOMAIN_LORDS: Record<string, Record<string, number>> = {
  wealth: { Jupiter: 1.0, Saturn: 0.8, Venus: 1.0 },
  career: { Saturn: 0.8 },
  health: { Mercury: 1.0 },
  marriage: { Venus: 1.0 },
  general: { Mars: 1.0, Sun: 1.0 },
}
const ENSEMBLE_EVENT_CLASS_SIGNIFICATORS: Record<string, Record<string, number>> = {
  major_gain: DOMAIN_LORDS.wealth, // EVT.2010.XX.XX.01 / EVT.2025.07.XX.01 both category='finance' -> wealth
  marriage: DOMAIN_LORDS.marriage, // EVT.2013.12.11.01 category='family' -> marriage; class name itself matches
}

async function main() {
  const periodsRaw: { level_n: number; lord_graha: string; start_date: string; end_date: string }[] =
    JSON.parse(readFileSync(`${SCRATCH}/vimshottari_periods_full.json`, 'utf8'))
  const periods: DashaPeriod[] = periodsRaw.map((p) => ({ level: p.level_n, lord: p.lord_graha, start: new Date(p.start_date), end: new Date(p.end_date) }))
  console.error(`[batch3] loaded ${periods.length} vimshottari periods (levels 1-3) for ensemble's pratyantar_lord constituent`)

  const chart: ChartContext = { chartId: CHART_ID, ayanamsha: AYANAMSHA, substrate: { periods } }
  const permOpts = { sidecarUrl: SIDECAR_URL, apiKey: API_KEY, stepDays: 5 }
  const allPerm = allPermissionSystemModels(permOpts)
  const BATCH3_PERMISSION_IDS = ['guru_shani_double_transit', 'av_threshold', 'planetary_return']
  const permModels = allPerm.filter((m) => BATCH3_PERMISSION_IDS.includes(m.modelId as string))
  if (permModels.length !== 3) throw new Error(`expected 3 permission models, got ${permModels.length}`)

  const params: MirroredScoringParams = { percentile: 0.9, shuffleCount: 1000, includeSecondaryBattery: true }

  type PerModelEventResult = {
    eventId: string
    category: string
    resolvedEventClass: EventClass | null
    skipped?: string
    meanCrpsReal?: number
    meanCrpsControlShuffled?: number
    skillVsShuffled?: number | null
    hitRate?: { real: boolean; percentile: number }
    dr17?: GradeResult
    error?: string
  }
  const results: Record<string, PerModelEventResult[]> = {
    guru_shani_double_transit: [], av_threshold: [], planetary_return: [], hierarchical_ensemble: [],
  }
  const negativeCrpsFound: { modelId: string; eventId: string; crps: number }[] = []

  // ── Part A: the 3 batch3 PERMISSION contenders, same pattern as batch2 ──
  let idx = 0
  for (const row of ROWS) {
    idx++
    const range = rangeForRow(row)
    const gradingEvent = toGradingEvent(row)
    console.error(`[batch3] event ${idx}/${ROWS.length} ${row.eventId} (category=${row.category}, resolved=${row.resolvedEventClass ?? 'UNRESOLVED'}) range=${range[0].toISOString().slice(0,10)}..${range[1].toISOString().slice(0,10)}`)

    if (row.resolvedEventClass) {
      await Promise.all(permModels.map((m) => m.bind?.(chart, row.resolvedEventClass!, range)))
      for (const model of permModels) {
        try {
          const r = runMirroredScoringHarness({ model, chart, eventClass: row.resolvedEventClass, events: [toCurveEvent(row)], boundsStart: range[0], boundsEnd: range[1], params })
          const realCurve = model.curve(chart, row.resolvedEventClass, range)
          const shuffledCurves: CurvePoint[][] = []
          const totalDays = Math.round((range[1].getTime() - range[0].getTime()) / 86_400_000)
          for (let i = 1; i <= params.shuffleCount; i++) {
            const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * i)
            shuffledCurves.push(shuffledBirthControlCurve(realCurve, shiftDays, range[0], range[1]))
          }
          const baseline = computeControlBaseline(shuffledCurves)
          const dr17 = gradeCurveEvent(realCurve, gradingEvent, baseline, model.modelId as string)
          if (r.primary.meanCrpsReal < 0) negativeCrpsFound.push({ modelId: model.modelId as string, eventId: row.eventId, crps: r.primary.meanCrpsReal })
          if (r.primary.meanCrpsControlShuffled < 0) negativeCrpsFound.push({ modelId: model.modelId as string, eventId: row.eventId + '(control)', crps: r.primary.meanCrpsControlShuffled })
          results[model.modelId as string].push({
            eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass,
            meanCrpsReal: r.primary.meanCrpsReal, meanCrpsControlShuffled: r.primary.meanCrpsControlShuffled,
            skillVsShuffled: r.primary.skillVsShuffled,
            hitRate: { real: r.secondary.real.hitCount > 0, percentile: params.percentile },
            dr17,
          })
        } catch (err) {
          results[model.modelId as string].push({ eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass, error: err instanceof Error ? `${err.name}: ${err.message}` : String(err) })
        }
      }
    } else {
      for (const model of permModels) {
        results[model.modelId as string].push({ eventId: row.eventId, category: row.category, resolvedEventClass: null, skipped: 'unresolved_event_class' })
      }
    }

    writeFileSync(`${SCRATCH}/b1_batch3_results_raw.json`, JSON.stringify(results, null, 2))
    writeFileSync(`${SCRATCH}/b1_batch3_progress.json`, JSON.stringify({ phase: 'permission_contenders', eventsDone: idx, eventsTotal: ROWS.length, negativeCrpsFoundSoFar: negativeCrpsFound.length }, null, 2))
  }
  console.error(`[batch3] Part A done (guru_shani_double_transit/av_threshold/planetary_return). negativeCrpsFound so far=${negativeCrpsFound.length}`)

  // ── Part B: hierarchical_ensemble, built LAST, over all 13 evaluable non-ensemble
  //    contenders, on the 3 resolved-event slice (the only slice where all 13 are
  //    jointly evaluable) ──
  if (PERMISSION_SYSTEM_IDS.length !== 12) throw new Error(`expected 12 PERMISSION_SYSTEM_IDS, got ${PERMISSION_SYSTEM_IDS.length}`)
  const eventClassSignificators = ENSEMBLE_EVENT_CLASS_SIGNIFICATORS
  const pratyantarLord = pratyantarLordModel(eventClassSignificators)
  const allPermForEnsemble = allPermissionSystemModels(permOpts) // fresh instances, own bind() cache per model
  const nonEnsembleContenders = [pratyantarLord, ...allPermForEnsemble]
  if (nonEnsembleContenders.length !== 13) throw new Error(`expected 13 non-ensemble contenders for the ensemble, got ${nonEnsembleContenders.length}`)

  const excludedFromEnsemble: { modelId: string; reason: string }[] = []

  for (const row of RESOLVED_ROWS) {
    const range = rangeForRow(row)
    const gradingEvent = toGradingEvent(row)
    const eventClass = row.resolvedEventClass!
    console.error(`[batch3] ensemble event ${row.eventId} eventClass=${eventClass} range=${range[0].toISOString().slice(0,10)}..${range[1].toISOString().slice(0,10)}`)

    // Bind every constituent for THIS exact (chart, eventClass, range) triple, and verify
    // each one actually produces a curve before including it — an excluded constituent is
    // recorded, never silently dropped.
    const evaluableContenders: typeof nonEnsembleContenders = []
    for (const m of nonEnsembleContenders) {
      try {
        await m.bind?.(chart, eventClass, range)
        const probe = m.curve(chart, eventClass, range) // throws if unbound/not evaluable
        if (probe.length === 0) throw new Error(`${m.modelId}: zero-length curve for eventClass=${eventClass}`)
        evaluableContenders.push(m)
      } catch (err) {
        const reason = err instanceof Error ? `${err.name}: ${err.message}` : String(err)
        if (!excludedFromEnsemble.some((e) => e.modelId === m.modelId as string && e.reason === reason)) {
          excludedFromEnsemble.push({ modelId: m.modelId as string, reason })
        }
      }
    }

    if (evaluableContenders.length === 0) {
      results.hierarchical_ensemble.push({ eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass, error: 'no evaluable constituents for this event' })
      continue
    }

    try {
      const ensemble = hierarchicalEnsembleModel(evaluableContenders)
      const r = runMirroredScoringHarness({ model: ensemble, chart, eventClass, events: [toCurveEvent(row)], boundsStart: range[0], boundsEnd: range[1], params })
      const realCurve = ensemble.curve(chart, eventClass, range)
      const shuffledCurves: CurvePoint[][] = []
      const totalDays = Math.round((range[1].getTime() - range[0].getTime()) / 86_400_000)
      for (let i = 1; i <= params.shuffleCount; i++) {
        const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * i)
        shuffledCurves.push(shuffledBirthControlCurve(realCurve, shiftDays, range[0], range[1]))
      }
      const baseline = computeControlBaseline(shuffledCurves)
      const dr17 = gradeCurveEvent(realCurve, gradingEvent, baseline, 'hierarchical_ensemble')
      if (r.primary.meanCrpsReal < 0) negativeCrpsFound.push({ modelId: 'hierarchical_ensemble', eventId: row.eventId, crps: r.primary.meanCrpsReal })
      if (r.primary.meanCrpsControlShuffled < 0) negativeCrpsFound.push({ modelId: 'hierarchical_ensemble', eventId: row.eventId + '(control)', crps: r.primary.meanCrpsControlShuffled })
      results.hierarchical_ensemble.push({
        eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass,
        meanCrpsReal: r.primary.meanCrpsReal, meanCrpsControlShuffled: r.primary.meanCrpsControlShuffled,
        skillVsShuffled: r.primary.skillVsShuffled,
        hitRate: { real: r.secondary.real.hitCount > 0, percentile: params.percentile },
        dr17,
      })
    } catch (err) {
      results.hierarchical_ensemble.push({ eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass, error: err instanceof Error ? `${err.name}: ${err.message}` : String(err) })
    }

    writeFileSync(`${SCRATCH}/b1_batch3_results_raw.json`, JSON.stringify(results, null, 2))
  }
  // The other 51 unresolved events: ensemble honestly SKIPPED (not fallback-scored), same
  // discipline as every PERMISSION contender in this run.
  for (const row of ROWS) {
    if (row.resolvedEventClass) continue
    results.hierarchical_ensemble.push({ eventId: row.eventId, category: row.category, resolvedEventClass: null, skipped: 'unresolved_event_class' })
  }

  writeFileSync(`${SCRATCH}/b1_batch3_ensemble_exclusions.json`, JSON.stringify(excludedFromEnsemble, null, 2))
  writeFileSync(`${SCRATCH}/b1_batch3_results_raw.json`, JSON.stringify(results, null, 2))
  writeFileSync(`${SCRATCH}/b1_batch3_progress.json`, JSON.stringify({ phase: 'done', eventsTotal: ROWS.length, negativeCrpsFoundSoFar: negativeCrpsFound.length, ensembleExclusions: excludedFromEnsemble.length }, null, 2))

  console.error(`[batch3] DONE. negativeCrpsFound=${negativeCrpsFound.length}, ensembleExclusions=${excludedFromEnsemble.length}`)
  writeFileSync(`${SCRATCH}/b1_batch3_negative_crps_check.json`, JSON.stringify(negativeCrpsFound, null, 2))
  console.error('[batch3] wrote', `${SCRATCH}/b1_batch3_results_raw.json`)
}

main().catch((err) => {
  console.error('[batch3] FATAL:', err)
  process.exit(1)
})
