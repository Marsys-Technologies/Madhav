-- Migration 456: brahma_event_ontology DR-13 shape/evidence/self-report/kill-switch extension
-- Created: 2026-07-19
-- Wave: D-4a "Measurement Foundry", Lane A-2 (Canonical event ontology)
--
-- Numbering note: highest numbered file in platform/supabase/migrations/ is 434, but migrate.ts
-- reads BOTH platform/migrations/ (legacy) and platform/supabase/migrations/ and dedups by
-- FILENAME, not number (see platform/supabase/migrations/README.md). platform/migrations/ already
-- has 455_kala_activation_period_cardinality_v2.sql (Lane A-0's CR-109 fix, merged to main at
-- c1187a8d). 456 is the first free number across BOTH directories combined, per the README's own
-- guidance ("pick a fresh number... increment beyond the current highest in both dirs combined").
--
-- Context: BRIEF_D4A.md Lane A-2 asks for a published canonical event-class ontology carrying
-- (1) stable event-class IDs shared by LEL/evidence/lambda_e, (2) event-class-specific evidence
-- requirements (gain != loss), (3) non-discriminating self-report flags, (4) kill-switch criteria
-- as data, (5) a canonical temporal SHAPE per class (point | interval | chain, DIS.026/DR-13),
-- including a chain's irreversibility milestone.
--
-- `brahma_event_ontology` (migration 388, BA-P3A "bg_ghatana") already exists and is ALREADY the
-- enforced event-class registry: `platform/src/lib/mcp/lel_event_writer.ts` rejects any LEL intake
-- whose event_class is not a row in this table. Building a second, competing ontology table would
-- duplicate a canonical artifact (CLAUDE.md: "Do not duplicate canonical-artifact paths") and split
-- the single source of truth the write path already enforces. This migration EXTENDS the existing
-- 22-class table with the DR-13 fields it lacks, rather than replacing it.
--
-- Coverage check performed live against `life_events` for chart 482012f1 (57 rows, 2026-07-19):
-- 13 live categories found (career, creative, education, family, finance, health, loss, other,
-- psychological, relationship, residential+travel, spiritual, travel). The 22 existing classes
-- cover 9 of these; this migration adds 5 new classes (achievement_recognition,
-- financial_deception, psychological_arc, birth_anchor, travel_event) to reach full coverage of
-- 'creative', 'psychological', 'other', and the deception/self-report-only subset of 'loss'.
--
-- Reversible: DOWN drops the added columns and the 5 new rows; the 22 original rows and their
-- pre-existing columns are untouched by the DOWN path.

BEGIN;

-- ── DDL: add DR-13 shape + evidence + self-report + kill-switch columns ───────────────────────

ALTER TABLE brahma_event_ontology
  ADD COLUMN IF NOT EXISTS temporal_shape TEXT,
  ADD COLUMN IF NOT EXISTS duration_prior JSONB,
  ADD COLUMN IF NOT EXISTS milestone_template JSONB,
  ADD COLUMN IF NOT EXISTS irreversibility_milestone TEXT,
  ADD COLUMN IF NOT EXISTS evidence_requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS self_report_non_discriminating BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS kill_switch_criteria JSONB NOT NULL DEFAULT '[]'::jsonb;

COMMENT ON COLUMN brahma_event_ontology.temporal_shape IS
  'DR-13/DIS.026 canonical shape: point (single dateable moment) | interval (elevated-hazard span '
  'with a duration_prior, no named milestones) | chain (named milestone_template, independently '
  'dateable). Consumed identically by the matcher (A-1), the prospective ledger (A-4 claim_shape '
  'validation), and the D-5 engine''s own output semantics — an event-class-shape mismatch is a '
  'schema violation, not a soft warning.';
COMMENT ON COLUMN brahma_event_ontology.duration_prior IS
  'interval-shape only: {min_days, typical_days, max_days}. NULL for point/chain.';
COMMENT ON COLUMN brahma_event_ontology.milestone_template IS
  'chain-shape only: ordered array of {milestone_id, name_en, typical_offset_days_from_first}. '
  'NULL for point/interval. typical_offset_days_from_first is a structural prior, not a fitted value.';
