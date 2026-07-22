#!/usr/bin/env -S npx tsx
/**
 * b1_batch3_driver_v2.ts — D-4b B-1 CLEAN re-run (attempt #3), BATCH 3/3 (FINAL BATCH).
 *
 * Contenders: guru_shani_double_transit, av_threshold, planetary_return (all
 * 3 PERMISSION standalone systems, permission_model.ts, same pattern as
 * batches 1/2) + hierarchical_ensemble (ensemble_model.ts) LAST, scored over
 * whichever of the manifest's 13 non-ensemble contenders are evaluable --
 * see B1_RUN_MANIFEST_v2_0.json's `batching.batches[2]`. Scored against the
 * TRAIN split ONLY (event_date < 2020-01-01), built from
 * D4B_PREREGISTRATION_PACKET_v1_0.md v1.2 §1 (git blob 9b6713db, verified)
 * via filterToTrainScope() (sealed_split_guard.ts) -- never a hand-written
 * date filter. Structural sealed-split enforcement: assertNoSealedSplitEvents
 * fires both inside harness.ts's runMirroredScoringHarness (CR-123) AND
 * explicitly here, right after building the scored event list and before
 * any artifact write (defense-in-depth per the native's instruction).
 *
 * RAW_EVENTS below is copied VERBATIM from b1_batch1_driver_v2_0.ts (same
 * packet, same git blob sha, same provenance rules) -- per the manifest's
 * own "identical everything" rule, every batch must build its TRAIN-scope
 * set from the exact same 56-row packet table. See batch 1's own module
 * docstring for full per-row provenance.
 *
 * ── Which of the 13 non-ensemble contenders are "evaluable" (read live
 * from THIS branch's already-committed batch 1/2 artifacts, not assumed) ──
 * batch_batch1.json (pratyantar_lord/vimshottari/yogini/ashtottari/
 * chara_karaka) and batch_batch2.json (naisargika/mudda/kalachakra/
 * narayana/sade_sati) both report `negative_crps_count: 0` and, per-model,
 * ZERO `skipped: "error: ..."` rows across all 31 TRAIN-scored events for
 * all 10 contenders (every skip present is the disclosed, expected
 * `unresolved_event_class` kind, not a failure). All 10 are therefore
 * evaluable. This batch verifies its OWN 3 new PERMISSION contenders
 * (guru_shani_double_transit, av_threshold, planetary_return) the same way
 * live, via `assertRosterBindable` + a per-event try/catch identical to
 * batches 1/2's pattern -- if any of these 3 (or, in principle, any of the
 * other 10, re-probed here via the SAME `assertRosterBindable` call on the
 * full 13-model roster) fails, it is EXCLUDED from the ensemble sum and the
 * exclusion is disclosed in the batch artifact's `ensemble_exclusions`
 * array -- never silently dropped, never silently included as a phantom
 * zero.
 *
 * PERMISSION-system (guru_shani_double_transit/av_threshold/
 * planetary_return) event_class resolution: same event_class_resolution.ts
 * table as batches 1/2 (only 3 gochara_resonance_map classes populated for
 * this chart: career_advancement=22, major_gain=35, marriage=23 rows) --
 * resolves the same 2 of this chart's 31 TRAIN-scored events to a populated
 * class: EVT.2013.12.11.01 (marriage) and EVT.2010.XX.XX.01 (major_gain).
 * Every other TRAIN event is UNRESOLVED for all 3 of this batch's PERMISSION
 * contenders AND for hierarchical_ensemble (which requires the SAME
 * populated-class binding every one of its 12 PERMISSION constituents
 * needs) and is SKIPPED for all 4, explicitly and visibly.
 *
 * ── hierarchical_ensemble construction (roster.ts / ensemble_model.ts) ──
 * `roster.ts`'s `buildActiveRoster(eventClassSignificators, permOpts)`
 * returns the manifest-order 13-model list: [pratyantar_lord, vimshottari,
 * yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra, narayana,
 * sade_sati, guru_shani_double_transit, av_threshold, planetary_return].
 * This batch's own 3 standalone contenders are the LAST 3 elements of that
 * SAME array (found by modelId, not re-instantiated) -- one live sidecar
 * bind per system, not duplicated between the standalone scoring pass and
 * the ensemble's constituent list. `hierarchicalEnsembleModel()` sums
 * whichever of the 13 successfully bind for a given (chart, eventClass,
 * range) -- see module docstring above for the exclusion-disclosure rule.
 *
 * DOCUMENTED JUDGMENT CALL (grid alignment / pratyantar_lord's ensemble
 * contribution for the 2 populated events): `hierarchical_ensemble` is
 * called with the SAME `eventClass` argument passed to every PERMISSION
 * constituent -- the resolved gochara class ('marriage' / 'major_gain'),
 * per `ensemble_model.ts`'s single-eventClass-for-all-constituents
 * contract. `pratyantar_lord`'s own `eventClassSignificators` map (built,
 * per batch 1's convention, keyed by LEL `category` -- 'family', 'finance',
 * etc. -- never by gochara event_class) has no entry for 'marriage' or
 * 'major_gain', so `pratyantar_lord`'s own `curve()` (model_interface.ts)
 * returns its documented HONEST ZERO curve (see that module's own comment:
 * "an event class this significator map has no entry for genuinely has
 * zero modeled intensity under this model") for both of this batch's
 * populated events. This is not a defect and not silently assumed --
 * `pratyantar_lord`'s own contribution to `hierarchical_ensemble`'s summed
 * curve for these 2 events is therefore always 0 by the pre-existing model
 * contract, and the ensemble's real signal for these 2 events comes
 * entirely from its 12 PERMISSION constituents. Inventing a gochara-class
 * keyed significator map for `pratyantar_lord` (so it would contribute a
 * non-zero curve here) would require an unauthorized new
 * astrological-domain judgment call outside this batch's scope (B.10) --
 * not attempted.
 *
 * Sidecar: PYTHON_SIDECAR_URL / PYTHON_SIDECAR_API_KEY must be set in the
 * environment this driver runs under (production sidecar
 * https://amjis-sidecar-938361928218.asia-south1.run.app, API key live
 * from `gcloud secrets versions access latest --secret=PYTHON_SIDECAR_API_KEY`
 * this session -- never hardcoded into this file).
 *
 * Periods substrate: `chart.substrate.periods` (chart_dashas, level 1-3)
 * is REUSED verbatim from this same session's live batch-1 query
 * (`${SCRATCH}/b1_batch1_vimshottari_periods.json`, chart_dashas table --
 * not life_events, no sealed-split restriction applies, disclosed here
 * rather than re-issued as a fresh identical query) -- needed only so
 * `pratyantar_lord` (an ensemble constituent) has a non-throwing
 * `curve()`; this batch does not score `pratyantar_lord` standalone
 * (already scored, batch 1).
 */
