#!/usr/bin/env -S npx tsx
/**
 * b1_batch1_driver.ts — D-4b B-1 chunked re-run, BATCH 1/3 (key="batch1").
 *
 * Scores ONLY the 5 contenders assigned to batch1 by
 * B1_RUN_MANIFEST_v1_0.json's `batching.batches[0]`: pratyantar_lord,
 * vimshottari, yogini, ashtottari, chara_karaka. Against the manifest's
 * cited D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §1 event set (56 events;
 * 54 scored per §0's own recommendation, excluding the birth
 * structural-anchor and the congenital-onset stammering entry).
 *
 * Imports the REAL, already-merged harness modules (model_interface.ts,
 * roster.ts/permission_model.ts, harness.ts, dr17_grading.ts,
 * event_class_resolution.ts) — no reimplementation of any scoring math.
 *
 * Substrate:
 *  - Vimshottari dasha periods (levels 1-3, full life-arc 1984-2026-09),
 *    live-fetched via ganita_dasha_periods_get this session, paginated to
 *    exhaustion (228/228 rows, zero gaps, verified), written to
 *    vimshottari_periods_full.json.
 *  - gochara_resonance_map's live populated event_class set for chart
 *    482012f1, live-queried this session (career_advancement=22,
 *    major_gain=35, marriage=23) -- matches event_class_resolution.ts's
 *    own documented 2026-07-22 live-verification figures exactly.
 *  - Event-class resolution for this batch's 3 domain-resolvable events
 *    (EVT.2010.XX.XX.01, EVT.2013.12.11.01 -- both independently
 *    live-verified this session via a query STRICTLY scoped to
 *    event_date < 2020-01-01, i.e. compliant with the "never read/query
 *    events on/after 2020-01-01" ground rule -- and EVT.2025.07.XX.01,
 *    whose domain was NOT independently re-queried this session because
 *    doing so would read a post-2020-01-01 life_events row; its
 *    resolution instead rests on the ALREADY-MERGED, already-tested
 *    event_class_resolution.ts module docstring's own explicit,
 *    live-verified (2026-07-22, a prior session) statement that this
 *    chart has "ONLY 2 category='finance' rows" and BOTH resolve to
 *    'major_gain' -- combined with this session's own live confirmation
 *    that EVT.2010.XX.XX.01 is one of the two (leaving EVT.2025.07.XX.01
 *    as the other, by elimination, per the packet's own 56-event roster,
 *    without this session itself reading that row).
 *
 * All other 51 (of 54 scored) events are UNRESOLVED against
 * gochara_resonance_map's 3-class scope (career_advancement / major_gain
 * / marriage) -- for those, per F-1's own established, honest design, the
 * 4 PERMISSION contenders (vimshottari/yogini/ashtottari/chara_karaka) are
 * SKIPPED (not silently scored against a degraded fallback), while
 * pratyantar_lord (which never reads gochara_resonance_map) is scored
 * against every one of the 54.
 *
 * Judgment calls made explicit here (house style, per curve_controls.ts /
 * proper_scoring.ts / dr17_grading.ts's own documented-judgment-call
 * discipline):
 *
 * J1. Two packet rows bundle a "chain" into ONE row rather than
 *     per-milestone rows (EVT.1995.XX.XX.01: onset~1995/active/resolving/
 *     resolved~2021; EVT.2007.XX.XX.03: onset 2007-06/resolved 2025).
 *     Both scored as a single INTERVAL spanning onset-to-resolution
 *     (DR-13 §2 overlap rule), not decomposed further -- the packet's own
 *     text does not give each phase an independently datable boundary
 *     precise enough to split further than that.
 * J2. EVT.2025.06.XX.01 (Yantra mandala chain): milestone 1 has no date
 *     ("undated") and is explicitly flagged "not independently
 *     scoreable" by the packet itself -- excluded; only milestone 2
 *     (~2025-06-15, month confidence) is scored, as a point event.
 * J3. Two open-ended intervals (EVT.2002.XX.XX.02 Shani Puja onset ~2002;
 *     EVT.2010.XX.XX.02 Ugratara devotion onset 2010) have no stated end
 *     bound. Capped at this run's own reference date (2026-07-22, this
 *     session's date) as "still ongoing as of now" -- mirrors the
 *     treatment EVT.CURRENT.01 itself receives in LEL's own frontmatter
 *     (a status-as-of-log-version marker), applied here to the two
 *     open-ended interval events that DO remain in the scored 54 (unlike
 *     EVT.CURRENT.01 itself, which the packet excludes from the 56
 *     entirely).
 * J4. Every month/year-approx point event's within-period date is set to
 *     the PERIOD MIDPOINT (e.g. "2001-03" -> 2001-03-15; "2004" year-approx
 *     -> 2004-07-01) -- the packet's own tolerance bands (±75d month,
 *     "secondary battery" year) are wide enough that the exact
 *     within-period day choice does not change which grid cells fall
 *     inside the matching window at either tier; documented rather than
 *     defaulted silently.
 * J5. `week` date-confidence (EVT.2022.XX.XX.02, the sole week-tier
 *     event in this batch's scored 54) is mapped to CurveEvent's legacy
 *     `dateConfidence` field as 'exact' for the SECONDARY (legacy
 *     hit-rate) metric only, since shape_scoring.ts's DateConfidence enum
 *     has no 'week' tier (pre-dates the native's week-tier date
 *     tightening) -- this makes the LEGACY hit-rate tolerance too wide
 *     (±45d instead of the packet's proposed ±7d) for this one event;
 *     immaterial to this run's PRIMARY metrics (CRPS/skill, DR-17 grade),
 *     which both use the packet's real ±7d value directly via
 *     GradingEvent.matchToleranceDays / dr17_grading's own 'week' tier.
 * J6. Interval-shaped events' `matchToleranceDays` field is unused by
 *     dr17_grading.ts's own interval-matching path (pure bounds overlap)
 *     -- set to 0 for those rows, never read.
 * J7. Year-tier point events' `matchToleranceDays` (needed by
 *     dr17_grading's point-matching regardless of DR-13(d)'s "year_only
 *     not in the primary battery" framing, since DR-17 grading is a
 *     DIFFERENT, non-percentile mechanism from the legacy hit-rate
 *     battery) is set to 180 days, cross-referencing the packet's own
 *     year-tier TIE-BAND width (§4) as the best available anchor -- no
 *     DR-13(d) year point-tolerance figure exists anywhere in ratified
 *     doctrine (packet §3 says year-only is secondary-battery-only for
 *     the LEGACY metric, silent on a DR-17 point-tolerance value).
 */