COMMENT ON COLUMN brahma_event_ontology.irreversibility_milestone IS
  'chain-shape only (nullable even then): milestone_id of the point-of-no-return milestone in '
  'milestone_template (e.g. business_launch.first_revenue, separation.final_decree). NULL when the '
  'chain has no classically-meaningful irreversibility point (e.g. relocation is reversible).';
COMMENT ON COLUMN brahma_event_ontology.evidence_requirements IS
  'Class-specific evidence signature: {valence: gain|loss|neutral|mixed, externally_verifiable: '
  'bool, verification_sources: [text], self_report_risk: none|low|moderate|high, notes: text}. '
  'A financial-gain class and a financial-loss class carry DIFFERENT evidence_requirements — '
  'never a shared bucket that cannot discriminate (BRIEF_D4A Lane A-2).';
COMMENT ON COLUMN brahma_event_ontology.self_report_non_discriminating IS
  'true when this class''s typical evidence is inherently self-reported with no external '
  'corroboration path (romantic status, internal devotional shifts, unresolved fraud claims). '
  'Calibration/confidence scoring MUST NOT weight a self_report_non_discriminating=true class '
  'the same as an externally_verifiable class — this flag is the switch that prevents it.';
COMMENT ON COLUMN brahma_event_ontology.kill_switch_criteria IS
  'Array of {criterion_id, description}: conditions that, if an actual instance meets them, '
  'DISQUALIFY that instance from lambda_e scoring / primary hit-rate (diagnostic-battery-only or '
  'fully excluded). Encoded as data so the harness (A-3/A-5) can read and enforce it mechanically '
  'rather than each consumer re-implementing ad hoc exclusion logic.';

-- ── BACKFILL: DR-13 fields for the 22 existing (native-ratified v1.1) classes ─────────────────

UPDATE brahma_event_ontology AS t SET
  temporal_shape             = v.temporal_shape,
  duration_prior              = v.duration_prior::jsonb,
  milestone_template          = v.milestone_template::jsonb,
  irreversibility_milestone   = v.irreversibility_milestone,
  evidence_requirements       = v.evidence_requirements::jsonb,
  self_report_non_discriminating = v.self_report_non_discriminating,
  kill_switch_criteria        = v.kill_switch_criteria::jsonb
