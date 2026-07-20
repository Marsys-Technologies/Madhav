-- Migration 460: kala_gochara_windows — D-5 Lane G-4 (Forward sweep + serving)
-- Created: 2026-07-19
--
-- Standing table for the G-4 daily-grid sweep, chart-relative birth -> birth+100y
-- (BRIEF_D5 §6 — uniform horizon, deliberately NOT tied to computed longevity/
-- ayurdaya; using it to bound the sweep would encode a lifespan claim, an Ethical
-- Framework violation). Each row is ONE served window for one (chart, event_class)
-- pair, computed from G-3's lambda_e(t | chart) intensity engine
-- (services/gochara_intensity), consuming G-1's gochara_resonance_map (targets)
-- and G-2's gochara_grammar (configuration sentences + composition operators)
-- read-only.
--
-- SHAPE-AWARE OUTPUT (BRIEF_D5 §3, BINDING): a row's shape mirrors its
-- event_class's brahma_event_ontology.temporal_shape (never more temporal
-- precision than the shape supports):
--   point    -> ONE row per activation: window_start = window_end = peak_date.
--   interval -> ONE row = an elevated-hazard SPAN (window_start < window_end),
--               duration drawn from the ontology's duration_prior, peak_date is
--               the highest-signed-intensity day inside the span (never asserted
--               as a lone point).
--   chain    -> MULTIPLE rows per activation episode, one per milestone_template
--               entry, each scored on its OWN configuration (milestone_id
--               populated); the class's irreversibility_milestone (where the
--               ontology declares one) is flagged via is_irreversibility_milestone.
--
-- PEAK_BASIS PROVENANCE (BRIEF_D5 §4 G-4 row references "per DR-10"): DR-10
-- (DIS.023, DISAGREEMENT_REGISTER_v1_0.md) names three PEAK-MODEL contenders for
-- the T-0/ka_sangam dasha-lord-decomposition retrodiction harness --
-- pratyantar_lord (classical default), midpoint_triangle (DEPRECATED), and
-- transit_kernel -- and mandates that every SERVED peak disclose which of those
-- three (or an honestly-named interim proxy, e.g. ka_sangam's own
-- 'dasha_lord_confluence_v1') produced it. G-4's sweep is NOT one of those three
-- contenders: it is G-3's independent lambda_e(t|chart) transit-intensity engine
-- (PROMISE x PERMISSION x exp(beta*X) - suppression), a DIFFERENT peak model
-- entirely, out of DR-10's original three-way frame. Searched this session for a
-- DR-10 ruling that names a gochara/transit-engine peak-model id explicitly --
-- none found (an honest gap, recorded here rather than silently mislabeling this
-- engine's peak as one of the three DR-10 names). Per DR-10's OWN discipline
-- ("peak-basis provenance mandatory" on every served peak), `peak_basis` on every
-- row is stamped with a NEW, honestly-distinct provenance id
-- ('gochara_lambda_e_v1') so a served row is never confused with a
-- pratyantar_lord/midpoint_triangle/transit_kernel peak — the two engines
-- (T-0/ka_sangam's dasha-decomposition peak-picker vs. this table's transit
-- lambda_e peak) are siblings under DR-10's provenance-disclosure discipline,
-- not the same model.
--
-- Sourced from (read-only consumption, no writes to any of these tables):
--   - gochara_resonance_map (G-1, migration 459) — targets
--   - services/gochara_grammar (G-2) — configuration sentences / composition
--   - services/gochara_intensity (G-3) — lambda_e engine
--   - brahma_event_ontology (migration 388/456) — temporal_shape, duration_prior,
--     milestone_template, irreversibility_milestone
--   - chart_dashas (L1) — birth-year anchor for the sweep horizon
--
-- Writer: ka_gochara_sweep (L3 Kāla, HEAVY — plan_substeps/run_substep,
-- cross-attempt substep resumption via build_substep_progress, migration 436).
--
-- Idempotency: per-chart delete-then-insert (§N.3), scoped per substep to
-- (chart_id, event_class) so a resumed build never re-deletes another
-- already-committed substep's rows.
--
-- ROLLBACK:
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_sweep';
--   DROP TABLE IF EXISTS kala_gochara_windows;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE IF NOT EXISTS kala_gochara_windows (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  temporal_shape TEXT NOT NULL CHECK (temporal_shape IN ('point', 'interval', 'chain')),

  -- Shape-aware window (BRIEF_D5 §3): point rows have window_start=window_end=peak_date;
  -- interval rows have window_start < window_end spanning the elevated-hazard duration;
  -- chain rows are one sub-window per milestone (window_start=window_end=milestone peak_date).
  window_start DATE NOT NULL,
  window_end DATE NOT NULL,
  peak_date DATE NOT NULL,

  -- chain-shape only: which milestone_template entry this row scores. NULL for point/interval.
  milestone_id TEXT,
  is_irreversibility_milestone BOOLEAN NOT NULL DEFAULT FALSE,

  -- lambda_e = PROMISE * PERMISSION * exp(beta_e * X(t)) - suppression, at peak_date.
  signed_intensity NUMERIC NOT NULL,   -- raw_intensity * (-1 if adverse else +1) -- D-2 doctrine
  raw_intensity NUMERIC NOT NULL,      -- unsigned magnitude
  valence TEXT NOT NULL,               -- 'gain'|'loss'|'neutral'|'mixed' (brahma_event_ontology)
  is_adverse BOOLEAN NOT NULL,

  -- Active configuration sentences at peak (G-2's ConfigurationSentence.to-dict list),
  -- each carrying fact_ids grounding references (§B.3 CLAUDE.md).
  active_sentences JSONB NOT NULL DEFAULT '[]'::jsonb,

  -- DR-14 PERMISSION breakdown: which independent timing systems were judged
  -- active at peak_date (services/gochara_intensity/permission.py's SystemContribution list).
  contributing_systems JSONB NOT NULL DEFAULT '[]'::jsonb,

  -- G-2 suppression/vedha-cancellation state at peak (services/gochara_intensity/suppression.py detail).
  suppression_state JSONB NOT NULL DEFAULT '{}'::jsonb,

  -- DR-10 peak-basis provenance (see header note above) — mandatory on every served peak.
  peak_basis TEXT NOT NULL DEFAULT 'gochara_lambda_e_v1',

  calibration_state TEXT NOT NULL DEFAULT 'structural_prior'
    CHECK (calibration_state IN ('structural_prior', 'empirically_calibrated')),
  source TEXT NOT NULL DEFAULT 'live' CHECK (source IN ('live', 'fixture')),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per (chart, event_class, window_start, peak_date, milestone) —
-- milestone_id coalesced so point/interval rows (milestone_id IS NULL) are
-- still unique per window_start/peak_date. A plain table-level UNIQUE
-- constraint cannot target an expression (COALESCE), so this is a unique
-- INDEX; the writer's ON CONFLICT clause targets it by the same expression
-- list (Postgres requires an exact match to infer the arbiter index).
CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_gochara_windows_natural_key
  ON kala_gochara_windows (chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''));

COMMENT ON TABLE kala_gochara_windows IS
  'D-5 Lane G-4: standing table for the birth->birth+100y daily-grid gochara '
  '(transit) intensity sweep. Shape-aware (point/interval/chain per '
  'brahma_event_ontology.temporal_shape, BRIEF_D5 §3 binding). Writer: '
  'ka_gochara_sweep. Read-only consumer of gochara_resonance_map (G-1) + '
  'gochara_grammar/gochara_intensity (G-2/G-3).';

COMMENT ON COLUMN kala_gochara_windows.peak_basis IS
  'DR-10 peak-basis provenance (DIS.023). This table''s peaks come from G-3''s '
  'lambda_e transit-intensity engine, NOT one of DR-10''s three named dasha-'
  'decomposition contenders (pratyantar_lord/midpoint_triangle/transit_kernel) '
  '-- default ''gochara_lambda_e_v1'' names that distinctly, per DR-10''s own '
  '"peak-basis provenance mandatory" discipline. See migration header for the '
  'full honest-gap note (no DR-10 ruling names a gochara-engine peak model '
  'explicitly; this is this lane''s own honestly-disclosed id, not a DR-10 ruling).';

COMMENT ON COLUMN kala_gochara_windows.milestone_id IS
  'chain-shape only (BRIEF_D5 §3): the brahma_event_ontology.milestone_template '
  'entry this row scores. NULL for point/interval rows.';

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_chart_event
  ON kala_gochara_windows (chart_id, event_class);

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_chart_window
  ON kala_gochara_windows (chart_id, window_start, window_end);

CREATE INDEX IF NOT EXISTS idx_kala_gochara_windows_chart_adverse
  ON kala_gochara_windows (chart_id, is_adverse, signed_intensity DESC);

-- ── asset_registry registration ──────────────────────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_gochara_sweep',
    'kala',
    105,
    'Gochara Purah-Sancalana Cakra',
    'Forward Sweep + Serving',
    'D-5 Lane G-4: birth->birth+100y daily-grid gochara (transit) intensity sweep '
    '(lambda_e via G-3''s services/gochara_intensity), shape-aware (point/interval/'
    'chain per brahma_event_ontology). HEAVY writer, per-event-class/decade '
    'sub-stepping with cross-attempt resumption (migration 436). Consumes G-1 '
    'gochara_resonance_map + G-2 gochara_grammar + G-3 gochara_intensity read-only.',
    'postgres_table', 'kala_gochara_windows',
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1',
    NULL,
    0, 'per_chart', true, true, true,
    1800,
    'Kāla', 'L3', 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql              = EXCLUDED.count_sql,
    target_table            = EXCLUDED.target_table,
    has_writer               = EXCLUDED.has_writer,
    has_substeps              = EXCLUDED.has_substeps,
    writer_timeout_seconds     = EXCLUDED.writer_timeout_seconds,
    sort_order                  = EXCLUDED.sort_order,
    english_description          = EXCLUDED.english_description;

UPDATE asset_registry SET depends_on = ARRAY['ka_gochara_resonance']::text[]
WHERE asset_id = 'ka_gochara_sweep';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_sweep';
--   DROP TABLE IF EXISTS kala_gochara_windows;
--   COMMIT;
-- =============================================================================
