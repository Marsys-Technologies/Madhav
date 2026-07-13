-- Migration 431: bodha_cgm_edges constituent_fact_ids_array — WP-2.3 / LCA-9a-1
-- ============================================================================
-- CGM graph-structure completion (graha↔bhava edges + yoga first-class nodes).
-- Adds a B.3 derivation-ledger column to bodha_cgm_edges: every edge the
-- graph-structure lane emits (lordship / occupancy / bhava_aspect / yoga_member)
-- carries the L1 chart_facts.fact_id(s) it derives from, so the edge's
-- derivation RESOLVES back to chart_facts (CLAUDE.md B.3 / §N.5).
--
-- fact_id in chart_facts is TEXT (16-hex), so this is TEXT[] (not UUID[], which
-- underlying_msr_signal_ids_array uses for signal UUIDs). NULL/empty is allowed
-- for pre-existing edge types (aspect/conjunction/dispositor/argala/*_domain)
-- that cite via citation_ref + underlying_msr_signal_ids_array; the new
-- graph-structure edge types populate it.
--
-- UNAPPLIED — surgical migration authored by the WP-2.3-graph writer lane;
-- applied at the W3 Abhinandan full-cascade rebuild (WP-3.1), never auto/bulk
-- (§N.4 surgical-migrations-only).

BEGIN;

ALTER TABLE bodha_cgm_edges
    ADD COLUMN IF NOT EXISTS constituent_fact_ids_array TEXT[];

COMMENT ON COLUMN bodha_cgm_edges.constituent_fact_ids_array IS
  'B.3 derivation ledger: the L1 chart_facts.fact_id(s) this edge derives from. '
  'Every entry MUST resolve to chart_facts.fact_id (§N.5). Populated by '
  'bo_karanajala for graph-structure edges (lordship=lord_in_house_per_varga D1, '
  'occupancy=graha_position/house_d1, bhava_aspect=aspect_parashari_given, '
  'yoga_member=constituent graha occupancy / bhava lord fact). NULL/empty for '
  'legacy edge types that cite via underlying_msr_signal_ids_array.';

COMMIT;
