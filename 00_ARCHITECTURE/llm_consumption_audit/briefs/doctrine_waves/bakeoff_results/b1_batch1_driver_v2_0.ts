#!/usr/bin/env -S npx tsx
/**
 * b1_batch1_driver_v2.ts — D-4b B-1 CLEAN re-run (attempt #3), BATCH 1/3.
 *
 * Contenders: pratyantar_lord, vimshottari, yogini, ashtottari, chara_karaka.
 * Scored against the TRAIN split ONLY (event_date < 2020-01-01), built from
 * D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §1 (git blob 9b6713db, verified)
 * via filterToTrainScope() (sealed_split_guard.ts) -- never a hand-written
 * date filter. Structural sealed-split enforcement: assertNoSealedSplitEvents
 * fires both inside harness.ts's runMirroredScoringHarness (CR-123) AND
 * explicitly here, right after building the scored event list and before
 * any artifact write (defense-in-depth per the native's instruction).
 *
 * Event source-of-truth for this driver: every date below is either (a) the
 * packet's own §1 "Date (tightened)" text verbatim, or (b) life_events'
 * stored event_date/interval_start/interval_end/domain, fetched LIVE this
 * session via a query that NEVER touched a row with event_date >=
 * 2020-01-01 (the query's own WHERE clause structurally excluded them --
 * see session transcript). Where the packet flags a "native tightening"
 * correction not yet reflected in the DB (EVT.2000.XX.XX.01,
 * EVT.2009.06.XX.01, EVT.2013.12.11.01, EVT.2018.11.28.01,
 * EVT.2015.XX.XX.01, EVT.2022.10.XX.01), the packet's tightened value wins.
 * TEST-scope rows (event_date >= 2020-01-01) are encoded ONLY from the
 * packet's own approximate text (month/year granularity) -- their exact day
 * is scoring-irrelevant since filterToTrainScope() drops them before any
 * model ever sees them; life_events was never queried for these.
 *
 * Two rows are genuinely multi-date "chain" events per the packet's own
 * Shape column (EVT.1995.XX.XX.01 headaches arc: active 1995-2010,
 * "resolved ~2021"; EVT.2007.XX.XX.03 sleep-disorder arc: onset 2007-06,
 * resolved ~2025 via EVT.2025.XX.XX.02) -- both are encoded with their
 * TRUE full span (including the post-2020 resolution date) so
 * filterToTrainScope() correctly and structurally excludes them, rather
 * than being hand-excluded by this driver.
 *
 * Two rows carry the packet's own §0-documented scoring-ambiguity flags
 * (EVT.1984.02.05.01 birth -- structural_anchor_not_scored_for_bakeoff;
 * EVT.1995.XX.XX.02 stammering -- congenital_onset_not_independently_
 * scoreable) -- both recommended EXCLUDED from the actual scoring pass per
 * §0's own text. The congenital row's true open-ended span (present, i.e.
 * post-2020) means filterToTrainScope() excludes it structurally anyway;
 * the birth row is TRAIN-scope by date and is separately, explicitly
 * flagged scoringExcluded=true here (disclosed, not silently dropped --
 * still reported in the run header for corpus completeness per §0).
 *
 * DOCUMENTED JUDGMENT CALL: EVT.2002.XX.XX.02 (Shani Puja) and
 * EVT.2010.XX.XX.02 (Ugratara devotion) -- the packet's §1 Shape column
 * reads "interval, open" for both, but life_events' own `shape` column
 * (the field DR-13 methodology actually assigns) stores BOTH as `point`
 * (exact date_confidence). An open-ended, still-ongoing devotional
 * practice has no independently-dateable end event; scoring it as an
 * interval would require fabricating an end-date (B.10 forbids this).
 * This driver follows life_events' own point-shape encoding (its onset is
 * the dateable, scoreable manifestation) rather than inventing an interval
 * bound. Disclosed here, not silently assumed.
 *
 * PERMISSION-system (vimshottari/yogini/ashtottari/chara_karaka) event_class
 * resolution: only 3 gochara_resonance_map classes are populated for this
 * chart (career_advancement=22, major_gain=35, marriage=23 rows, live
 * queried this session) and event_class_resolution.ts's evidence-cited
 * DOMAIN_TO_EVENT_CLASS table resolves exactly 2 of this batch's 31
 * TRAIN-scored events to a populated class: EVT.2013.12.11.01
 * (family/marriage -> marriage) and EVT.2010.XX.XX.01
 * (finance/family_windfall -> major_gain). Every other TRAIN event is
 * UNRESOLVED for the 4 PERMISSION contenders in this batch and is SKIPPED
 * for them, explicitly and visibly (never silently scored against a
 * degraded fallback) -- pratyantar_lord alone is scored on all 31, since it
 * does not read gochara_resonance_map at all.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import type { ChartContext, EventClass, TemporalCurveModel } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { pratyantarLordModel } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import { permissionSystemModel, type PermissionModelOptions } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/permission_model'
import { runMirroredScoringHarness, type MirroredScoringParams } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/harness'
import { assertRosterBindable, RosterBindFailureError } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/roster_bind'
import { assertNoSealedSplitEvents, filterToTrainScope, TEST_SPLIT_BOUNDARY } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/sealed_split_guard'
import type { CurveEvent, DateConfidence, EventShape } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/shape_scoring'
import { shuffledBirthControlCurve } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/curve_controls'
import {
  gradeCurveEvent,
  computeControlBaseline,
  tierForDateConfidence,
  type GradingEvent,
  type GradeResult,
} from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/dr17_grading'
import { resolveEventClass, type RawEventForResolution } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/event_class_resolution'
import type { DashaPeriod, CurvePoint } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/curve'
import { writeBatchArtifact, hashManifestFile } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/b1_batch_artifact_io'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const SIDECAR_URL = process.env.PYTHON_SIDECAR_URL || ''
const API_KEY = process.env.PYTHON_SIDECAR_API_KEY || ''
const SCRATCH = '/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/cb8619fb-b398-41cc-a7e7-6cc6c9eafb53/scratchpad'
const REPO = '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2'
const MANIFEST_PATH = `${REPO}/00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/bakeoff_results/B1_RUN_MANIFEST_v2_0.json`
const ARTIFACTS_DIR = `${REPO}/00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/bakeoff_results/b1_batches_v2`
const PACKET_BLOB_SHA_EXPECTED = '9b6713db8c2551a937ff2070e498da1f12526966'

// ── DOMAIN_LORDS / significatorsForCategory, carried verbatim from mechanisms.ts (T-0, live-verified) ──
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

type RawEvent = {
  eventId: string
  category: string
  domain: string
  shape: EventShape
  dateConfidence: DateConfidence
  eventDate?: string
  intervalStart?: string
  intervalEnd?: string
  scoringExcluded?: true
  exclusionReason?: string
  provenance: string
}

// ── Full 56-row packet §1 event set. See module docstring for provenance rules. ──
const RAW_EVENTS: RawEvent[] = [
  { eventId: 'EVT.1984.02.05.01', category: 'other', domain: 'other/birth', shape: 'point', dateConfidence: 'exact', eventDate: '1984-02-05', scoringExcluded: true, exclusionReason: 'structural_anchor_not_scored_for_bakeoff (packet §0)', provenance: 'DB event_date (5d039007)' },
  { eventId: 'EVT.1995.XX.XX.01', category: 'health', domain: 'health/chronic_onset', shape: 'interval', dateConfidence: 'year_only', intervalStart: '1994-12-31', intervalEnd: '2021-06-30', provenance: 'DB interval_start (64c475da) + packet text "resolved ~2021" (approx placeholder, not precision-critical -- excluded by TEST-touch regardless of exact day)' },
  { eventId: 'EVT.1998.02.16.01', category: 'relationship', domain: 'relationship/romantic_long_term_started', shape: 'point', dateConfidence: 'exact', eventDate: '1998-02-16', provenance: 'packet §1 (matches DB 3a37fa76 IST date)' },
  { eventId: 'EVT.2000.XX.XX.01', category: 'education', domain: 'education/advanced_course_partial', shape: 'interval', dateConfidence: 'month_known', intervalStart: '2000-06-01', intervalEnd: '2000-12-31', provenance: 'packet §1 native tightening #4 (supersedes DB 39f8395f pre-tightening point value)' },
  { eventId: 'EVT.1995.XX.XX.02', category: 'psychological', domain: 'psychological/speech_pattern_arc', shape: 'interval', dateConfidence: 'exact', intervalStart: '1984-02-05', intervalEnd: '2026-07-22', scoringExcluded: true, exclusionReason: 'congenital_onset_not_independently_scoreable (packet §0)', provenance: 'DB (3e96c6da-corr-congenital) open-ended present; placeholder end triggers correct TEST-touch exclusion' },
  { eventId: 'EVT.2001.03.XX.01', category: 'education', domain: 'education/entrance_exam_preparation', shape: 'point', dateConfidence: 'month_known', eventDate: '2001-03-14', provenance: 'DB event_date (359944e3)' },
  { eventId: 'EVT.2003.06.XX.01', category: 'education', domain: 'education/entrance_exam_preparation_ended', shape: 'point', dateConfidence: 'month_known', eventDate: '2003-06-14', provenance: 'DB event_date (4a1b1dc0)' },
  { eventId: 'EVT.2004.01.XX.01', category: 'relationship', domain: 'relationship/romantic_concurrent', shape: 'point', dateConfidence: 'month_known', eventDate: '2004-01-14', provenance: 'DB event_date (45ba996d)' },
  { eventId: 'EVT.2004.XX.XX.02', category: 'education', domain: 'education/opportunity_declined', shape: 'point', dateConfidence: 'year_only', eventDate: '2004-05-31', provenance: 'DB event_date (cd68bc5c)' },
  { eventId: 'EVT.2007.06.XX.01', category: 'health', domain: 'health/surgery_minor', shape: 'point', dateConfidence: 'month_known', eventDate: '2007-06-14', provenance: 'DB event_date (4e09e1e1)' },
  { eventId: 'EVT.2007.XX.XX.03', category: 'health', domain: 'health/chronic_onset', shape: 'interval', dateConfidence: 'month_known', intervalStart: '2007-06-13', intervalEnd: '2025-06-01', provenance: 'DB interval_start (8573c0ca-corr-day-lock) + packet text "resolved EVT.2025.XX.XX.02" (approx placeholder -- excluded by TEST-touch regardless of exact day)' },
  { eventId: 'EVT.2007.06.XX.02', category: 'education', domain: 'education/engineering_completed', shape: 'point', dateConfidence: 'month_known', eventDate: '2007-06-14', provenance: 'DB event_date (71af4f61)' },
  { eventId: 'EVT.2007.06.10.01', category: 'career', domain: 'career/first_job_joined', shape: 'point', dateConfidence: 'exact', eventDate: '2007-06-10', provenance: 'packet §1 (matches DB fd04fecc IST date)' },
  { eventId: 'EVT.2008.06.09.01', category: 'career', domain: 'career/first_job_exited', shape: 'point', dateConfidence: 'exact', eventDate: '2008-06-09', provenance: 'packet §1 (matches DB aed78f94 IST date)' },
  { eventId: 'EVT.2009.06.XX.01', category: 'loss', domain: 'loss/grandparent_passing', shape: 'point', dateConfidence: 'month_known', eventDate: '2009-06-30', provenance: 'packet §1 native tightening #8 best_estimate (supersedes DB 1dc207bc pre-tightening value)' },
  { eventId: 'EVT.2002.XX.XX.01', category: 'psychological', domain: 'psychological/chronic_episode', shape: 'interval', dateConfidence: 'year_only', intervalStart: '2000-12-31', intervalEnd: '2005-12-30', provenance: 'DB interval bounds (123eee97)' },
  { eventId: 'EVT.2002.XX.XX.02', category: 'spiritual', domain: 'spiritual/sadhana_initiation', shape: 'point', dateConfidence: 'exact', eventDate: '2002-06-30', provenance: 'DB shape=point, event_date (62f0460d) -- documented judgment call, see module docstring' },
  { eventId: 'EVT.1998.XX.XX.02', category: 'spiritual', domain: 'spiritual/transmission', shape: 'point', dateConfidence: 'year_only', eventDate: '1998-06-30', provenance: 'DB event_date (d5db1b9a); packet explicitly retains LEL recorded 1998 value, quarantined 2001 correction NOT applied' },
  { eventId: 'EVT.2010.XX.XX.01', category: 'finance', domain: 'finance/family_windfall', shape: 'interval', dateConfidence: 'month_known', intervalStart: '2010-07-01', intervalEnd: '2011-03-01', provenance: 'packet §1 native-tightened bounds (DB bd7f5711 interval_start/end agree closely) -- NAMED SPECIMEN' },
  { eventId: 'EVT.2010.12.XX.01', category: 'travel', domain: 'travel/first_foreign_trip', shape: 'point', dateConfidence: 'month_known', eventDate: '2010-12-14', provenance: 'DB event_date (a1ef10c2)' },
  { eventId: 'EVT.2011.01.XX.01', category: 'education', domain: 'education/mba_admission', shape: 'point', dateConfidence: 'month_known', eventDate: '2011-01-14', provenance: 'DB event_date (4e96f4b9)' },
  { eventId: 'EVT.2011.06.XX.01', category: 'education', domain: 'education/mba_enrolled', shape: 'point', dateConfidence: 'month_known', eventDate: '2011-06-14', provenance: 'DB event_date (95138517)' },
  { eventId: 'EVT.2012.09.XX.01', category: 'creative', domain: 'creative/modeling', shape: 'point', dateConfidence: 'month_known', eventDate: '2012-09-14', provenance: 'DB event_date (852d1420)' },
  { eventId: 'EVT.2012.XX.XX.02', category: 'education', domain: 'education/leadership_role', shape: 'point', dateConfidence: 'year_only', eventDate: '2012-08-31', provenance: 'DB event_date (cf0c918d)' },
  { eventId: 'EVT.2012.10.XX.01', category: 'relationship', domain: 'relationship/romantic_concurrent', shape: 'point', dateConfidence: 'month_known', eventDate: '2012-10-14', provenance: 'DB event_date (aa591eb5)' },
  { eventId: 'EVT.2013.03.XX.01', category: 'education', domain: 'education/mba_graduation', shape: 'point', dateConfidence: 'month_known', eventDate: '2013-03-14', provenance: 'DB event_date (c143ce2a)' },
  { eventId: 'EVT.2013.05.XX.01', category: 'career', domain: 'career/corporate_job_joined', shape: 'point', dateConfidence: 'month_known', eventDate: '2013-05-14', provenance: 'DB event_date (6f5ee9cb)' },
  { eventId: 'EVT.2013.XX.XX.01', category: 'family', domain: 'family/parent_illness_onset', shape: 'point', dateConfidence: 'year_only', eventDate: '2013-06-30', provenance: 'DB event_date (72fad18c); terminus EVT.2018.11.28.01 scored as its own separate row, both TRAIN-scope' },
  { eventId: 'EVT.2013.12.11.01', category: 'family', domain: 'family/marriage', shape: 'point', dateConfidence: 'exact', eventDate: '2013-12-11', provenance: 'packet §1 (matches DB b72f40f7 IST date) -- NAMED SPECIMEN' },
  { eventId: 'EVT.1993.XX.XX.01', category: 'creative', domain: 'creative/award', shape: 'point', dateConfidence: 'year_only', eventDate: '1993-06-30', provenance: 'DB event_date (0d03e02a)' },
  { eventId: 'EVT.2016.XX.XX.01', category: 'career', domain: 'career/employer_instability', shape: 'point', dateConfidence: 'year_only', eventDate: '2016-06-30', provenance: 'DB event_date (b5ea6a4d)' },
  { eventId: 'EVT.2017.03.XX.01', category: 'career', domain: 'career/employer_switch', shape: 'point', dateConfidence: 'month_known', eventDate: '2017-03-14', provenance: 'DB event_date (e3b2f1d5)' },
  { eventId: 'EVT.2018.11.28.01', category: 'loss', domain: 'loss/parent_passing', shape: 'point', dateConfidence: 'exact', eventDate: '2018-11-28', provenance: 'packet §1 (matches DB b75c63f4 IST date)' },
  { eventId: 'EVT.2019.05.XX.01', category: 'residential+travel', domain: 'residential+travel/foreign_move_start', shape: 'point', dateConfidence: 'month_known', eventDate: '2019-05-14', provenance: 'DB event_date (928a1f56)' },
  { eventId: 'EVT.2010.XX.XX.02', category: 'spiritual', domain: 'spiritual/devata_adoption', shape: 'point', dateConfidence: 'exact', eventDate: '2010-06-30', provenance: 'DB shape=point, event_date (132b61e0) -- documented judgment call, see module docstring' },
  // ── TEST-scope (>= 2020-01-01) -- approximate placeholders from packet text ONLY, life_events never queried for these ──
  { eventId: 'EVT.2021.01.XX.01', category: 'health', domain: 'health/panic_episode', shape: 'point', dateConfidence: 'month_known', eventDate: '2021-01-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2021.XX.XX.02', category: 'career', domain: 'career/tepper_selection', shape: 'point', dateConfidence: 'year_only', eventDate: '2021-07-01', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2021.XX.XX.03', category: 'career', domain: 'career/quarry_stalled', shape: 'point', dateConfidence: 'year_only', eventDate: '2021-07-01', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2022.01.03.01', category: 'family', domain: 'family/childbirth', shape: 'point', dateConfidence: 'exact', eventDate: '2022-01-03', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2022.XX.XX.02', category: 'relationship', domain: 'relationship/affair_start', shape: 'point', dateConfidence: 'exact', eventDate: '2022-08-18', provenance: 'packet §1 text only, week-tier collapsed to exact placeholder (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2022.10.XX.01', category: 'relationship', domain: 'relationship/romantic_concurrent_ended', shape: 'point', dateConfidence: 'exact', eventDate: '2022-07-14', provenance: 'packet §1 native tightening #13 corrected date (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2015.XX.XX.01', category: 'spiritual', domain: 'spiritual/devata_adoption', shape: 'interval', dateConfidence: 'month_known', intervalStart: '2021-04-01', intervalEnd: '2021-05-31', provenance: 'packet §1 native tightening #10 corrected interval (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2023.05.XX.01', category: 'residential+travel', domain: 'residential+travel/foreign_move_end', shape: 'point', dateConfidence: 'month_known', eventDate: '2023-05-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2023.06.XX.01', category: 'education', domain: 'education/tepper_completed', shape: 'point', dateConfidence: 'month_known', eventDate: '2023-06-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2023.07.XX.01', category: 'career', domain: 'career/business_launch', shape: 'point', dateConfidence: 'month_known', eventDate: '2023-07-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2024.02.16.01', category: 'career', domain: 'career/business_milestone', shape: 'point', dateConfidence: 'exact', eventDate: '2024-02-16', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2025.05.XX.01', category: 'loss', domain: 'loss/financial_deception', shape: 'point', dateConfidence: 'month_known', eventDate: '2025-05-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2025.07.XX.01', category: 'finance', domain: 'finance/business_milestone_windfall', shape: 'point', dateConfidence: 'month_known', eventDate: '2025-07-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2026.03.20.01', category: 'career', domain: 'career/business_milestone', shape: 'point', dateConfidence: 'exact', eventDate: '2026-03-20', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2026.04.08.01', category: 'career', domain: 'career/quarry_cleared', shape: 'point', dateConfidence: 'exact', eventDate: '2026-04-08', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2025.XX.XX.02', category: 'health', domain: 'health/chronic_resolution', shape: 'point', dateConfidence: 'year_only', eventDate: '2025-07-01', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2025.XX.XX.01', category: 'spiritual', domain: 'spiritual/devata_shift', shape: 'point', dateConfidence: 'year_only', eventDate: '2025-07-01', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2026.01.XX.01', category: 'other', domain: 'other/psychological_shift', shape: 'point', dateConfidence: 'month_known', eventDate: '2026-01-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2024.XX.XX.01', category: 'spiritual', domain: 'spiritual/practice_intensification', shape: 'point', dateConfidence: 'year_only', eventDate: '2024-07-01', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2025.06.XX.01', category: 'spiritual', domain: 'spiritual/yantra_mandala', shape: 'point', dateConfidence: 'month_known', eventDate: '2025-06-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
  { eventId: 'EVT.2025.11.XX.01', category: 'spiritual', domain: 'spiritual/devata_adoption', shape: 'point', dateConfidence: 'month_known', eventDate: '2025-11-15', provenance: 'packet §1 text only (TEST-scope, not DB-queried)' },
]

function toDate(s: string): Date {
  return new Date(s + 'T00:00:00Z')
}

function toCurveEvent(r: RawEvent): CurveEvent {
  return {
    eventId: r.eventId,
    shape: r.shape,
    dateConfidence: r.dateConfidence,
    eventDate: r.eventDate ? toDate(r.eventDate) : undefined,
    intervalStart: r.intervalStart ? toDate(r.intervalStart) : undefined,
    intervalEnd: r.intervalEnd ? toDate(r.intervalEnd) : undefined,
  }
}

/** §3 point tolerance (exact->45d, month->75d, year_only->45d fallback, matching shape_scoring.ts's toleranceDaysFor). Buffer for the SCORING RANGE (not the match tolerance itself) is wider to give the model room to show a genuine local max. */
function bufferDaysFor(dc: DateConfidence): number {
  if (dc === 'exact') return 60
  if (dc === 'month_known') return 90
  return 150
}

