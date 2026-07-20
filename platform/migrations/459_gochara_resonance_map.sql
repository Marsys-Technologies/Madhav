-- Migration 459: gochara_resonance_map — G-1 Resonance Map (D-5 Lane G-1)
-- Created: 2026-07-19
-- (Renumbered 458->459: the brief's suggested number collided with a
--  concurrently-landing D-5 lane's platform/supabase/migrations/458_
--  brahma_prospective_ledger.sql — both migration directories share one
--  global numbering sequence, migration-guard flagged the collision, 459
--  is the corrected next-free number.)
--
-- Per-chart × event-class classical-prior-weighted target sets for the gochara
-- (transit) intensity engine (D-5 Lane G-3 consumes this read-only). Every row
-- names ONE target (a bhava, a lord reference, a karaka, a bg_transit_rules
-- mechanism node, a sensitive-degree fact, an arudha pada, a yoga firing, or a
-- dasha-lord portfolio entry) that the event_class's classical signature model
-- resonates through, carrying a weight and a mandatory citation-or-honest-flag.
--
-- Sourced from:
--   - bg_transit_rules (L0, BPHS ch.29 / Phaladeepika ch.26 Gochara rules) — mechanism_node
--   - brahma_event_ontology.signature_model + .citations (migration 388/456) — bhava/lord/karaka
--   - chart_facts (L1, sensitive_degree_check / arudha_pada / yoga_label categories) — sensitive_degree/arudha
--   - ga_yoga_firings (L1, firings-authoritative) — yoga_constituent
--   - chart_dashas (L1, vimshottari MD) — dasha_lord_portfolio
--
-- B.10 (CLAUDE.md): zero fabricated citations. Rows sourced directly from a
-- classically-cited row (bg_transit_rules / brahma_event_ontology.citations)
-- carry that citation verbatim and uncited_extension=false. Rows that connect
-- an event_class to a chart-specific L1 primitive NOT itself keyed to that
-- event_class in the source data (sensitive degrees, arudha padas, yoga
-- firings, dasha-lord portfolios) are this writer's own synthesis: they carry
-- uncited_extension=true, and copy through the underlying primitive's real
-- citation_human text (when present) as supporting context — never a
-- fabricated citation string.
--
-- Writer: ka_gochara_resonance (L3 Kāla). No DAG dependency beyond L0/L1 base
-- data being built (bg_transit_rules, chart_facts, chart_dashas, ga_yoga_firings).
--
-- ROLLBACK:
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_resonance';
--   DROP TABLE IF EXISTS gochara_resonance_map;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

CREATE TABLE IF NOT EXISTS gochara_resonance_map (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,          -- one of brahma_event_ontology's 27 event_class_id values
  target_type TEXT NOT NULL,          -- 'bhava' | 'lord' | 'karaka' | 'mechanism_node' | 'sensitive_degree' | 'arudha' | 'yoga_constituent' | 'dasha_lord_portfolio'
  target_ref TEXT NOT NULL,           -- house number as text, planet/lord-reference name, node id, chart_facts.fact_id, etc. — unique identifier of the target within target_type
  weight NUMERIC NOT NULL,            -- classical-prior weight, see GOCHARA_RESONANCE_MAP_SPEC.md §2 for the scale
  classical_citation TEXT,            -- required UNLESS uncited_extension = true
  uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
  source_rule_id INTEGER REFERENCES bg_transit_rules(id),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(chart_id, event_class, target_type, target_ref)
);

COMMENT ON TABLE gochara_resonance_map IS
  'D-5 Lane G-1: per-chart x event-class classical-prior-weighted target sets '
  '(bhavas, lords, karakas, bg_transit_rules mechanism nodes, sensitive degrees, '
  'arudhas, yoga constituents, dasha-lord portfolios). Consumed read-only by '
  'D-5 Lane G-3''s intensity engine. Writer: ka_gochara_resonance.';

COMMENT ON COLUMN gochara_resonance_map.target_type IS
  'bhava|lord|karaka|mechanism_node|sensitive_degree|arudha|yoga_constituent|dasha_lord_portfolio — see GOCHARA_RESONANCE_MAP_SPEC.md §3.';

COMMENT ON COLUMN gochara_resonance_map.classical_citation IS
  'Mandatory unless uncited_extension=true. Copied verbatim from the source row '
  '(bg_transit_rules.classical_citation, brahma_event_ontology.citations, or an '
  'L1 fact''s citation_human) — never fabricated (B.10).';

-- B.10 invariant: every row carries either a real citation or an explicit honest flag.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'gochara_resonance_map_citation_or_flag'
  ) THEN
    ALTER TABLE gochara_resonance_map
      ADD CONSTRAINT gochara_resonance_map_citation_or_flag
      CHECK (classical_citation IS NOT NULL OR uncited_extension = true);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_gochara_resonance_chart_event ON gochara_resonance_map(chart_id, event_class);

-- ── asset_registry registration ──────────────────────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_gochara_resonance',
    'kala',
    104,
    'Gochara Anunāda Cakra',
    'Resonance Map',
    'D-5 Lane G-1: per-chart x event-class classical-prior-weighted target sets '
    '(bhavas, lords, karakas, mechanism nodes, sensitive degrees, arudhas, yoga '
    'constituents, dasha-lord portfolios) sourced from bg_transit_rules + '
    'brahma_event_ontology + chart-scoped L1 facts. Feeds D-5 Lane G-3''s '
    'transit-intensity engine. Writer: ka_gochara_resonance.',
    'postgres_table', 'gochara_resonance_map',
    'SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=$1',
    NULL,
    0, 'per_chart', true, true,
    'Kāla', 'L3', 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql    = EXCLUDED.count_sql,
    target_table = EXCLUDED.target_table,
    has_writer   = EXCLUDED.has_writer,
    sort_order   = EXCLUDED.sort_order,
    english_description = EXCLUDED.english_description;

UPDATE asset_registry SET depends_on = ARRAY[]::text[]
WHERE asset_id = 'ka_gochara_resonance';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_resonance';
--   DROP TABLE IF EXISTS gochara_resonance_map;
--   COMMIT;
-- =============================================================================