FROM (VALUES
  -- event_class_id, temporal_shape, duration_prior, milestone_template, irreversibility_milestone,
  --   evidence_requirements, self_report_non_discriminating, kill_switch_criteria
  ('career_entry', 'point', NULL, NULL, NULL,
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["offer letter","joining letter","HR record"],"self_report_risk":"low","notes":"Employment start is externally verifiable via employer records."}',
    false, '[]'),

  ('career_advancement', 'point', NULL, NULL, NULL,
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["promotion letter","title change","payroll record"],"self_report_risk":"low","notes":null}',
    false, '[]'),

  ('career_change', 'chain',
    NULL,
    '[{"milestone_id":"resignation_or_decision","name_en":"Resignation / decision to change","typical_offset_days_from_first":0},{"milestone_id":"offer_accepted","name_en":"New offer accepted","typical_offset_days_from_first":30},{"milestone_id":"new_role_start","name_en":"New role start date","typical_offset_days_from_first":60}]',
    'new_role_start',
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["resignation letter","new offer letter","new employer joining record"],"self_report_risk":"low","notes":"An employer switch unfolds as a chain; new_role_start is the irreversibility point (prior employer relationship closed in practice)."}',
    false, '[]'),

  ('career_setback', 'interval', '{"min_days":30,"typical_days":180,"max_days":720}', NULL, NULL,
    '{"valence":"loss","externally_verifiable":false,"verification_sources":["layoff notice","public news of employer distress","funding-lapse record where available"],"self_report_risk":"moderate","notes":"Employer instability / business stalling is often perceived before it is externally documented."}',
    false,
    '[{"criterion_id":"subjective_instability_perception","description":"Instability perceived by the native but with no external marker (no layoff notice, no public news, no funding-lapse record) is self-report-only: diagnostic-battery-only, never primary hit-rate scoring."}]'),

  ('business_launch', 'chain',
    NULL,
    '[{"milestone_id":"decision","name_en":"Decision to found/launch","typical_offset_days_from_first":0},{"milestone_id":"registration","name_en":"Legal/business registration","typical_offset_days_from_first":45},{"milestone_id":"first_revenue","name_en":"First revenue booked","typical_offset_days_from_first":120}]',
    'first_revenue',
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["registration certificate","first invoice/payment record"],"self_report_risk":"low","notes":"first_revenue is the classical irreversibility point per BRIEF_D4A Lane A-2''s own worked example (decision -> registration -> first-revenue)."}',
    false, '[]'),

  ('education_milestone', 'chain',
    NULL,
    '[{"milestone_id":"exam_written","name_en":"Entrance/qualifying exam written","typical_offset_days_from_first":0},{"milestone_id":"result_declared","name_en":"Result declared","typical_offset_days_from_first":60},{"milestone_id":"enrollment","name_en":"Enrollment / admission taken up","typical_offset_days_from_first":150},{"milestone_id":"completion","name_en":"Program completion / degree conferral","typical_offset_days_from_first":730}]',
    'completion',
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["admit card/scorecard","admission letter","degree/certificate"],"self_report_risk":"low","notes":"Matches BRIEF_D4A Lane A-2''s worked example verbatim (exam-written -> result -> enrollment -> completion)."}',
    false,
    '[{"criterion_id":"declined_or_non_completion","description":"An admission that was declined, or a program left incomplete, never reaches the completion milestone. Score only the milestones actually reached; never impute completion for a declined or partial chain."}]'),

  ('exam_outcome', 'point', NULL, NULL, NULL,
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["scorecard","result notification"],"self_report_risk":"low","notes":null}',
    false, '[]'),

  ('marriage', 'point', NULL, NULL, NULL,
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["marriage certificate","ceremony record"],"self_report_risk":"low","notes":"Recorded at ceremony-date granularity in the live LEL; a future v2 could split into a chain (engagement -> ceremony -> registration) if per-milestone dates become available."}',
    false, '[]'),

  ('romantic_start', 'point', NULL, NULL, NULL,
    '{"valence":"gain","externally_verifiable":false,"verification_sources":[],"self_report_risk":"high","notes":"Private relationship status; no external corroboration path exists in the general case."}',
    true, '[]'),

  ('separation', 'chain',
    NULL,
    '[{"milestone_id":"physical_separation","name_en":"Physical/practical separation","typical_offset_days_from_first":0},{"milestone_id":"legal_filing","name_en":"Legal filing","typical_offset_days_from_first":180},{"milestone_id":"final_decree","name_en":"Final decree / legal dissolution","typical_offset_days_from_first":540}]',
    'final_decree',
    '{"valence":"loss","externally_verifiable":true,"verification_sources":["legal filing record","final decree"],"self_report_risk":"moderate","notes":"BRIEF_D4A Lane A-2''s own divorce-chain worked example; final_decree is the irreversibility milestone."}',
    false, '[]'),

  ('childbirth', 'point', NULL, NULL, NULL,
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["birth certificate","hospital record"],"self_report_risk":"low","notes":null}',
    false, '[]'),

  ('parental_event', 'interval', '{"min_days":14,"typical_days":180,"max_days":3650}', NULL, NULL,
    '{"valence":"mixed","externally_verifiable":true,"verification_sources":["medical record (via family)","family testimony"],"self_report_risk":"moderate","notes":"Onset date of a parent''s condition is frequently reported at a delay from the family; interval-shaped to honor that fuzz."}',
    false, '[]'),

  ('bereavement', 'point', NULL, NULL, NULL,
    '{"valence":"loss","externally_verifiable":true,"verification_sources":["death certificate"],"self_report_risk":"low","notes":"Death date is the least ambiguous point-class event in the ontology; NOT self-report-discriminated."}',
    false, '[]'),

  ('major_gain', 'interval', '{"min_days":14,"typical_days":90,"max_days":365}', NULL, NULL,
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["bank credit record","payment receipt","settlement statement"],"self_report_risk":"low","notes":"DR-13-ratified windfall reclassification: a payment FLOW over a window, not a single asserted day. Distinct evidence signature from major_loss (gain vs loss)."}',
    false, '[]'),

  ('major_loss', 'interval', '{"min_days":1,"typical_days":60,"max_days":365}', NULL, NULL,
    '{"valence":"loss","externally_verifiable":true,"verification_sources":["brokerage/loss statement","insurance claim record","asset valuation record"],"self_report_risk":"low","notes":"Market/investment/asset loss with a documentary trail — distinct from financial_deception, whose evidence is typically self-report-only until corroborated."}',
    false, '[]'),

  ('property_acquisition', 'point', NULL, NULL, NULL,
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["deed registration","sale agreement"],"self_report_risk":"low","notes":null}',
    false, '[]'),

  ('relocation', 'interval', '{"min_days":14,"typical_days":240,"max_days":3650}', NULL, NULL,
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["visa/travel record","address-change record"],"self_report_risk":"low","notes":"Live LEL records this as a start/return pair (residential+travel/foreign_move_start, /foreign_return) — modeled as an interval between those two dates."}',
    false, '[]'),

  ('foreign_settlement', 'chain',
    NULL,
    '[{"milestone_id":"departure","name_en":"Departure","typical_offset_days_from_first":0},{"milestone_id":"arrival","name_en":"Arrival","typical_offset_days_from_first":1},{"milestone_id":"residency_established","name_en":"Durable residency established","typical_offset_days_from_first":365}]',
    'residency_established',
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["visa/residency permit","address record"],"self_report_risk":"low","notes":"residency_established is a PRACTICAL/SOCIAL irreversibility point, not a legal one — settlement is reversible in principle; the milestone marks durable establishment, distinguishing this chain from the reversible relocation interval."}',
    false, '[]'),

  ('illness_acute', 'point', NULL, NULL, NULL,
    '{"valence":"loss","externally_verifiable":true,"verification_sources":["medical record","hospital admission record"],"self_report_risk":"low","notes":null}',
    false, '[]'),

  ('chronic_onset', 'interval', '{"min_days":1,"typical_days":60,"max_days":365}', NULL, NULL,
    '{"valence":"loss","externally_verifiable":true,"verification_sources":["diagnosis record"],"self_report_risk":"low","notes":"Diagnosis date usually lags true symptom onset; interval-shaped to honor that fuzz rather than asserting a single onset day."}',
    false, '[]'),

  ('surgery', 'point', NULL, NULL, NULL,
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["medical/procedure record"],"self_report_risk":"low","notes":null}',
    false, '[]'),

  ('spiritual_turn', 'interval', '{"min_days":7,"typical_days":120,"max_days":730}', NULL, NULL,
    '{"valence":"gain","externally_verifiable":false,"verification_sources":["dated ritual/initiation record where one exists"],"self_report_risk":"high","notes":"Devotional-intensity shifts with no externally observable marker are internal-state reports."}',
    true,
    '[{"criterion_id":"internal_state_only","description":"A devotional/practice-intensity shift with no externally observable marker (no dated initiation, no new ritual infrastructure) is diagnostic-battery-only, never primary hit-rate scoring."}]')
) AS v(event_class_id, temporal_shape, duration_prior, milestone_template, irreversibility_milestone,
       evidence_requirements, self_report_non_discriminating, kill_switch_criteria)
