-- NIRMĀṆA v2.1 — E-gate batch eligibility (charter C2 + C10)
-- Conductor-owned shared tooling (charter C5). Read-only: no INSERT/UPDATE/DELETE anywhere.
--
-- Usage:  psql "$DATABASE_URL" -v layer=L2 -f platform/scripts/nirmana/egate.sql
--         psql "$DATABASE_URL" -v layer=ALL -f platform/scripts/nirmana/egate.sql
--
-- Reports, for every not-yet-frozen asset in the layer, the two E-gate conditions this query
-- CAN establish:
--   ancestors_frozen  — C2.1, the transitive depends_on closure per the FROZEN definition
--   route_recorded    — C2.2, asset_analysis_accepted AND optimization_verdict_accepted
--
-- It deliberately does NOT report C2.3 (analysis generation-pins still match: writer digest +
-- upstream generation). That condition is a comparison against the pins recorded in your own
-- W1/W2 analysis, which live in your session's artifacts, not in this schema. `gate` below reads
-- OPEN-PENDING-PIN, never OPEN, precisely so this tool cannot be mistaken for a full clearance:
-- an unearned green is exactly what §N.8 forbids. Check your pins, then dispatch.
--
-- Run this ONCE PER LOOP for your whole layer (charter C10 batch variant) — not once per asset.

\if :{?layer} \else \set layer 'ALL' \endif

WITH RECURSIVE assets AS (
  SELECT a->>'asset_id'  AS id,
         a->>'layer'     AS layer,
         a->>'asset_kind' AS kind,
         COALESCE(a->'depends_on','[]'::jsonb) AS deps
  FROM nirmana_evidence.nirmana_elevation_campaign_definitions d,
       jsonb_array_elements(d.manifest->'assets') a
  WHERE d.definition_status = 'frozen'
), edges AS (
  SELECT id, jsonb_array_elements_text(deps) AS dep FROM assets WHERE jsonb_array_length(deps) > 0
), anc AS (
  SELECT id, dep AS ancestor FROM edges
  UNION
  SELECT a.id, e.dep FROM anc a JOIN edges e ON e.id = a.ancestor
), frozen AS (
  SELECT DISTINCT entity_id AS id
  FROM nirmana_evidence.nirmana_elevation_campaign_events
  WHERE event_type = 'asset_frozen' AND entity_type = 'asset'
), route AS (
  SELECT entity_id AS id,
         bool_or(event_type = 'asset_analysis_accepted')       AS analysis_ok,
         bool_or(event_type = 'optimization_verdict_accepted') AS verdict_ok
  FROM nirmana_evidence.nirmana_elevation_campaign_events
  WHERE entity_type = 'asset'
  GROUP BY entity_id
), blocked AS (
  SELECT anc.id, count(*) FILTER (WHERE f.id IS NULL) AS unfrozen_ancestors,
         string_agg(anc.ancestor, ', ' ORDER BY anc.ancestor) FILTER (WHERE f.id IS NULL) AS waiting_on
  FROM anc LEFT JOIN frozen f ON f.id = anc.ancestor
  GROUP BY anc.id
)
SELECT
  a.layer,
  a.id                                        AS asset_id,
  COALESCE(a.kind, '(data)')                  AS kind,
  COALESCE(b.unfrozen_ancestors, 0)           AS unfrozen_ancestors,
  COALESCE(r.analysis_ok, false)              AS w2_analysis,
  COALESCE(r.verdict_ok,  false)              AS w2_verdict,
  CASE
    WHEN COALESCE(b.unfrozen_ancestors,0) > 0 THEN 'BLOCKED-ANCESTORS'
    WHEN NOT (COALESCE(r.analysis_ok,false) AND COALESCE(r.verdict_ok,false)) THEN 'BLOCKED-NO-ROUTE'
    ELSE 'OPEN-PENDING-PIN'
  END                                         AS gate,
  b.waiting_on
FROM assets a
LEFT JOIN blocked b ON b.id = a.id
LEFT JOIN route   r ON r.id = a.id
WHERE a.id NOT IN (SELECT id FROM frozen)
  AND (:'layer' = 'ALL' OR a.layer = :'layer')
ORDER BY
  CASE
    WHEN COALESCE(b.unfrozen_ancestors,0) > 0 THEN 3
    WHEN NOT (COALESCE(r.analysis_ok,false) AND COALESCE(r.verdict_ok,false)) THEN 2
    ELSE 1
  END,
  a.layer, a.id;
