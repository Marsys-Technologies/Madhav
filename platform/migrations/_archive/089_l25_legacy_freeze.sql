-- 089_l25_legacy_freeze.sql
-- Unit 2a — freeze the pre-engine corpus as `provenance.attribution =
-- 'model_attributed'`. Strangler discipline: NEVER delete. The frozen rows
-- remain queryable; new engine-built rows live alongside them keyed by
-- (chart_id, ayanamsha_id).
--
-- After this migration:
--   chart_facts + l25_* rows WITH chart_id IS NULL = legacy / model-attributed
--   chart_facts + l25_* rows WITH chart_id IS NOT NULL = engine-built
--
-- Read-side helpers (views) expose both.
--
-- ROLLBACK: see end of file.

BEGIN;

-- ─── 1. Mark every NULL-chart-id row as model_attributed in its provenance ───
-- chart_facts: provenance is JSONB on the row. Patch in-place.
UPDATE chart_facts
   SET provenance = jsonb_set(
         COALESCE(provenance, '{}'::jsonb),
         '{attribution}',
         '"model_attributed"'::jsonb,
         true
       )
 WHERE chart_id IS NULL
   AND (provenance->>'attribution') IS DISTINCT FROM 'model_attributed';

UPDATE l25_msr_signals
   SET provenance = jsonb_set(
         COALESCE(provenance, '{}'::jsonb),
         '{attribution}',
         '"model_attributed"'::jsonb,
         true
       )
 WHERE chart_id IS NULL
   AND (provenance->>'attribution') IS DISTINCT FROM 'model_attributed';

-- l25_cdlm_links, l25_cgm_nodes, l25_cgm_edges, l25_ucn_sections,
-- l25_rm_resonances: most have a `provenance` slot via their `source_section`
-- + build_id, but no `provenance` JSONB column. We mark them indirectly via a
-- helper attribution view, leaving the row body intact (no schema-disruptive
-- backfill into structural columns).

-- ─── 2. View: chart_facts with attribution tag (engine | model_attributed) ──
CREATE OR REPLACE VIEW v_chart_facts_attributed AS
SELECT
  cf.*,
  CASE
    WHEN cf.chart_id IS NULL THEN 'model_attributed'
    ELSE 'engine'
  END AS attribution
FROM chart_facts cf;

-- ─── 3. View family for L2.5 attributed reads ───────────────────────────────
CREATE OR REPLACE VIEW v_l25_msr_signals_attributed AS
SELECT
  s.*,
  CASE WHEN s.chart_id IS NULL THEN 'model_attributed' ELSE 'engine' END AS attribution
FROM l25_msr_signals s;

CREATE OR REPLACE VIEW v_l25_cdlm_links_attributed AS
SELECT
  l.*,
  CASE WHEN l.chart_id IS NULL THEN 'model_attributed' ELSE 'engine' END AS attribution
FROM l25_cdlm_links l;

CREATE OR REPLACE VIEW v_l25_cgm_nodes_attributed AS
SELECT
  n.*,
  CASE WHEN n.chart_id IS NULL THEN 'model_attributed' ELSE 'engine' END AS attribution
FROM l25_cgm_nodes n;

CREATE OR REPLACE VIEW v_l25_cgm_edges_attributed AS
SELECT
  e.*,
  CASE WHEN e.chart_id IS NULL THEN 'model_attributed' ELSE 'engine' END AS attribution
FROM l25_cgm_edges e;

CREATE OR REPLACE VIEW v_l25_rm_resonances_attributed AS
SELECT
  r.*,
  CASE WHEN r.chart_id IS NULL THEN 'model_attributed' ELSE 'engine' END AS attribution
FROM l25_rm_resonances r;

CREATE OR REPLACE VIEW v_l25_ucn_sections_attributed AS
SELECT
  u.*,
  CASE WHEN u.chart_id IS NULL THEN 'model_attributed' ELSE 'engine' END AS attribution
FROM l25_ucn_sections u;

COMMIT;

-- ROLLBACK
-- BEGIN;
-- DROP VIEW IF EXISTS v_l25_ucn_sections_attributed;
-- DROP VIEW IF EXISTS v_l25_rm_resonances_attributed;
-- DROP VIEW IF EXISTS v_l25_cgm_edges_attributed;
-- DROP VIEW IF EXISTS v_l25_cgm_nodes_attributed;
-- DROP VIEW IF EXISTS v_l25_cdlm_links_attributed;
-- DROP VIEW IF EXISTS v_l25_msr_signals_attributed;
-- DROP VIEW IF EXISTS v_chart_facts_attributed;
-- -- (We do NOT roll back the provenance.attribution patches — they are idempotent.)
-- COMMIT;