WHERE t.event_class_id = v.event_class_id;

-- ── INSERT: 5 new classes closing the live-data coverage gap ──────────────────────────────────
-- Live coverage check (2026-07-19, chart 482012f1, 57 rows): categories 'creative', 'psychological',
-- 'other', and the self-report-only subset of 'loss' (financial_deception) had NO existing class.
-- signature_model for these 5 rows is PROVISIONALLY inherited from the nearest existing class
-- ("provisional": true) — a dedicated Jyotish-domain pass to refine houses/lords/karakas for these
-- 5 classes is an open item, not silently presented as an equally-verified prior (B.10 discipline).

INSERT INTO brahma_event_ontology
  (event_class_id, name_en, domain, lel_category, signature_model, magnitude_floor, adjacency,
   base_rate_by_age, matching_rules, citations, version,
   temporal_shape, duration_prior, milestone_template, irreversibility_milestone,
   evidence_requirements, self_report_non_discriminating, kill_switch_criteria)
VALUES
  ('achievement_recognition', 'Achievement / Recognition', 'general', 'creative',
    '{"provisional":true,"inherited_from":"career_advancement","houses":["10","11","5"],"lords":["10L","11L","5L"],"karakas":["Sun","Mercury"],"vargas":["D10"],"dasha_rules":"benefic 10/11/5 dasha","transit_triggers":"Jupiter transit to 10th/11th/5th"}',
    'moderate', '["career_advancement"]',
    '{"band_0_12":0.02,"band_13_25":0.30,"band_26_40":0.40,"band_41_60":0.20,"band_60_plus":0.05}',
    '{"lel_domain_patterns":["career/award_selection","creative/award","creative/modeling","education/leadership_role"]}',
    ARRAY['BPHS ch.10 (karma-bhava)','Phaladeepika ch.10 (inherited — provisional pending dedicated sourcing)'],
    '2.0',
    'point', NULL, NULL, NULL,
    '{"valence":"gain","externally_verifiable":true,"verification_sources":["award/selection notice from issuing institution","published credit/byline"],"self_report_risk":"low","notes":"Institution-issued recognition; covers career awards, creative awards, and formal leadership-role appointments alike."}',
    false, '[]'),

  ('financial_deception', 'Financial Deception / Fraud Loss', 'wealth', 'loss',
    '{"provisional":true,"inherited_from":"major_loss","houses":["2","11","12"],"lords":["2L/11L afflicted","12L active"],"karakas":["Rahu","Saturn"],"vargas":["D2"],"dasha_rules":"adverse dasha for 2nd/11th with Rahu involvement","transit_triggers":"adverse Rahu/Saturn transit to 2nd or 11th"}',
    'significant', '["major_loss"]',
    '{"band_0_12":0.00,"band_13_25":0.10,"band_26_40":0.35,"band_41_60":0.35,"band_60_plus":0.20}',
    '{"lel_domain_patterns":["loss/financial_deception"]}',
    ARRAY['BPHS ch.12 (vyaya) — inherited from major_loss, provisional pending dedicated sourcing'],
    '2.0',
    'interval', '{"min_days":1,"typical_days":60,"max_days":365}', NULL, NULL,
    '{"valence":"loss","externally_verifiable":false,"verification_sources":["police complaint/FIR where filed","court filing where one exists","counterparty admission"],"self_report_risk":"high","notes":"Distinct evidence signature from major_loss: a fraud/deception claim is typically the native''s private account only, unlike a brokerage/insurance-documented market loss."}',
    true,
    '[{"criterion_id":"unresolved_allegation","description":"A deception claim with no external corroboration (no police report, no court filing, no counterparty admission) is SELF-REPORT-ONLY: diagnostic-battery-only until corroborated, never primary hit-rate scoring."}]'),

  ('psychological_arc', 'Psychological / Speech-Pattern Arc', 'character', 'psychological',
    '{"provisional":true,"inherited_from":"chronic_onset","houses":["1","6","12"],"lords":["1L","6L"],"karakas":["Moon","Mercury","Saturn"],"vargas":["D1"],"dasha_rules":"Saturn/Moon-afflicted dasha","transit_triggers":"adverse Saturn/Moon transit to lagna"}',
    'moderate', '["chronic_onset"]',
    '{"band_0_12":0.10,"band_13_25":0.20,"band_26_40":0.25,"band_41_60":0.25,"band_60_plus":0.20}',
    '{"lel_domain_patterns":["psychological/chronic_episode","psychological/speech_pattern_arc","other/psychological_shift"]}',
    ARRAY['BPHS ch.1 (lagna, temperament) — inherited from chronic_onset, provisional pending dedicated sourcing'],
    '2.0',
    'interval', '{"min_days":14,"typical_days":180,"max_days":1825}', NULL, NULL,
    '{"valence":"mixed","externally_verifiable":false,"verification_sources":["clinical/therapy record where one exists"],"self_report_risk":"high","notes":"Internal psychological state, generally unverifiable externally except where a clinical record exists."}',
    true,
    '[{"criterion_id":"congenital_onset","description":"A condition present since birth (e.g. congenital stammering, per the native-ratified date-tightening correction) has no discrete astrological trigger window and MUST NOT be scored against any timing model — there is no onset transit to match."}]'),

  ('birth_anchor', 'Birth (Subject''s Own, Chart Epoch)', 'transition', 'other',
    '{"provisional":true,"inherited_from":null,"houses":["1"],"lords":["1L"],"karakas":["Sun"],"vargas":["D1"],"dasha_rules":null,"transit_triggers":null}',
    'life_altering', '[]',
    '{"band_0_12":1.00,"band_13_25":0.00,"band_26_40":0.00,"band_41_60":0.00,"band_60_plus":0.00}',
    '{"lel_domain_patterns":["other/birth"]}',
    ARRAY['n/a — defines the natal epoch, not a classically-timed event'],
    '2.0',
    'point', NULL, NULL, NULL,
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["birth certificate"],"self_report_risk":"none","notes":"The subject''s own birth defines t=0 for the chart; it is not a predictable configuration."}',
    false,
    '[{"criterion_id":"epoch_tautology","description":"The chart''s own birth event is the zero-lag definitional anchor of the natal chart, not a predictable configuration. ALWAYS excluded from lambda_e scoring, the retrodiction harness, and every model contender — scoring it would be tautological, not a measurement."}]'),

  ('travel_event', 'Discrete Travel Event', 'travel', 'travel',
    '{"provisional":true,"inherited_from":"foreign_settlement","houses":["3","9","12"],"lords":["3L","9L"],"karakas":["Moon"],"vargas":["D1"],"dasha_rules":"benefic 3/9/12 transit-dasha","transit_triggers":"benefic transit to 3rd, 9th, or 12th"}',
    'trivial', '["foreign_settlement","relocation"]',
    '{"band_0_12":0.10,"band_13_25":0.35,"band_26_40":0.35,"band_41_60":0.15,"band_60_plus":0.05}',
    '{"lel_domain_patterns":["travel/first_foreign_trip"]}',
    ARRAY['BPHS ch.12 (videsh) — inherited from foreign_settlement, provisional pending dedicated sourcing'],
    '2.0',
    'point', NULL, NULL, NULL,
    '{"valence":"neutral","externally_verifiable":true,"verification_sources":["passport/visa stamp","travel booking record"],"self_report_risk":"low","notes":"Lighter-weight than foreign_settlement: a single dateable trip, not a durable-residency chain."}',
    false, '[]')