import { writeFileSync, readFileSync } from 'node:fs'
import type { ChartContext, EventClass } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { pratyantarLordModel } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { allPermissionSystemModels } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/permission_model'
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
const RUN_REF_DATE = '2026-07-22' // this session's own reference "now" (J3)

const DOMAIN_LORDS: Record<string, Record<string, number>> = {
  wealth: { Jupiter: 1.0, Saturn: 0.8, Venus: 1.0 },
  career: { Saturn: 0.8 },
  health: { Mercury: 1.0 },
  marriage: { Venus: 1.0 },
  general: { Mars: 1.0, Sun: 1.0 },
}
const CATEGORY_TO_DOMAIN: Record<string, string> = {
  finance: 'wealth', loss: 'wealth', career: 'career', health: 'health',
  psychological: 'health', relationship: 'marriage', family: 'marriage',
  education: 'general', creative: 'general', spiritual: 'general',
  travel: 'general', other: 'general', 'residential+travel': 'general',
}
function significatorsForCategory(category: string): Record<string, number> {
  return DOMAIN_LORDS[CATEGORY_TO_DOMAIN[category] ?? 'general'] ?? DOMAIN_LORDS.general
}

type Row = {
  eventId: string
  category: string
  shape: EventShape // 'point' | 'interval' (no chain rows remain -- J1/J2 flatten them)
  tier: DateConfidenceTier // 'day' | 'week' | 'month' | 'year'
  eventDate?: string
  intervalStart?: string
  intervalEnd?: string
  resolvedEventClass: EventClass | null // populated only for the 3 domain-resolved events
  note: string
}