import { readFileSync, writeFileSync } from 'node:fs'
import type { ChartContext, EventClass, TemporalCurveModel } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface'
import type { PermissionModelOptions } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/permission_model'
import { buildActiveRoster } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/roster'
import { hierarchicalEnsembleModel } from '/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/wave-D-4b-B1-full-rerun-2/platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/ensemble_model'
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

// ── DOMAIN_LORDS / significatorsForCategory, carried verbatim from batch 1's own copy (mechanisms.ts, T-0, live-verified) -- needed to construct pratyantar_lord as an ensemble constituent, per the module docstring's documented judgment call. ──
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

// ── Full 56-row packet §1 event set. VERBATIM copy of b1_batch1_driver_v2_0.ts's
// RAW_EVENTS (same packet, same git blob sha) -- see that module's docstring for
// full per-row provenance. ──
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
  { eventId: 'EVT.2002.XX.XX.02', category: 'spiritual', domain: 'spiritual/sadhana_initiation', shape: 'point', dateConfidence: 'exact', eventDate: '2002-06-30', provenance: 'DB shape=point, event_date (62f0460d) -- documented judgment call, see batch 1 module docstring' },
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
  { eventId: 'EVT.2010.XX.XX.02', category: 'spiritual', domain: 'spiritual/devata_adoption', shape: 'point', dateConfidence: 'exact', eventDate: '2010-06-30', provenance: 'DB shape=point, event_date (132b61e0) -- documented judgment call, see batch 1 module docstring' },
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
  console.error(`[b1_batch3] start ${new Date().toISOString()}`)

  if (!SIDECAR_URL || !API_KEY) {
    throw new Error('[b1_batch3] PYTHON_SIDECAR_URL and PYTHON_SIDECAR_API_KEY must both be set in the environment -- refusing to run against permission_model.ts\'s silent localhost:8000 default (would fail every bind() with a network error, not a scoring result).')
  }

  // ── §0: manifest hash + packet blob-sha verification (never altered) ──
  const manifestHash = hashManifestFile(MANIFEST_PATH)
  const manifestRaw = JSON.parse(readFileSync(MANIFEST_PATH, 'utf8'))
  console.error(`[b1_batch3] manifest sha256=${manifestHash} version=${manifestRaw.version}`)
  if (manifestRaw.pre_registration_packet.git_blob_sha !== PACKET_BLOB_SHA_EXPECTED) {
    throw new Error(`packet blob sha mismatch: manifest says ${manifestRaw.pre_registration_packet.git_blob_sha}, expected ${PACKET_BLOB_SHA_EXPECTED}`)
  }

  // ── Build the TRAIN-scope event list from the packet's §1 table via filterToTrainScope() ──
  const allCurveEvents: CurveEvent[] = RAW_EVENTS.map(toCurveEvent)
  const trainCurveEvents = filterToTrainScope(allCurveEvents)
  const trainIds = new Set(trainCurveEvents.map((e) => e.eventId))
  const trainRaw = RAW_EVENTS.filter((r) => trainIds.has(r.eventId))
  const scoredRaw = trainRaw.filter((r) => !r.scoringExcluded)
  console.error(
    `[b1_batch3] filterToTrainScope: ${allCurveEvents.length} total packet rows -> ${trainCurveEvents.length} TRAIN-scope ` +
      `-> ${scoredRaw.length} actually scored (${trainRaw.length - scoredRaw.length} scoring-excluded per packet §0, disclosed)`
  )

  // ── Periods substrate (chart_dashas, levels 1-3, REUSED from this session's batch-1 live query -- see module docstring). Needed only for pratyantar_lord as an ensemble constituent. ──
  const periodsRaw: { level_n: number; lord_graha: string; start_date: string; end_date: string }[] = JSON.parse(
    readFileSync(`${SCRATCH}/b1_batch1_vimshottari_periods.json`, 'utf8')
  )
  const periods: DashaPeriod[] = periodsRaw.map((p) => ({ level: p.level_n, lord: p.lord_graha, start: new Date(p.start_date), end: new Date(p.end_date) }))
  const chart: ChartContext = { chartId: CHART_ID, ayanamsha: AYANAMSHA, substrate: { periods } }

  // ── pratyantar_lord's own significator map (category-keyed, per batch 1's convention) ──
  const eventClassSignificators: Record<EventClass, Record<string, number>> = {}
  for (const r of RAW_EVENTS) eventClassSignificators[r.category] = significatorsForCategory(r.category)

  // ── Full 13-model manifest-order roster (roster.ts) -- source of both this batch's own 3 standalone contenders AND the ensemble's constituents ──
  const permOpts: PermissionModelOptions = { sidecarUrl: SIDECAR_URL, apiKey: API_KEY, stepDays: 5, windowDays: 15.0, ayanamshaId: AYANAMSHA }
  const fullRoster: TemporalCurveModel[] = buildActiveRoster(eventClassSignificators, permOpts)
  console.error(`[b1_batch3] fullRoster (manifest order, 13 models): ${fullRoster.map((m) => m.modelId).join(', ')}`)

  const guruShani = fullRoster.find((m) => m.modelId === 'guru_shani_double_transit')!
  const avThreshold = fullRoster.find((m) => m.modelId === 'av_threshold')!
  const planetaryReturn = fullRoster.find((m) => m.modelId === 'planetary_return')!
  if (!guruShani || !avThreshold || !planetaryReturn) {
    throw new Error('[b1_batch3] fullRoster is missing one of this batch\'s own 3 contenders -- roster.ts drifted from PERMISSION_SYSTEM_IDS unexpectedly.')
  }

  // ── Bind-time assertion over the FULL 13-model roster (covers this batch's own 3 AND every ensemble constituent in one probe) ──
  console.error('[b1_batch3] running assertRosterBindable() probe over the full 13-model roster (eventClass=marriage, a known-populated class)...')
  const probeRange: [Date, Date] = [new Date('2013-10-01T00:00:00Z'), new Date('2014-02-01T00:00:00Z')]
  try {
    const report = await assertRosterBindable(fullRoster, chart, 'marriage', probeRange)
    console.error('[b1_batch3] BIND-TIME ASSERTION PASSED:', JSON.stringify(report))
  } catch (err) {
    if (err instanceof RosterBindFailureError) {
      console.error('[b1_batch3] BIND-TIME ASSERTION FAILED:', JSON.stringify(err.failures, null, 2))
      process.exit(1)
    }
    throw err
  }

  // ── §2: per-event, per-model scoring ──
  const params: MirroredScoringParams = { percentile: 0.9, shuffleCount: 1000, includeSecondaryBattery: true }
  const populatedEventClassesLive = ['career_advancement', 'major_gain', 'marriage'] // live-queried by batch 1 this session (gochara_resonance_map); reused here per manifest's "identical everything" rule

  type PermEventResult = { eventId: string; eventClass: string; harness: unknown; dr17: GradeResult } | { eventId: string; skipped: string }
  const results: {
    guru_shani_double_transit: PermEventResult[]
    av_threshold: PermEventResult[]
    planetary_return: PermEventResult[]
    hierarchical_ensemble: PermEventResult[]
  } = { guru_shani_double_transit: [], av_threshold: [], planetary_return: [], hierarchical_ensemble: [] }

  const eventClassResolutions: { eventId: string; domain: string; resolved: boolean; eventClass: string | null; populated: boolean; reason: string }[] = []
  const negativeCrpsFindings: string[] = []
  const ensembleExclusions: { eventId: string; excludedModelId: string; reason: string }[] = []
  let scoredEventIdx = 0

  const ownKeys: Array<['guru_shani_double_transit' | 'av_threshold' | 'planetary_return', TemporalCurveModel]> = [
    ['guru_shani_double_transit', guruShani], ['av_threshold', avThreshold], ['planetary_return', planetaryReturn],
  ]

  function scoreOneModel(key: string, model: TemporalCurveModel, chart: ChartContext, eventClass: string, range: [Date, Date], raw: RawEvent, curveEvent: CurveEvent): PermEventResult {
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
    if (harnessResult.primary.meanCrpsReal < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/real`)
    if (harnessResult.primary.meanCrpsControlShuffled < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/control_shuffled`)
    if (harnessResult.primary.meanCrpsControlAntiphase < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/control_antiphase`)
    for (const p of harnessResult.primary.perEventReal) if (p.crps < 0) negativeCrpsFindings.push(`${key}/${raw.eventId}/perEventReal`)
    return { eventId: raw.eventId, eventClass, harness: harnessResult, dr17 }
  }

  for (const raw of scoredRaw) {
    scoredEventIdx++
    const curveEvent = toCurveEvent(raw)
    const range = rangeForEvent(raw)
    console.error(`[b1_batch3] event ${scoredEventIdx}/${scoredRaw.length} ${raw.eventId} category=${raw.category} domain=${raw.domain} range=${range[0].toISOString().slice(0, 10)}..${range[1].toISOString().slice(0, 10)}`)

    const forResolution: RawEventForResolution = { eventId: raw.eventId, category: raw.category, domain: raw.domain }
    const resolution = resolveEventClass(forResolution)
    const populated = resolution.eventClass !== null && populatedEventClassesLive.includes(resolution.eventClass)
    eventClassResolutions.push({ eventId: raw.eventId, domain: raw.domain, resolved: resolution.resolved, eventClass: resolution.eventClass, populated, reason: resolution.reason })

    if (!populated) {
      for (const [key] of ownKeys) results[key].push({ eventId: raw.eventId, skipped: `unresolved_event_class: ${resolution.reason}` })
      results.hierarchical_ensemble.push({ eventId: raw.eventId, skipped: `unresolved_event_class: ${resolution.reason} (ensemble requires the same populated-class binding every PERMISSION constituent needs)` })
      continue
    }
    const eventClass = resolution.eventClass!
    console.error(`[b1_batch3]   event_class RESOLVED -> '${eventClass}' (populated) -- binding full 13-model roster + scoring this batch's 3 contenders + hierarchical_ensemble`)

    // ── Bind the FULL 13-model roster for this exact (chart, eventClass, range); track per-model success ──
    const bindOutcomes = await Promise.allSettled(fullRoster.map((m) => m.bind ? m.bind(chart, eventClass, range) : Promise.resolve()))
    const evaluableThisEvent: TemporalCurveModel[] = []
    bindOutcomes.forEach((outcome, i) => {
      const m = fullRoster[i]
      if (outcome.status === 'fulfilled') {
        evaluableThisEvent.push(m)
      } else {
        const reason = outcome.reason instanceof Error ? `${outcome.reason.name}: ${outcome.reason.message}` : String(outcome.reason)
        console.error(`[b1_batch3]   bind() FAILED for ensemble constituent '${m.modelId}': ${reason} -- EXCLUDING from hierarchical_ensemble for this event, disclosed.`)
        ensembleExclusions.push({ eventId: raw.eventId, excludedModelId: m.modelId, reason: `bind() failed: ${reason}` })
      }
    })

    // ---- This batch's own 3 standalone contenders ----
    for (const [key, model] of ownKeys) {
      try {
        if (!evaluableThisEvent.includes(model)) {
          throw new Error(`bind() failed for '${model.modelId}' -- see ensembleExclusions for this event`)
        }
        results[key].push(scoreOneModel(key, model, chart, eventClass, range, raw, curveEvent))
      } catch (err) {
        results[key].push({ eventId: raw.eventId, skipped: `error: ${err instanceof Error ? `${err.name}: ${err.message}` : String(err)}` })
      }
    }

    // ---- hierarchical_ensemble, built from whichever of the 13 successfully bound for THIS event ----
    try {
      if (evaluableThisEvent.length === 0) {
        throw new Error('zero of the 13 roster constituents bound successfully for this event -- an ensemble over zero models is not a legitimate superposition (B.10)')
      }
      const ensembleModel = hierarchicalEnsembleModel(evaluableThisEvent)
      results.hierarchical_ensemble.push(scoreOneModel('hierarchical_ensemble', ensembleModel, chart, eventClass, range, raw, curveEvent))
    } catch (err) {
      results.hierarchical_ensemble.push({ eventId: raw.eventId, skipped: `error: ${err instanceof Error ? `${err.name}: ${err.message}` : String(err)}` })
    }

    writeSnapshot()
  }
  writeSnapshot()

  function writeSnapshot() {
    writeFileSync(`${SCRATCH}/b1_batch3_v2_progress.json`, JSON.stringify({ eventsDone: scoredEventIdx, eventsTotal: scoredRaw.length, negativeCrpsCount: negativeCrpsFindings.length, ensembleExclusionsCount: ensembleExclusions.length }, null, 2))
    writeFileSync(`${SCRATCH}/b1_batch3_v2_results_raw.json`, JSON.stringify(results, null, 2))
  }

  // ── DR-20 defense-in-depth: explicit assertNoSealedSplitEvents() on the FINAL scored event list, before any artifact write ──
  const finalScoredCurveEvents = scoredRaw.map(toCurveEvent)
  assertNoSealedSplitEvents(finalScoredCurveEvents)
  console.error(`[b1_batch3] assertNoSealedSplitEvents() PASSED explicitly on ${finalScoredCurveEvents.length} scored events (defense-in-depth, in addition to harness.ts's internal CR-123 call)`)

  // ── Zero negative CRPS verification ──
  if (negativeCrpsFindings.length > 0) {
    console.error('[b1_batch3] NEGATIVE CRPS FOUND:', JSON.stringify(negativeCrpsFindings))
    throw new Error(`negative CRPS values found: ${negativeCrpsFindings.join(', ')} -- F-2 (circularShiftCurve sort fix, PR #697) should make this impossible; this is a real defect if it fires.`)
  }
  console.error(`[b1_batch3] zero negative CRPS verified across ${scoredRaw.length} events x 4 contenders (real + shuffled-control + antiphase-control)`)
  console.error(`[b1_batch3] ensemble exclusions this run: ${ensembleExclusions.length}`)

  // ── Write batch artifact via writeBatchArtifact() ──
  const writtenAt = new Date().toISOString()
  const batchResults = {
    batch_id: 3,
    contenders: ['guru_shani_double_transit', 'av_threshold', 'planetary_return', 'hierarchical_ensemble'],
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
    ensemble_construction: {
      full_roster_order: fullRoster.map((m) => m.modelId),
      note: 'hierarchical_ensemble is built per-event from whichever of the 13-model full roster successfully bind() for that event\'s (chart, eventClass, range); pratyantar_lord is always an attempted constituent but contributes an honest ZERO curve for both of this batch\'s populated events (model_interface.ts documented behaviour -- eventClassSignificators is category-keyed, has no "marriage"/"major_gain" entry) -- see this driver\'s own module docstring "DOCUMENTED JUDGMENT CALL" section.',
      ensemble_exclusions: ensembleExclusions,
    },
    evaluable_contenders_read_from_batches_1_2: {
      batch1: ['pratyantar_lord', 'vimshottari', 'yogini', 'ashtottari', 'chara_karaka'],
      batch2: ['naisargika', 'mudda', 'kalachakra', 'narayana', 'sade_sati'],
      note: 'read live from batch_batch1.json / batch_batch2.json (already committed on this branch) before this batch ran: negative_crps_count=0 and zero `skipped: "error: ..."` rows for all 10 contenders across all 31 TRAIN-scored events -- all 10 are evaluable, no exclusions carried forward from batches 1/2.',
    },
    results,
  }
  const outPath = writeBatchArtifact(ARTIFACTS_DIR, 'batch3', manifestHash, batchResults, writtenAt)
  console.error(`[b1_batch3] DONE. Wrote ${outPath}`)
  console.error(`[b1_batch3] end ${new Date().toISOString()}`)
}

main().catch((err) => {
  console.error('[b1_batch3] FATAL:', err)
  process.exit(1)
})