ON CONFLICT (event_class_id) DO UPDATE SET
  temporal_shape                  = EXCLUDED.temporal_shape,
  duration_prior                  = EXCLUDED.duration_prior,
  milestone_template               = EXCLUDED.milestone_template,
  irreversibility_milestone        = EXCLUDED.irreversibility_milestone,
  evidence_requirements            = EXCLUDED.evidence_requirements,
  self_report_non_discriminating   = EXCLUDED.self_report_non_discriminating,
  kill_switch_criteria             = EXCLUDED.kill_switch_criteria,
  matching_rules                   = EXCLUDED.matching_rules,
  version                          = EXCLUDED.version;

-- ── version bump: all 27 classes now DR-13-shape-complete at v2.0 ─────────────────────────────

UPDATE brahma_event_ontology SET version = '2.0' WHERE version IN ('1.0', '1.1');

-- ── constraints (validated against the now-fully-backfilled table) ────────────────────────────

ALTER TABLE brahma_event_ontology
  ALTER COLUMN temporal_shape SET NOT NULL;

-- ADD CONSTRAINT has no IF NOT EXISTS form in Postgres; guard each with an existence check so this
-- file is safely re-runnable (surgical-migration idempotency discipline, CLAUDE.md §N.3).
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_event_ontology_temporal_shape_check'
  ) THEN
    ALTER TABLE brahma_event_ontology
      ADD CONSTRAINT brahma_event_ontology_temporal_shape_check
        CHECK (temporal_shape IN ('point', 'interval', 'chain'));
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_event_ontology_shape_data_consistency_check'
  ) THEN
    ALTER TABLE brahma_event_ontology
      ADD CONSTRAINT brahma_event_ontology_shape_data_consistency_check
        CHECK (
          (temporal_shape = 'point'
            AND duration_prior IS NULL AND milestone_template IS NULL AND irreversibility_milestone IS NULL)
          OR (temporal_shape = 'interval'
            AND duration_prior IS NOT NULL AND milestone_template IS NULL AND irreversibility_milestone IS NULL)
          OR (temporal_shape = 'chain'
            AND milestone_template IS NOT NULL AND jsonb_array_length(milestone_template) >= 2)
        );
  END IF;