// D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §1, git blob 9b6713db8c2551a937ff2070e498da1f12526966,
// read verbatim this session. 54 of 56 rows (birth EVT.1984.02.05.01 and congenital-onset
// EVT.1995.XX.XX.02 excluded per §0's own recommendation).
const ROWS: Row[] = [
  // Era 1-2
  { eventId: 'EVT.1995.XX.XX.01', category: 'health', shape: 'interval', tier: 'year', intervalStart: '1995-01-01', intervalEnd: '2021-12-31', resolvedEventClass: null, note: 'chain/interval hybrid, J1: scored as full onset-to-resolution interval' },
  { eventId: 'EVT.1998.02.16.01', category: 'relationship', shape: 'point', tier: 'day', eventDate: '1998-02-16', resolvedEventClass: null, note: 'R#1 start' },
  { eventId: 'EVT.2000.XX.XX.01', category: 'education', shape: 'interval', tier: 'month', intervalStart: '2000-06-01', intervalEnd: '2000-12-31', resolvedEventClass: null, note: '' },
  // Era 3-4
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
  // Era 5
  { eventId: 'EVT.2010.XX.XX.01', category: 'finance', shape: 'interval', tier: 'month', intervalStart: '2010-07-01', intervalEnd: '2011-03-31', resolvedEventClass: 'major_gain', note: 'Windfall, NAMED SPECIMEN, domain live-verified this session (event_date<2020)' },
  { eventId: 'EVT.2010.12.XX.01', category: 'travel', shape: 'point', tier: 'month', eventDate: '2010-12-15', resolvedEventClass: null, note: 'Thailand trip' },
  { eventId: 'EVT.2011.01.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2011-01-15', resolvedEventClass: null, note: 'XIMB admission, chain 1/2' },
  { eventId: 'EVT.2011.06.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2011-06-15', resolvedEventClass: null, note: 'XIMB enrolled, chain 2/2' },
  { eventId: 'EVT.2012.09.XX.01', category: 'creative', shape: 'point', tier: 'month', eventDate: '2012-09-15', resolvedEventClass: null, note: 'Modeling' },
  { eventId: 'EVT.2012.XX.XX.02', category: 'education', shape: 'point', tier: 'year', eventDate: '2012-07-01', resolvedEventClass: null, note: 'IRC presidency, J4 midpoint' },
  { eventId: 'EVT.2012.10.XX.01', category: 'relationship', shape: 'point', tier: 'month', eventDate: '2012-10-15', resolvedEventClass: null, note: 'R#3 start, chain 1/2' },
  { eventId: 'EVT.2013.03.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2013-03-15', resolvedEventClass: null, note: 'MBA graduation' },
  { eventId: 'EVT.2013.05.XX.01', category: 'career', shape: 'point', tier: 'month', eventDate: '2013-05-15', resolvedEventClass: null, note: 'Mahindra Retail joined' },
  { eventId: 'EVT.2013.XX.XX.01', category: 'family', shape: 'interval', tier: 'year', intervalStart: '2013-01-01', intervalEnd: '2018-11-28', resolvedEventClass: null, note: "Father's illness onset->terminus, chain 1/2" },
  { eventId: 'EVT.2013.12.11.01', category: 'family', shape: 'point', tier: 'day', eventDate: '2013-12-11', resolvedEventClass: 'marriage', note: 'Marriage, NAMED SPECIMEN, domain live-verified this session (event_date<2020)' },
  { eventId: 'EVT.1993.XX.XX.01', category: 'creative', shape: 'point', tier: 'year', eventDate: '1993-07-01', resolvedEventClass: null, note: 'Painting awards (M5A), J4 midpoint' },
  // Era 6-7
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
  // Era 8
  { eventId: 'EVT.2023.05.XX.01', category: 'residential+travel', shape: 'point', tier: 'month', eventDate: '2023-05-15', resolvedEventClass: null, note: 'US return, chain 2/2' },
  { eventId: 'EVT.2023.06.XX.01', category: 'education', shape: 'point', tier: 'month', eventDate: '2023-06-15', resolvedEventClass: null, note: 'Tepper completed, chain terminus' },
  { eventId: 'EVT.2023.07.XX.01', category: 'career', shape: 'point', tier: 'month', eventDate: '2023-07-15', resolvedEventClass: null, note: 'Marsys founded' },
  { eventId: 'EVT.2024.02.16.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2024-02-16', resolvedEventClass: null, note: 'Kotadwara sand mine launch' },
  { eventId: 'EVT.2025.05.XX.01', category: 'loss', shape: 'point', tier: 'month', eventDate: '2025-05-15', resolvedEventClass: null, note: 'Financial deception/scam' },
  { eventId: 'EVT.2025.07.XX.01', category: 'finance', shape: 'point', tier: 'month', eventDate: '2025-07-15', resolvedEventClass: 'major_gain', note: 'First Marsys contract; domain by elimination -- see module docstring, NOT independently re-queried (>=2020-01-01)' },
  { eventId: 'EVT.2026.03.20.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2026-03-20', resolvedEventClass: null, note: 'Marsys Technology project closed' },
  { eventId: 'EVT.2026.04.08.01', category: 'career', shape: 'point', tier: 'day', eventDate: '2026-04-08', resolvedEventClass: null, note: 'Quarry hearing cleared' },
  { eventId: 'EVT.2025.XX.XX.02', category: 'health', shape: 'point', tier: 'year', eventDate: '2025-07-01', resolvedEventClass: null, note: 'Sleep-disorder resolution, J4 midpoint, chain terminus' },
  { eventId: 'EVT.2025.XX.XX.01', category: 'spiritual', shape: 'point', tier: 'year', eventDate: '2025-07-01', resolvedEventClass: null, note: 'Shift toward Vishnu/Venkateshwara, J4 midpoint' },
  // Remaining 2025-2026
  { eventId: 'EVT.2026.01.XX.01', category: 'other', shape: 'point', tier: 'month', eventDate: '2026-01-15', resolvedEventClass: null, note: 'Psychological focus shift' },
  { eventId: 'EVT.2024.XX.XX.01', category: 'spiritual', shape: 'point', tier: 'year', eventDate: '2024-07-01', resolvedEventClass: null, note: 'Practice intensification, J4 midpoint' },
  { eventId: 'EVT.2025.06.XX.01', category: 'spiritual', shape: 'point', tier: 'month', eventDate: '2025-06-15', resolvedEventClass: null, note: 'Yantra mandala milestone 2/2, J2 (milestone 1 excluded, undated)' },
  { eventId: 'EVT.2025.11.XX.01', category: 'spiritual', shape: 'point', tier: 'month', eventDate: '2025-11-15', resolvedEventClass: null, note: 'Ma Kamlatmika devotion' },
]