function rangeForEvent(r: RawEvent): [Date, Date] {
  const buf = bufferDaysFor(r.dateConfidence) * 86_400_000
  if (r.shape === 'interval') {
    const s = toDate(r.intervalStart!).getTime()
    const e = toDate(r.intervalEnd!).getTime()
    return [new Date(s - buf), new Date(e + buf)]
  }
  const t = toDate(r.eventDate!).getTime()
  return [new Date(t - buf), new Date(t + buf)]
}

function matchToleranceDaysFor(dc: DateConfidence): number {
  if (dc === 'exact') return 45
  if (dc === 'month_known') return 75
  return 45 // year_only fallback, documented judgment call matching shape_scoring.ts's toleranceDaysFor
}

async function main() {
  console.error(`[b1_batch1] start ${new Date().toISOString()}`)

  // ── §0: manifest hash + packet blob-sha verification (never altered) ──
  const manifestHash = hashManifestFile(MANIFEST_PATH)
  const manifestRaw = JSON.parse(readFileSync(MANIFEST_PATH, 'utf8'))
  console.error(`[b1_batch1] manifest sha256=${manifestHash} version=${manifestRaw.version}`)
  if (manifestRaw.pre_registration_packet.git_blob_sha !== PACKET_BLOB_SHA_EXPECTED) {
    throw new Error(`packet blob sha mismatch: manifest says ${manifestRaw.pre_registration_packet.git_blob_sha}, expected ${PACKET_BLOB_SHA_EXPECTED}`)
  }

  // ── Build the TRAIN-scope event list from the packet's §1 table via filterToTrainScope() ──
  const allCurveEvents: CurveEvent[] = RAW_EVENTS.map(toCurveEvent)
  const trainCurveEvents = filterToTrainScope(allCurveEvents)
  const trainIds = new Set(trainCurveEvents.map((e) => e.eventId))
  const rawById = new Map(RAW_EVENTS.map((r) => [r.eventId, r]))
  const trainRaw = RAW_EVENTS.filter((r) => trainIds.has(r.eventId))
  const scoredRaw = trainRaw.filter((r) => !r.scoringExcluded)
  console.error(
    `[b1_batch1] filterToTrainScope: ${allCurveEvents.length} total packet rows -> ${trainCurveEvents.length} TRAIN-scope ` +
      `-> ${scoredRaw.length} actually scored (${trainRaw.length - scoredRaw.length} scoring-excluded per packet §0, disclosed)`
  )

  // ── Periods substrate (vimshottari, levels 1-3, live-queried this session, chart_dashas -- not life_events, no sealed-split restriction applies) ──
  const periodsRaw: { level_n: number; lord_graha: string; start_date: string; end_date: string }[] = JSON.parse(
    readFileSync(`${SCRATCH}/b1_batch1_vimshottari_periods.json`, 'utf8')
  )
  const periods: DashaPeriod[] = periodsRaw.map((p) => ({ level: p.level_n, lord: p.lord_graha, start: new Date(p.start_date), end: new Date(p.end_date) }))
  const chart: ChartContext = { chartId: CHART_ID, ayanamsha: AYANAMSHA, substrate: { periods } }

  // ── Batch 1 roster: pratyantar_lord + 4 PERMISSION systems ──
  const eventClassSignificators: Record<EventClass, Record<string, number>> = {}
  for (const r of RAW_EVENTS) eventClassSignificators[r.category] = significatorsForCategory(r.category)

  const permOpts: PermissionModelOptions = { sidecarUrl: SIDECAR_URL, apiKey: API_KEY, stepDays: 5, windowDays: 15.0, ayanamshaId: AYANAMSHA }
  const pratyantar = pratyantarLordModel(eventClassSignificators)
  const vimshottari = permissionSystemModel('vimshottari', permOpts)
  const yogini = permissionSystemModel('yogini', permOpts)
  const ashtottari = permissionSystemModel('ashtottari', permOpts)
  const charaKaraka = permissionSystemModel('chara_karaka', permOpts)
  const permissionModels: TemporalCurveModel[] = [vimshottari, yogini, ashtottari, charaKaraka]
  const allModels: TemporalCurveModel[] = [pratyantar, ...permissionModels]

  // ── Bind-time assertion (literal first action before any scoring) ──
  console.error('[b1_batch1] running assertRosterBindable() probe (eventClass=marriage, a known-populated class)...')
  const probeRange: [Date, Date] = [new Date('2013-10-01T00:00:00Z'), new Date('2014-02-01T00:00:00Z')]
  try {
    const report = await assertRosterBindable(allModels, chart, 'marriage', probeRange)
    console.error('[b1_batch1] BIND-TIME ASSERTION PASSED:', JSON.stringify(report))
  } catch (err) {
    if (err instanceof RosterBindFailureError) {
      console.error('[b1_batch1] BIND-TIME ASSERTION FAILED:', JSON.stringify(err.failures, null, 2))
      process.exit(1)
    }
    throw err
  }

  // ── §2: per-event, per-model scoring ──
  const params: MirroredScoringParams = { percentile: 0.9, shuffleCount: 1000, includeSecondaryBattery: true }
  const populatedEventClassesLive = ['career_advancement', 'major_gain', 'marriage'] // live-queried this session (gochara_resonance_map)

  type PermEventResult = { eventId: string; eventClass: string; harness: unknown; dr17: GradeResult } | { eventId: string; skipped: string }
  const results: {
    pratyantar_lord: { eventId: string; eventClass: string; harness: unknown; dr17: GradeResult }[]
    vimshottari: PermEventResult[]
    yogini: PermEventResult[]
    ashtottari: PermEventResult[]
    chara_karaka: PermEventResult[]
  } = { pratyantar_lord: [], vimshottari: [], yogini: [], ashtottari: [], chara_karaka: [] }

  const eventClassResolutions: { eventId: string; domain: string; resolved: boolean; eventClass: string | null; populated: boolean; reason: string }[] = []
  const negativeCrpsFindings: string[] = []
  let scoredEventIdx = 0

  for (const raw of scoredRaw) {
    scoredEventIdx++
    const curveEvent = toCurveEvent(raw)
    const range = rangeForEvent(raw)
    console.error(`[b1_batch1] event ${scoredEventIdx}/${scoredRaw.length} ${raw.eventId} category=${raw.category} domain=${raw.domain} range=${range[0].toISOString().slice(0, 10)}..${range[1].toISOString().slice(0, 10)}`)

    // ---- pratyantar_lord (eventClass = raw category, no gochara_resonance_map dependency) ----
    {
      const realCurve = pratyantar.curve(chart, raw.category, range)
      const harnessResult = runMirroredScoringHarness({ model: pratyantar, chart, eventClass: raw.category, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
      const controlCurves: CurvePoint[][] = []
      const totalDays = Math.round((range[1].getTime() - range[0].getTime()) / 86_400_000)
      for (let i = 1; i <= params.shuffleCount; i++) {
        const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * i)
        controlCurves.push(shuffledBirthControlCurve(realCurve, shiftDays, range[0], range[1]))
      }
      const baseline = computeControlBaseline(controlCurves)
      const gradingEvent: GradingEvent = {
        eventId: raw.eventId,
        shape: raw.shape === 'interval' ? 'interval' : 'point',
        dateConfidenceTier: tierForDateConfidence(raw.dateConfidence),
        matchToleranceDays: matchToleranceDaysFor(raw.dateConfidence),
        eventDate: raw.eventDate ? toDate(raw.eventDate) : undefined,
        intervalStart: raw.intervalStart ? toDate(raw.intervalStart) : undefined,
        intervalEnd: raw.intervalEnd ? toDate(raw.intervalEnd) : undefined,
      }
      const dr17 = gradeCurveEvent(realCurve, gradingEvent, baseline, 'pratyantar_lord')
      results.pratyantar_lord.push({ eventId: raw.eventId, eventClass: raw.category, harness: harnessResult, dr17 })
      if (harnessResult.primary.meanCrpsReal < 0) negativeCrpsFindings.push(`pratyantar_lord/${raw.eventId}/real`)
      if (harnessResult.primary.meanCrpsControlShuffled < 0) negativeCrpsFindings.push(`pratyantar_lord/${raw.eventId}/control_shuffled`)
      if (harnessResult.primary.meanCrpsControlAntiphase < 0) negativeCrpsFindings.push(`pratyantar_lord/${raw.eventId}/control_antiphase`)
      for (const p of harnessResult.primary.perEventReal) if (p.crps < 0) negativeCrpsFindings.push(`pratyantar_lord/${raw.eventId}/perEventReal`)
    }

    // ---- 4 PERMISSION systems (eventClass = resolved gochara_resonance_map class; skip if unresolved) ----
    const forResolution: RawEventForResolution = { eventId: raw.eventId, category: raw.category, domain: raw.domain }
    const resolution = resolveEventClass(forResolution)
    const populated = resolution.eventClass !== null && populatedEventClassesLive.includes(resolution.eventClass)
    eventClassResolutions.push({ eventId: raw.eventId, domain: raw.domain, resolved: resolution.resolved, eventClass: resolution.eventClass, populated, reason: resolution.reason })

    const permKeys: Array<['vimshottari' | 'yogini' | 'ashtottari' | 'chara_karaka', TemporalCurveModel]> = [
      ['vimshottari', vimshottari], ['yogini', yogini], ['ashtottari', ashtottari], ['chara_karaka', charaKaraka],
    ]
    if (!populated) {
      for (const [key] of permKeys) results[key].push({ eventId: raw.eventId, skipped: `unresolved_event_class: ${resolution.reason}` })
      continue
    }
    const eventClass = resolution.eventClass!
    console.error(`[b1_batch1]   event_class RESOLVED -> '${eventClass}' (populated) -- scoring all 4 PERMISSION contenders`)
    await Promise.all(permissionModels.map((m) => m.bind?.(chart, eventClass, range)))
    for (const [key, model] of permKeys) {
      try {
        const realCurve = model.curve(chart, eventClass, range)
        const harnessResult = runMirroredScoringHarness({ model, chart, eventClass, events: [curveEvent], boundsStart: range[0], boundsEnd: range[1], params })
        const controlCurves: CurvePoint[][] = []
        const totalDays = Math.round((range[1].getTime() - range[0].getTime()) / 86_400_000)
        for (let i = 1; i <= params.shuffleCount; i++) {
          const shiftDays = Math.round((totalDays / (params.shuffleCount + 1)) * i)
          controlCurves.push(shuffledBirthControlCurve(realCurve, shiftDays, range[0], range[1]))
        }
        const baseline = computeControlBaseline(controlCurves)
        const gradingEvent: GradingEvent = {
          eventId: raw.eventId,
          shape: raw.shape === 'interval' ? 'interval' : 'point',
          dateConfidenceTier: tierForDateConfidence(raw.dateConfidence),
          matchToleranceDays: matchToleranceDaysFor(raw.dateConfidence),
          eventDate: raw.eventDate ? toDate(raw.eventDate) : undefined,
          intervalStart: raw.intervalStart ? toDate(raw.intervalStart) : undefined,
          intervalEnd: raw.intervalEnd ? toDate(raw.intervalEnd) : undefined,
        }
        const dr17 = gradeCurveEvent(realCurve, gradingEvent, baseline, key)
        results[key].push({ eventId: raw.eventId, eventClass, harness: harnessResult, dr17 })
        if (harnessResult.primary.meanCrpsReal < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/real`)
        if (harnessResult.primary.meanCrpsControlShuffled < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/control_shuffled`)
        if (harnessResult.primary.meanCrpsControlAntiphase < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/control_antiphase`)
      } catch (err) {
        results[key].push({ eventId: raw.eventId, skipped: `error: ${err instanceof Error ? `${err.name}: ${err.message}` : String(err)}` })
      }
    }
    writeSnapshot()
  }
  writeSnapshot()

  function writeSnapshot() {
    writeFileSync(`${SCRATCH}/b1_batch1_v2_progress.json`, JSON.stringify({ eventsDone: scoredEventIdx, eventsTotal: scoredRaw.length, negativeCrpsCount: negativeCrpsFindings.length }, null, 2))
    writeFileSync(`${SCRATCH}/b1_batch1_v2_results_raw.json`, JSON.stringify(results, null, 2))
  }

  // ── DR-20 defense-in-depth: explicit assertNoSealedSplitEvents() on the FINAL scored event list, before any artifact write ──
  const finalScoredCurveEvents = scoredRaw.map(toCurveEvent)
  assertNoSealedSplitEvents(finalScoredCurveEvents)
  console.error(`[b1_batch1] assertNoSealedSplitEvents() PASSED explicitly on ${finalScoredCurveEvents.length} scored events (defense-in-depth, in addition to harness.ts's internal CR-123 call)`)

  // ── Zero negative CRPS verification ──
  if (negativeCrpsFindings.length > 0) {
    console.error('[b1_batch1] NEGATIVE CRPS FOUND:', JSON.stringify(negativeCrpsFindings))
    throw new Error(`negative CRPS values found: ${negativeCrpsFindings.join(', ')} -- F-2 (circularShiftCurve sort fix, PR #697) should make this impossible; this is a real defect if it fires.`)
  }
  console.error(`[b1_batch1] zero negative CRPS verified across ${scoredRaw.length} events x 5 contenders (real + shuffled-control + antiphase-control)`)

  // ── Write batch artifact via writeBatchArtifact() ──
  const writtenAt = new Date().toISOString()
  const batchResults = {
    batch_id: 1,
    contenders: ['pratyantar_lord', 'vimshottari', 'yogini', 'ashtottari', 'chara_karaka'],
    chart_id: CHART_ID,
    packet_blob_sha: PACKET_BLOB_SHA_EXPECTED,
    manifest_version: manifestRaw.version,
    train_scope_event_count: trainCurveEvents.length,
    scored_event_count: scoredRaw.length,
    scoring_excluded: trainRaw.filter((r) => r.scoringExcluded).map((r) => ({ eventId: r.eventId, reason: r.exclusionReason })),
    permission_event_class_resolution: eventClassResolutions,
    populated_event_classes_live: populatedEventClassesLive,
    negative_crps_count: negativeCrpsFindings.length,
    control_design: { mechanism: 'DR-15(c) coverage-matched shuffled-birth, evenly-spaced circular shifts of the real curve per event range (harness.ts / curve_controls.ts)', n: params.shuffleCount },
    dr17_grading: { framework: 'DR-17 (peak/sub_peak/elevated/neutral/contra)', weights_ruling: 'NP-D4B-001', tie_bands_ruling: 'NP-D4B-003 adopted table', anti_hit: 'structurally inert this run -- see dr17_grading.ts module docstring judgment call 4' },
    results,
  }
  const outPath = writeBatchArtifact(ARTIFACTS_DIR, 'batch1', manifestHash, batchResults, writtenAt)
  console.error(`[b1_batch1] DONE. Wrote ${outPath}`)
  console.error(`[b1_batch1] end ${new Date().toISOString()}`)
}

main().catch((err) => {
  console.error('[b1_batch1] FATAL:', err)
  process.exit(1)
})