END $$;

-- irreversibility_milestone, when set, must name a milestone actually in milestone_template.
-- FIX (D-4a Lane A-1, post-merge blocker fix, 2026-07-19): the original form of this constraint
-- used `EXISTS (SELECT 1 FROM jsonb_array_elements(...) ...)` inside a CHECK clause — Postgres
-- does not support subqueries (including set-returning-function-based ones) in CHECK constraints
-- (error 0A000, "cannot use subquery in check constraint"), so this migration failed to apply on
-- every environment that reached it. Rewritten as a pure jsonb containment expression (`@>`),
-- which Postgres DOES allow in a CHECK: jsonb array containment recursively tests whether ANY
-- element of the left array is a superset of the corresponding element of the right array, so
-- `milestone_template @> [{"milestone_id": X}]` is true iff some element of milestone_template
-- has milestone_id = X, regardless of that element's other keys (name_en, typical_offset_days_
-- from_first, ...). Verified live: '[{"milestone_id":"a","name_en":"A"},{"milestone_id":"b",...}]'
-- @> '[{"milestone_id":"b"}]' -> true; a milestone_id absent from the array -> false. Semantically
-- identical to the original EXISTS form, just expressible without a subquery.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_event_ontology_irreversibility_milestone_check'
  ) THEN
    ALTER TABLE brahma_event_ontology
      ADD CONSTRAINT brahma_event_ontology_irreversibility_milestone_check
        CHECK (
          irreversibility_milestone IS NULL
          OR milestone_template @> jsonb_build_array(jsonb_build_object('milestone_id', irreversibility_milestone))
        );
  END IF;