function toleranceDaysForTier(tier: DateConfidenceTier): number {
  if (tier === 'day') return 45
  if (tier === 'week') return 7
  if (tier === 'month') return 75
  return 180 // year, J7
}

function bufferDaysForTier(tier: DateConfidenceTier): number {
  if (tier === 'year') return 200 // covers the ±180d tie-band + margin
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

async function main() {
  const periodsRaw: { level_n: number; lord_graha: string; start_date: string; end_date: string }[] =
    JSON.parse(readFileSync(`${SCRATCH}/vimshottari_periods_full.json`, 'utf8'))
  const periods: DashaPeriod[] = periodsRaw.map((p) => ({ level: p.level_n, lord: p.lord_graha, start: new Date(p.start_date), end: new Date(p.end_date) }))
  console.error(`[batch1] loaded ${periods.length} vimshottari periods (levels 1-3), span ${periods[0].start.toISOString().slice(0,10)}..${periods[periods.length-1].end.toISOString().slice(0,10)}`)

  const eventClassSignificators: Record<EventClass, Record<string, number>> = {}
  for (const r of ROWS) eventClassSignificators[r.category] = significatorsForCategory(r.category)

  const chart: ChartContext = { chartId: CHART_ID, ayanamsha: AYANAMSHA, substrate: { periods } }
  const pratyantarLord = pratyantarLordModel(eventClassSignificators)
  const permOpts = { sidecarUrl: SIDECAR_URL, apiKey: API_KEY, stepDays: 5 }
  const allPerm = allPermissionSystemModels(permOpts)
  const BATCH1_PERMISSION_IDS = ['vimshottari', 'yogini', 'ashtottari', 'chara_karaka']
  const permModels = allPerm.filter((m) => BATCH1_PERMISSION_IDS.includes(m.modelId as string))
  if (permModels.length !== 4) throw new Error(`expected 4 permission models, got ${permModels.length}`)

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
    pratyantar_lord: [], vimshottari: [], yogini: [], ashtottari: [], chara_karaka: [],
  }
  let negativeCrpsFound: { modelId: string; eventId: string; crps: number }[] = []

  let idx = 0
  for (const row of ROWS) {
    idx++
    const range = rangeForRow(row)
    const curveEvent = toCurveEvent(row)
    const gradingEvent = toGradingEvent(row)
    console.error(`[batch1] event ${idx}/${ROWS.length} ${row.eventId} (category=${row.category}, resolved=${row.resolvedEventClass ?? 'UNRESOLVED'}) range=${range[0].toISOString().slice(0,10)}..${range[1].toISOString().slice(0,10)}`)

    // ── pratyantar_lord: scored for every row (no gochara_resonance_map dependency) ──
    try {
      const r = runMirroredScoringHarness({ model: pratyantarLord, chart, eventClass: row.category, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
      const realCurve = pratyantarLord.curve(chart, row.category, range)
      const shuffledCurves: CurvePoint[][] = []
      const totalDays = Math.round((range[1].getTime() - range[0].getTime()) / 86_400_000)
      for (let i = 1; i <= params.shuffleCount; i++) {
        const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * i)
        shuffledCurves.push(shuffledBirthControlCurve(realCurve, shiftDays, range[0], range[1]))
      }
      const baseline = computeControlBaseline(shuffledCurves)
      const dr17 = gradeCurveEvent(realCurve, gradingEvent, baseline, 'pratyantar_lord')
      if (r.primary.meanCrpsReal < 0) negativeCrpsFound.push({ modelId: 'pratyantar_lord', eventId: row.eventId, crps: r.primary.meanCrpsReal })
      if (r.primary.meanCrpsControlShuffled < 0) negativeCrpsFound.push({ modelId: 'pratyantar_lord', eventId: row.eventId + '(control)', crps: r.primary.meanCrpsControlShuffled })
      results.pratyantar_lord.push({
        eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass,
        meanCrpsReal: r.primary.meanCrpsReal, meanCrpsControlShuffled: r.primary.meanCrpsControlShuffled,
        skillVsShuffled: r.primary.skillVsShuffled,
        hitRate: { real: r.secondary.real.hitCount > 0, percentile: params.percentile },
        dr17,
      })
    } catch (err) {
      results.pratyantar_lord.push({ eventId: row.eventId, category: row.category, resolvedEventClass: row.resolvedEventClass, error: err instanceof Error ? `${err.name}: ${err.message}` : String(err) })
    }

    // ── 4 PERMISSION contenders: only for domain-resolved events ──
    if (row.resolvedEventClass) {
      await Promise.all(permModels.map((m) => m.bind?.(chart, row.resolvedEventClass!, range)))
      for (const model of permModels) {
        try {
          const r = runMirroredScoringHarness({ model, chart, eventClass: row.resolvedEventClass, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
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

    writeFileSync(`${SCRATCH}/b1_batch1_results_raw.json`, JSON.stringify(results, null, 2))
    writeFileSync(`${SCRATCH}/b1_batch1_progress.json`, JSON.stringify({ eventsDone: idx, eventsTotal: ROWS.length, negativeCrpsFoundSoFar: negativeCrpsFound.length }, null, 2))
  }

  console.error(`[batch1] DONE. negativeCrpsFound=${negativeCrpsFound.length}`)
  writeFileSync(`${SCRATCH}/b1_batch1_negative_crps_check.json`, JSON.stringify(negativeCrpsFound, null, 2))
  console.error('[batch1] wrote', `${SCRATCH}/b1_batch1_results_raw.json`)
}

main().catch((err) => {
  console.error('[batch1] FATAL:', err)
  process.exit(1)
})
