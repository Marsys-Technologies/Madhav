-- Migration 462: Vidhi registry seed — VIDHI-PŪRṆATĀ (planner completeness + default-depth)
-- Created: 2026-07-23
--
-- Brings the migration-440 DB seed (the "third copy" of the Vidhi registry) into lockstep
-- with the canonical source platform/src/lib/vidhi/registry_data.ts after the VIDHI-PŪRṆATĀ
-- wave's P-1..P-3b edits. Migration 440 created the schema + asset_registry rows; the row
-- seed itself is authored in bg_vidhi_primitives.py / bg_vidhi_floors.py (Python writers) and
-- mirrored here. This migration re-seeds the three tables to the POST-WAVE registry contents:
--   • 48 vidhi_primitives (was ~37) — adds P-2 spiritual_yoga_scan; P-3 ayurdaya_read /
--     medical_read / upapada_read; P-3b chart_digest_read / yoga_firings_read /
--     gochara_activation_read / gochara_forecast_read / election_read /
--     standing_predictions_read / tail_divergence_read (E-0..E-7 elevation lanes).
--   • 11 vidhi_intent_floors (was 8) — adds P-2 spirituality_deepdive / education_deepdive /
--     progeny_deepdive; general_synthesis floor replaced by the E-0 Pūrṇa-Ādhāra foundation.
--   • 230 vidhi_floor_items — every existing deepdive floor expanded (F2/F3/F4/F7 fixes +
--     the shared E-1/E-2/E-5/E-6/E-7 elevation tail).
--
-- Honesty line (brief §0): every floor item resolves to a live tool OR carries a truthful
-- primitive-level known_gap surfaced in the completeness receipt's `dark` bucket, never faked.
-- New-primitive known_gaps carried through verbatim from the canonical registry:
--   spiritual_yoga_scan → CR-130 · gochara_activation/forecast/election_read → CR-131 ·
--   upapada_read → CR-61.  standing_predictions/tail_divergence/chart_digest/yoga_firings/
--   ayurdaya/medical_read are data-backed (known_gap NULL). Each CR is OPEN/LOGGED per
--   platform/src/lib/vidhi/cr_status.ts (registry_completeness test asserts this).
--
-- §N.3 idempotency (mirrors the Python writers exactly):
--   • vidhi_primitives  → ON CONFLICT (primitive_id) DO UPDATE  (L0 global upsert).
--   • vidhi_intent_floors → ON CONFLICT (intent) DO UPDATE.
--   • vidhi_floor_items → per-intent DELETE-then-INSERT (a floor edit re-numbers item_order,
--     so wholesale replace avoids orphaned rows under stale numbering).
-- Re-runnable: applying twice is a no-op beyond updated_at.
--
-- Schema delta: vidhi_floor_items gains a `hard_floor` column (P-3b §N.6 serving-density
-- signal — FloorItem.hard_floor in the canonical registry). ADD COLUMN IF NOT EXISTS, so this
-- is idempotent and additive; migration 440's schema is otherwise unchanged.
--
-- This migration is DATA + one additive column on Vidhi-owned tables only. It does NOT touch
-- the FROZEN orchestrator/WriterBase, any L1–L5 writer/table, or any calibration table.
--
-- ROLLBACK (manual):
--   BEGIN;
--   -- Re-apply migration 440's writers (bg_vidhi_primitives / bg_vidhi_floors) to restore the
--   -- pre-wave seed, OR DELETE the P-2/P-3/P-3b rows by primitive_id / intent. The added
--   -- column can be dropped: ALTER TABLE vidhi_floor_items DROP COLUMN IF EXISTS hard_floor;
--   COMMIT;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §0 — additive schema: §N.6 serving-density signal column (P-3b) ──
ALTER TABLE vidhi_floor_items ADD COLUMN IF NOT EXISTS hard_floor BOOLEAN NOT NULL DEFAULT false;
COMMENT ON COLUMN vidhi_floor_items.hard_floor IS
    'VIDHI-PŪRṆATĀ P-3b §N.6 serving-density signal (mirrors FloorItem.hard_floor in '
    'platform/src/lib/vidhi/registry_data.ts). true = densest/most-actionable layer of its '
    'band (E-0 digest lead, E-7 insight band) — a budget trim must never sacrifice it first.';