END $$;

-- ── asset_registry bookkeeping: bg_ghatana description now reflects 27 classes + DR-13 shapes ──

UPDATE asset_registry SET
  english_description =
    'Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended '
    '2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requirements, '
    'self_report_non_discriminating flags, kill_switch_criteria) + electional activity ontology '
    '(12 muhurta activity classes). Seeded from W1 seed package Sections 5-6; shape/evidence/'
    'self-report/kill-switch fields added by D-4a Lane A-2. Governs L4 ph_nimitta, L4 ph_muhurta, '
    'the D-4a matcher (A-1), and the D-4a prospective ledger (A-4) claim_shape validation.',
  count_sql = 'SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count'
WHERE asset_id = 'bg_ghatana';

COMMIT;

-- DOWN (manual, if ever needed):
-- BEGIN;
-- ALTER TABLE brahma_event_ontology DROP CONSTRAINT IF EXISTS brahma_event_ontology_irreversibility_milestone_check;
-- ALTER TABLE brahma_event_ontology DROP CONSTRAINT IF EXISTS brahma_event_ontology_shape_data_consistency_check;
-- ALTER TABLE brahma_event_ontology DROP CONSTRAINT IF EXISTS brahma_event_ontology_temporal_shape_check;
-- DELETE FROM brahma_event_ontology WHERE event_class_id IN
--   ('achievement_recognition','financial_deception','psychological_arc','birth_anchor','travel_event');
-- ALTER TABLE brahma_event_ontology
--   DROP COLUMN IF EXISTS temporal_shape,
--   DROP COLUMN IF EXISTS duration_prior,
--   DROP COLUMN IF EXISTS milestone_template,
--   DROP COLUMN IF EXISTS irreversibility_milestone,
--   DROP COLUMN IF EXISTS evidence_requirements,
--   DROP COLUMN IF EXISTS self_report_non_discriminating,
--   DROP COLUMN IF EXISTS kill_switch_criteria;
-- UPDATE brahma_event_ontology SET version = '1.1' WHERE version = '2.0';
-- UPDATE asset_registry SET
--   english_description = 'Life-event ontology (22 classes keyed to LEL categories) + electional '
--     'activity ontology (12 muhurta activity classes). Seeded from W1 seed package Sections 5-6. '
--     'Governs L4 ph_nimitta and ph_muhurta.',
--   count_sql = 'SELECT (SELECT COUNT(*) FROM brahma_event_ontology) + (SELECT COUNT(*) FROM brahma_activity_ontology) AS count'
-- WHERE asset_id = 'bg_ghatana';
-- COMMIT;