-- ── §1 — vidhi_primitives: upsert all 48 atoms (ON CONFLICT DO UPDATE, L0 idempotency) ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('bhava_condition', 1, 'Full condition of a bhava (house): occupants, lord, aspects received, dignity of occupants.', 'structural', 'ganita_structural_get', '{"chart_id":"{chart_id}","house":"{house}"}'::JSONB,
        'ganita_chart_facts_get(category=bhava)', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('bhavesha_condition', 1, 'Condition of a bhava’s lord (bhāveśa): placement, dignity, strength, aspects on/from it.', 'structural', 'ganita_condition_get', '{"chart_id":"{chart_id}","house":"{house}","mode":"lord"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('karaka_condition', 1, 'Condition of a significator graha (naisargika or chāra kāraka) for the domain in question.', 'structural', 'ganita_condition_get', '{"chart_id":"{chart_id}","karaka":"{karaka}","mode":"karaka"}'::JSONB,
        'ganita_strength_get', NULL, ARRAY[]::TEXT[], ARRAY['CR-36']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('from_moon_view', 1, 'Chandra-lagna re-derivation of house/karaka reads (bhāva reckoned from Moon, not just Lagna).', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","reference_point":"moon"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('varga_ratification', 1, 'Compares D1 promise against operative-varga delivery per bhāveśa/kāraka; fires when dignity flips.', 'signal', 'bodha_signals_get', '{"chart_id":"{chart_id}","signal_type_class":"varga_ratification_divergence"}'::JSONB,
        'ganita_chart_facts_get(divisional_chart={varga})', NULL, ARRAY['varga_ratification_divergence']::TEXT[], ARRAY['CR-36']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('special_lagna_read', 1, 'Reads special lagnas (Indu, Sree, Ghati, Hora, Bhava, etc.) with domain salience.', 'structural', 'ganita_special_lagnas_get', '{"chart_id":"{chart_id}","lagnas":"{lagnas}"}'::JSONB,
        'ganita_special_lagnas_get', 'CR-16', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('chara_karaka_read', 1, 'Reads a chāra kāraka (e.g. Ātmakāraka) placement and condition per Jaimini.', 'structural', 'ganita_condition_get', '{"chart_id":"{chart_id}","mode":"chara_karaka","karaka":"{chara_karaka}"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dhana_yoga_scan', 1, 'Scans the house-lord yoga family for the domain (dhana / raja / Budha-Āditya / Sarasvatī / Lakṣmī).', 'doctrine', 'ganita_yoga_firings_get', '{"chart_id":"{chart_id}","domain":"{domain}","family":"house_lord"}'::JSONB,
        'ganita_yogas_get', 'CR-56', ARRAY[]::TEXT[], ARRAY['CR-27c']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('spiritual_yoga_scan', 1, 'Scans the Jaimini spiritual/renunciate yoga family (pravrajyā, sannyāsa, tāpasa — 4+ grahas in one bhāva, Ketu/Saturn/12th-lord involvement) for the mokṣa domain.', 'doctrine', 'ganita_yoga_firings_get', '{"chart_id":"{chart_id}","domain":"spirituality","family":"spiritual"}'::JSONB,
        'ganita_yogas_get', 'CR-130', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('nbry_scan', 1, 'Nīcha-Bhaṅga (debility cancellation) scan, per-varga (not D1-only).', 'doctrine', 'ganita_yoga_firings_get', '{"chart_id":"{chart_id}","bhanga_active":true}'::JSONB,
        'ganita_condition_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('wealth_loss_mechanism_scan', 1, 'Scans functional-lordship links (dusthana/maraka/badhaka aspects) that constitute a loss mechanism.', 'signal', 'bodha_signals_get', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'judgment_query', NULL, ARRAY[]::TEXT[], ARRAY['CR-27c']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dasha_spine_lord_capability', 1, 'Full daśā spine enriched with per-lord capability (shadbala percentile, house class, functional lordship, ratification factor, warning tier).', 'temporal', 'ganita_dasha_lord_capability_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'ganita_dashas_get', NULL, ARRAY['dasha_lord_capability']::TEXT[], ARRAY['CR-36', 'CR-27a']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('taranga_curve', 1, 'Domain-scoped temporal window bundle (dasha × transit convolution) — full convergence convolution is D-3 (Kāla Taraṅga) scope; this primitive serves the pre-D-3 window bundle.', 'temporal', 'kala_bundle_get', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'kala_windows_get', 'CR-66', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('lel_retrodiction', 1, 'Joins LEL events to the signal/mechanism they retrodictively confirm, served as confirmation only (never as prediction input).', 'temporal', 'mimamsa_lel_query', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'mimamsa_lel_query', 'CR-68', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('intervention_synthesis', 1, 'Leverage-ranked remedy synthesis: domain load-bearing weight ÷ capability, forward-weighted by daśā runway.', 'remedy', 'bodha_remedies_get', '{"chart_id":"{chart_id}","leverage_ranked":true}'::JSONB,
        'bodha_remedies_get', 'CR-69', ARRAY[]::TEXT[], ARRAY['CR-27b']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('positions_snapshot', 1, 'Full natal position snapshot (rasi + degree + nakshatra + retrograde flags, all grahas).', 'structural', 'ganita_positions_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'ganita_positions_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dignity_scan', 1, 'Per-graha dignity (exaltation/own/friend/neutral/enemy/debility) across the chart.', 'strength', 'ganita_condition_get', '{"chart_id":"{chart_id}","mode":"dignity"}'::JSONB,
        'ganita_strength_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('shadbala_rank', 1, 'Ranked shadbala (six-fold strength) across all grahas — authoritative strength ordering.', 'strength', 'ganita_strength_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_chart_digest_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('nakshatra_semantics', 1, 'Nakshatra-semantic layer per graha: own-star, dispositor chains, tara bala, end-degree flags.', 'signal', 'ganita_nakshatra_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_signals_get(signal_type_class=nakshatra_semantic)', 'CR-64', ARRAY[]::TEXT[], ARRAY['CR-27d']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('sensitive_degree_check', 1, 'Sensitive-degree checks (mrityu-bhaga, gandanta, pushkara, kartari, 22nd drekkana) per graha.', 'structural', 'ganita_sensitive_degrees_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'ganita_chart_facts_get', NULL, ARRAY['sensitive_degree']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('divisional_facts', 1, 'Divisional-chart (varga) fact set for a named varga, including D2 varga_hora_class (Surya/Chandra hora semantics).', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","divisional_chart":"{varga}"}'::JSONB,
        NULL, NULL, ARRAY['varga_hora_class']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dasha_window', 1, 'Bounded daśā window query (level-scoped, natally enriched: lord house/dignity/shadbala).', 'temporal', 'ganita_dasha_periods_get', '{"chart_id":"{chart_id}","level":"{level}","start":"{start}","end":"{end}"}'::JSONB,
        'ganita_dashas_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('yoga_activation_scan', 1, 'Yoga activation by daśā — which catalog yogas are dated/active for the query horizon.', 'temporal', 'kala_yoga_activation_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'kala_yoga_activation_get', 'CR-37', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('transit_window_scan', 1, 'Gochara (transit) window scan for a bounded horizon.', 'temporal', 'kala_windows_get', '{"chart_id":"{chart_id}","start":"{start}","end":"{end}"}'::JSONB,
        'ref_planet_transit_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('muhurta_scan', 1, 'Muhurta window scan for an intervention/undertaking horizon.', 'temporal', 'kala_muhurta_get', '{"chart_id":"{chart_id}","start":"{start}","end":"{end}"}'::JSONB,
        'kala_muhurta_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('mechanism_read', 1, 'Named, valenced CGM subgraph read — chain/circuit motifs (e.g. the 10→8→12→10 specimen).', 'signal', 'bodha_graph_subgraph_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_graph_subgraph_get', 'CR-24', ARRAY[]::TEXT[], ARRAY['CR-27c']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('arudha_read', 1, 'Arudha-semantic read: AL conjunctions, A2/A11 placement, AL–bhāva relationships, ranked.', 'signal', 'ganita_condition_get', '{"chart_id":"{chart_id}","mode":"arudha"}'::JSONB,
        'bodha_signals_get(frame=arudha)', 'CR-61', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dosha_scan', 1, 'Per-chart bespoke dosha detection with cancellation/bhaṅga checks.', 'doctrine', 'ref_doshas_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_signals_get(signal_type_class=dosha_label)', 'CR-73', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('statistical_context', 1, 'Within-chart statistical rarity / calibration context for a signal or verdict (L5 structural-mode).', 'utility', 'mimamsa_calibration_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_quality_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('remedy_scan', 1, 'Domain-scoped remedy scan joined to (weakest load-bearing graha × existing sādhana history × daśā runway).', 'remedy', 'bodha_remedies_get', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'ref_remedies_chart_get', 'CR-67', ARRAY[]::TEXT[], ARRAY['CR-27b']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('contradiction_scan', 1, 'Cross-signal contradiction/discovery scan.', 'utility', 'bodha_discoveries_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_signals_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('chalit_cusp_read', 1, 'Chalit (bhāva-cuspal) chart facts: bhava_cusps, house_chalit, sandhi_flag.', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","category":"chalit"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY['chalit_cusp']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('sudarshana_agreement_check', 1, 'Sudarśana-cakra tri-lagna (rasi/Chandra/Sūrya) agreement signal.', 'signal', 'bodha_signals_get', '{"chart_id":"{chart_id}","signal_type_class":"sudarshana_agreement"}'::JSONB,
        'ganita_chart_facts_get', NULL, ARRAY['sudarshana_agreement']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('bhavat_bhavam_check', 1, 'Bhāvāt-bhāvam (house-from-house) amplifier signal.', 'signal', 'bodha_signals_get', '{"chart_id":"{chart_id}","signal_type_class":"bhavat_bhavam_amplifier"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY['bhavat_bhavam']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('bhava_bala_scan', 1, 'Bhāva-bala (house-strength) atoms per house (house_bhava_bala_total).', 'strength', 'ganita_strength_get', '{"chart_id":"{chart_id}","mode":"bhava_bala"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY['bhava_bala']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('ashtakavarga_scan', 1, 'Ashtakavarga bindu-sign scan (ashtakavarga_bindu_sign) per graha/house.', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","category":"ashtakavarga"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY['ashtakavarga_bindu']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('karakamsa_read', 1, 'Karakāṃśa (Ātmakāraka-in-D9) position read.', 'structural', 'ganita_condition_get', '{"chart_id":"{chart_id}","mode":"karakamsa"}'::JSONB,
        'ganita_special_lagnas_get', NULL, ARRAY['karakamsa']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('kp_cusp_sublord_read', 1, 'Real KP cusps + sub-lords (bhāva cuspal sub-lord chain per KP).', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","category":"kp_cusps"}'::JSONB,
        'ganita_structural_get', 'CR-30', ARRAY['kp_cusp_sublord']::TEXT[], ARRAY['CR-36']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('ayurdaya_read', 1, 'Classical longevity (Āyurdāya) computation: Piṇḍa/Aṃśa/Naisarga āyus totals + longevity band (alpāyu/madhyāyu/pūrṇāyu), applicable_method, and the maraka grahas — a longevity-band + maraka-load read, NOT a death prediction.', 'doctrine', 'ganita_ayurdaya_get', '{"chart_id":"{chart_id}"}'::JSONB,
        NULL, NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('medical_read', 1, 'Vaidya-phala medical watch-indications per graha: dosha aggravated (vāta/pitta/kapha), organ_watch, body_part_watch, and indication tier, with BPHS Ch.18 / Aṣṭāṅga Hṛdayam citations. NOT a diagnosis — classical watch-indications only.', 'structural', 'ganita_medical_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'ref_sign_medical_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('upapada_read', 1, 'Upapada Lagna (UL/UPA) read for the marriage/relationship domain: the UPA bhava-arudha position (sign + house) and Arudha A12 (ARUDHA_A12), plus the 2nd-from-UL bhāva as an answerer-side derivation off the UPA house (sustenance / longevity-of-union significator). Raw arudha positions are data-backed; salience ranking is CR-61.', 'signal', 'ganita_condition_get', '{"chart_id":"{chart_id}","facet":"karakas"}'::JSONB,
        'bodha_signals_get(frame=arudha)', 'CR-61', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('chart_digest_read', 1, 'Whole-chart UCD digest (bodha_chart_digest_get): msr_signal/yoga/dosha counts, contradiction_count, weakest_graha (shadbala-derived), composite-ranked entity_profiles (one row per graha and per BHAVA_1..12), convergence_domains, and top signals — the layered digest/rollup that leads the Pūrṇa-Ādhāra foundational floor.', 'structural', 'bodha_chart_digest_get', '{"chart_id":"{chart_id}","mode":"summary"}'::JSONB,
        'get_chart_orientation', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('yoga_firings_read', 1, 'Firings-authoritative yoga surface (ganita_yoga_firings_get): every FIRED yoga for the chart (dhana / raja / nīcha-bhaṅga / pañca-mahāpuruṣa / budha-āditya / sarasvatī …) with fire_reason, per-varga grounds and strength — the "confirmed firings" layer (never a catalog/label match) the whole-chart foundation reads.', 'doctrine', 'ganita_yoga_firings_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'ganita_yogas_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('gochara_activation_read', 1, 'Gochara (D-5) activation view (gochara_activation_get): kala_gochara_windows rows ACTIVE on the current date — "is this event-class configuration firing right now?" over the signed λ_e intensity field, carrying the DR-16 honest-clarity + structural_prior envelope. Bind at horizon=current in every deepdive machine band.', 'temporal', 'gochara_activation_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'kala_windows_get', 'CR-131', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('gochara_forecast_read', 1, 'Gochara (D-5) forecast view (gochara_forecast_get): kala_gochara_windows overlapping a forward date range (point/interval/chain shapes, is_irreversibility_milestone flagged) over the signed λ_e field, DR-16-enveloped — the forward temporal spine. Bind where horizon=multi_year.', 'temporal', 'gochara_forecast_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'kala_windows_get', 'CR-131', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('election_read', 1, 'Gochara (D-5) election-avoidance view (gochara_election_avoidance_get): ADVERSE kala_gochara_windows to avoid for an undertaking, each carrying the full DR-16 payload (clarity_statement, probabilistic framing, falsifier, mitigation-paired BPHS remedy, confidence_disclosure). Bind when the question is an undertaking / timing / muhūrta ask.', 'temporal', 'gochara_election_avoidance_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'kala_muhurta_get', 'CR-131', ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('standing_predictions_read', 1, 'Standing prospective-ledger read (phala_predictive_anchors_get): the OPEN filed predictions for the domain — each with window_start/peak/end, magnitude, confidence band, malleability, a FALSIFIER (deny/confirm observable + evaluation date) and posterior. Makes every reading falsifier-bearing by default. Confirmation/disclosure ONLY — never a calibration write.', 'temporal', 'phala_predictive_anchors_get', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'phala_anchors_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('tail_divergence_read', 1, 'Tail-divergence read (synth_tail_divergence_get): the bottom-decile dissent/tail signals (BA-P4 70/20/10 attention budget) that contradict or diverge from the dominant synthesis — the rarity / "where THIS chart departs from the typical" surface the insight band mines for the non-obvious, beyond-acharya finding.', 'signal', 'synth_tail_divergence_get', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'bodha_discoveries_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

-- ── §2 — vidhi_intent_floors + vidhi_floor_items: 11 floors (per-intent delete-then-insert, L0 floor-content replace) ──
INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('wealth_deepdive', 1, ARRAY['CR-27a', 'CR-27b', 'CR-27c', 'CR-27d', 'CR-36']::TEXT[], 'Flagship floor — worked example per DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3; §G master acceptance target.', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'wealth_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":2}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhavesha_condition', 2, 'acharya_floor', '{"house":2}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'karaka_condition', 3, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'from_moon_view', 4, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'chalit_cusp_read', 5, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhava_bala_scan', 6, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'ashtakavarga_scan', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'sensitive_degree_check', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'divisional_facts', 9, 'acharya_floor', '{"varga":"D2"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'varga_ratification', 10, 'acharya_floor', '{"vargas":["D2","D9","D11"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'karakamsa_read', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'kp_cusp_sublord_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'special_lagna_read', 13, 'acharya_floor', '{"lagnas":["indu","sree"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'chara_karaka_read', 14, 'acharya_floor', '{"chara_karaka":"AmK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'dhana_yoga_scan', 15, 'acharya_floor', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'nbry_scan', 16, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'wealth_loss_mechanism_scan', 17, 'acharya_floor', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'sudarshana_agreement_check', 18, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhavat_bhavam_check', 19, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'nakshatra_semantics', 20, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'dasha_spine_lord_capability', 21, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'taranga_curve', 22, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'intervention_synthesis', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'gochara_activation_read', 24, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'gochara_forecast_read', 25, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'election_read', 26, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'standing_predictions_read', 27, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'lel_retrodiction', 28, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'contradiction_scan', 29, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'tail_divergence_read', 30, 'machine_band', '{"domain":"wealth"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'mechanism_read', 31, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'statistical_context', 32, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('career_deepdive', 1, ARRAY['CR-27c', 'CR-27d']::TEXT[], 'D10/D9 multi-varga per CR-62’s wealth {D1,D2,D9,D11} / career {D1,D9,D10} map (design §12 lord-placement join).', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'career_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":10}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhavesha_condition', 2, 'acharya_floor', '{"house":10}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'karaka_condition', 3, 'acharya_floor', '{"karaka":"sun"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'divisional_facts', 4, 'acharya_floor', '{"varga":"D10"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'divisional_facts', 5, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'varga_ratification', 6, 'acharya_floor', '{"vargas":["D1","D9","D10"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'chalit_cusp_read', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhava_bala_scan', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'ashtakavarga_scan', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'sensitive_degree_check', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'karakamsa_read', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'kp_cusp_sublord_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'sudarshana_agreement_check', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhavat_bhavam_check', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'dhana_yoga_scan', 15, 'acharya_floor', '{"domain":"career","family":"raja"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'nakshatra_semantics', 16, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'chara_karaka_read', 17, 'acharya_floor', '{"chara_karaka":"AmK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'dasha_spine_lord_capability', 18, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'taranga_curve', 19, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'intervention_synthesis', 20, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'gochara_activation_read', 21, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'gochara_forecast_read', 22, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'election_read', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'standing_predictions_read', 24, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'lel_retrodiction', 25, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'contradiction_scan', 26, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'tail_divergence_read', 27, 'machine_band', '{"domain":"career"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'mechanism_read', 28, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'statistical_context', 29, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('health_deepdive', 1, ARRAY['CR-27b']::TEXT[], NULL, now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'health_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":6}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhavesha_condition', 2, 'acharya_floor', '{"house":6}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karaka_condition', 3, 'acharya_floor', '{"karaka":"mars"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dignity_scan', 4, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'sensitive_degree_check', 5, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'divisional_facts', 6, 'acharya_floor', '{"varga":"D6"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dosha_scan', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'varga_ratification', 8, 'acharya_floor', '{"vargas":["D1","D6","D9"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'chalit_cusp_read', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhava_bala_scan', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'ashtakavarga_scan', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karakamsa_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'kp_cusp_sublord_read', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'sudarshana_agreement_check', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhavat_bhavam_check', 15, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'ayurdaya_read', 16, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'medical_read', 17, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhava_condition', 18, 'acharya_floor', '{"house":8}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karaka_condition', 19, 'acharya_floor', '{"karaka":"saturn"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dasha_spine_lord_capability', 20, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'taranga_curve', 21, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'remedy_scan', 22, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'gochara_activation_read', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'gochara_forecast_read', 24, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'election_read', 25, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'standing_predictions_read', 26, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'lel_retrodiction', 27, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'contradiction_scan', 28, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'tail_divergence_read', 29, 'machine_band', '{"domain":"health"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'mechanism_read', 30, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'statistical_context', 31, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('marriage_deepdive', 1, ARRAY['CR-27b']::TEXT[], NULL, now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'marriage_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":7}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhavesha_condition', 2, 'acharya_floor', '{"house":7}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'karaka_condition', 3, 'acharya_floor', '{"karaka":"venus"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'divisional_facts', 4, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'varga_ratification', 5, 'acharya_floor', '{"vargas":["D1","D9"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'dosha_scan', 6, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'karakamsa_read', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'chalit_cusp_read', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_bala_scan', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'ashtakavarga_scan', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'sensitive_degree_check', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'kp_cusp_sublord_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'sudarshana_agreement_check', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhavat_bhavam_check', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_condition', 15, 'acharya_floor', '{"house":2}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_condition', 16, 'acharya_floor', '{"house":8}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'chara_karaka_read', 17, 'acharya_floor', '{"chara_karaka":"DK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'upapada_read', 18, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'dasha_spine_lord_capability', 19, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'taranga_curve', 20, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'remedy_scan', 21, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'gochara_activation_read', 22, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'gochara_forecast_read', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'election_read', 24, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'standing_predictions_read', 25, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'lel_retrodiction', 26, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'contradiction_scan', 27, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'tail_divergence_read', 28, 'machine_band', '{"domain":"marriage"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'mechanism_read', 29, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'statistical_context', 30, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('spirituality_deepdive', 1, ARRAY[]::TEXT[], 'VIDHI-PŪRṆATĀ P-2 [MANDATORY] — mokṣa-domain floor (brief §2 P-2 / §A). H9+H12 + lords, Jupiter(guru)+Ketu(mokṣa) kārakas, AK+karakāṃśa (from-karakāṃśa 12th derived answerer-side), D20, D1/D9/D20 ratification. Jaimini spiritual-yoga scan is DARK (CR-130 — family key absent).', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'spirituality_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":12}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhavesha_condition', 3, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhavesha_condition', 4, 'acharya_floor', '{"house":12}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'karaka_condition', 5, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'karaka_condition', 6, 'acharya_floor', '{"karaka":"ketu"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'chara_karaka_read', 7, 'acharya_floor', '{"chara_karaka":"AK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'karakamsa_read', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'divisional_facts', 9, 'acharya_floor', '{"varga":"D20"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'varga_ratification', 10, 'acharya_floor', '{"vargas":["D1","D9","D20"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'nakshatra_semantics', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'spiritual_yoga_scan', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'sudarshana_agreement_check', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'dasha_spine_lord_capability', 14, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'intervention_synthesis', 15, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'gochara_activation_read', 16, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'gochara_forecast_read', 17, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'election_read', 18, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'standing_predictions_read', 19, 'machine_band', '{"domain":"spirituality"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'lel_retrodiction', 20, 'machine_band', '{"domain":"spirituality"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'contradiction_scan', 21, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'tail_divergence_read', 22, 'machine_band', '{"domain":"spirituality"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'mechanism_read', 23, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'statistical_context', 24, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('education_deepdive', 1, ARRAY[]::TEXT[], 'VIDHI-PŪRṆATĀ P-2 [CANDIDATE] — D24-backed education floor (brief §A). H4+H5+H9 + 4th/5th lords, Mercury(buddhi)+Jupiter(jñāna) kārakas, D24 + D1/D9/D24 ratification. education-scoped taraṅga_curve inherits CR-66 (phala domain anchors zero) — dark, not faked.', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'education_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":4}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhava_condition', 3, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhavesha_condition', 4, 'acharya_floor', '{"house":4}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhavesha_condition', 5, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'karaka_condition', 6, 'acharya_floor', '{"karaka":"mercury"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'karaka_condition', 7, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'divisional_facts', 8, 'acharya_floor', '{"varga":"D24"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'varga_ratification', 9, 'acharya_floor', '{"vargas":["D1","D9","D24"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'nakshatra_semantics', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'dignity_scan', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'sensitive_degree_check', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'dasha_spine_lord_capability', 13, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'taranga_curve', 14, 'machine_band', '{"domain":"education"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'gochara_activation_read', 15, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'gochara_forecast_read', 16, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'election_read', 17, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'standing_predictions_read', 18, 'machine_band', '{"domain":"education"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'lel_retrodiction', 19, 'machine_band', '{"domain":"education"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'contradiction_scan', 20, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'tail_divergence_read', 21, 'machine_band', '{"domain":"education"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'mechanism_read', 22, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'statistical_context', 23, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('progeny_deepdive', 1, ARRAY[]::TEXT[], 'VIDHI-PŪRṆATĀ P-2 [CANDIDATE] — D7-backed progeny floor (brief §A). Spine off H5 + Jupiter (putra-kāraka) + PuK REGARDLESS of the D7 spouse_karya label quirk (P-0 (e): L1 chart_divisionals writer mislabel, must_not_touch; D7 is corroboration only). H5(+H9 5th-from-5th), D7, D1/D9/D7 ratification.', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'progeny_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'bhavesha_condition', 3, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'karaka_condition', 4, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'chara_karaka_read', 5, 'acharya_floor', '{"chara_karaka":"PuK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'divisional_facts', 6, 'acharya_floor', '{"varga":"D7"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'varga_ratification', 7, 'acharya_floor', '{"vargas":["D1","D9","D7"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'dosha_scan', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'dasha_spine_lord_capability', 9, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'remedy_scan', 10, 'machine_band', '{"domain":"progeny"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'gochara_activation_read', 11, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'gochara_forecast_read', 12, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'election_read', 13, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'standing_predictions_read', 14, 'machine_band', '{"domain":"progeny"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'lel_retrodiction', 15, 'machine_band', '{"domain":"progeny"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'contradiction_scan', 16, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'tail_divergence_read', 17, 'machine_band', '{"domain":"progeny"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'mechanism_read', 18, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'statistical_context', 19, 'machine_band', '{}'::JSONB, true);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('structure_read', 1, ARRAY[]::TEXT[], 'Narrow/structure depth — the "show me my D1" canonical example; no machine band (deliberate).', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'structure_read';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('structure_read', 'positions_snapshot', 1, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('structure_read', 'dignity_scan', 2, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('structure_read', 'shadbala_rank', 3, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('structure_read', 'chalit_cusp_read', 4, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('structure_read', 'bhava_bala_scan', 5, 'acharya_floor', '{}'::JSONB, false);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('panoramic_breadth', 1, ARRAY['CR-27a', 'CR-27c', 'CR-27d']::TEXT[], 'The "unleash my financial potential"-shaped wide sweep — domain-agnostic breadth, not depth.', now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'panoramic_breadth';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'positions_snapshot', 1, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'shadbala_rank', 2, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'nakshatra_semantics', 3, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'arudha_read', 4, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'mechanism_read', 5, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'contradiction_scan', 6, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'statistical_context', 7, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('panoramic_breadth', 'dasha_spine_lord_capability', 8, 'machine_band', '{}'::JSONB, false);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('retrieval_only', 1, ARRAY[]::TEXT[], NULL, now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'retrieval_only';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('retrieval_only', 'positions_snapshot', 1, 'acharya_floor', '{}'::JSONB, false);

INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
VALUES ('general_synthesis', 1, ARRAY['CR-27a']::TEXT[], NULL, now())
ON CONFLICT (intent) DO UPDATE SET
    version       = EXCLUDED.version,
    cr27_coverage = EXCLUDED.cr27_coverage,
    notes         = EXCLUDED.notes,
    updated_at    = now();
DELETE FROM vidhi_floor_items WHERE intent = 'general_synthesis';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'chart_digest_read', 1, 'acharya_floor', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'positions_snapshot', 2, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'dignity_scan', 3, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'shadbala_rank', 4, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'bhava_bala_scan', 5, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'bhava_condition', 6, 'acharya_floor', '{"house":1}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'bhavat_bhavam_check', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'sensitive_degree_check', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'chara_karaka_read', 9, 'acharya_floor', '{"chara_karaka":"AK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'karakamsa_read', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'arudha_read', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'upapada_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'yoga_firings_read', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'divisional_facts', 14, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'divisional_facts', 15, 'acharya_floor', '{"varga":"D2"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'divisional_facts', 16, 'acharya_floor', '{"varga":"D10"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'divisional_facts', 17, 'acharya_floor', '{"varga":"D7"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'divisional_facts', 18, 'acharya_floor', '{"varga":"D20"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'dasha_spine_lord_capability', 19, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'gochara_activation_read', 20, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'gochara_forecast_read', 21, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'election_read', 22, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'standing_predictions_read', 23, 'machine_band', '{"domain":"general"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'lel_retrodiction', 24, 'machine_band', '{"domain":"general"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'contradiction_scan', 25, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'tail_divergence_read', 26, 'machine_band', '{"domain":"general"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'mechanism_read', 27, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('general_synthesis', 'statistical_context', 28, 'machine_band', '{}'::JSONB, true);

-- ── §3 — asset_registry target_floor refresh (§N.4: floor = achieved count, never fabricated) ──
-- Migration 440 seeded these two rows with the pre-wave counts (primitives=25, floors=8).
-- Re-baseline to the post-wave achieved counts so the cockpit stats route (which reads
-- count_sql live) is not compared against a stale aspirational floor. Idempotent (fixed value).
UPDATE asset_registry SET target_floor = 48 WHERE asset_id = 'bg_vidhi_primitives';
UPDATE asset_registry SET target_floor = 11 WHERE asset_id = 'bg_vidhi_floors';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE vidhi_floor_items DROP COLUMN IF EXISTS hard_floor;
--   -- To restore the pre-wave seed, re-run bg_vidhi_primitives / bg_vidhi_floors writers
--   -- at their pre-wave revision, or delete the P-2/P-3/P-3b primitives + the three new
--   -- intent floors (spirituality_deepdive, education_deepdive, progeny_deepdive).
--   COMMIT;
-- =============================================================================
