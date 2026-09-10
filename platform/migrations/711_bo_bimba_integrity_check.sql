-- 711_bo_bimba_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_bimba. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- bo_bimba writes bodha_cgm_nodes, but it is NOT the only writer of that
-- table -- bo_karanajala back-fills centrality columns on rows bo_bimba
-- already inserted, and other node_type values ('arudha', 'special_lagna')
-- are written by their own emitters entirely outside bo_bimba's remit. So
-- this check is deliberately scoped to what bo_bimba (writers/bo_bimba.py)
-- itself unconditionally guarantees, not the whole table:
--
--   1. graha tiling: exactly 9 node_type='graha' rows per (chart_id,
--      ayanamsha_id) -- the writer's `for graha in KNOWN_GRAHAS:` loop is
--      unconditional (never signal-gated) -- with the exact 9-name set,
--      not just the count (a writer bug dropping one graha and duplicating
--      another would still pass count(*) = 9).
--   2. bhava tiling: exactly 12 node_type='bhava' rows per (chart_id,
--      ayanamsha_id) -- `for h in range(1, 13):` is equally unconditional --
--      with the exact node_subject set '1'..'12'.
--   3. bhava hub_flag TRUTH re-derivation: hub_flag = (node_subject IN
--      ('1','5','9')) -- the writer's own hardcoded trikona-house rule,
--      recomputed here rather than trusted as stored.
--   4. bhava position_in_chart_jsonb->>'house' always equals node_subject
--      (the writer sets both from the same loop variable `h`; they must
--      never drift apart).
--   5. Global distinctness: no duplicate (chart_id, ayanamsha_id,
--      node_type, node_subject) tuple anywhere in bodha_cgm_nodes -- a
--      table-wide invariant regardless of which writer touched a row.
--
-- Deliberately NOT checked, and why: node_type='domain' count. bo_bimba's
-- `for domain in CANONICAL_DOMAINS_SORTED:` loop is equally unconditional
-- in the CURRENT source (13 canonical domains, brahmagyan/domain_
-- vocabulary.py), but live production shows 13 domain nodes only on the
-- canonical chart (482012f1-...) -- the other two charts carry 7, the
-- PRE-G13/PA-4 domain-vocabulary-expansion count (see bo_bimba.py's own
-- comment: "KNOWN_DOMAINS was: [7 domains]... Now: CANONICAL_DOMAINS
-- (frozenset of 13)"). This is real staleness from a chart not yet
-- rebuilt since that vocabulary expansion, not a writer defect -- but it
-- means "exactly 13 domain nodes" is honestly FALSE on 2/3 charts today,
-- so C12 forbids asserting it here (a check that has never been green on
-- current data is a proposal, not a gate). Noted in L2_STATE.md rather
-- than silently worked around. node_type='yoga'/'dosha' counts are
-- genuinely chart-data-dependent (one row per distinct yoga/dosha
-- configuration actually present) and centrality columns are bo_karanajala's
-- write, not bo_bimba's -- both out of this migration's scope.
--
-- Verified live against all three production charts before landing (C12):
-- all five conjuncts evaluate TRUE today.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_cgm_nodes
    WHERE node_type = 'graha'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) != 9
       OR count(DISTINCT node_subject) FILTER (
            WHERE node_subject IN ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')
          ) != 9
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_cgm_nodes
    WHERE node_type = 'bhava'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) != 12
       OR count(DISTINCT node_subject) FILTER (
            WHERE node_subject IN ('1','2','3','4','5','6','7','8','9','10','11','12')
          ) != 12
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_nodes
    WHERE node_type = 'bhava'
      AND hub_flag != (node_subject IN ('1', '5', '9'))
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cgm_nodes
    WHERE node_type = 'bhava'
      AND (position_in_chart_jsonb->>'house') != node_subject
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, node_type, node_subject
    FROM bodha_cgm_nodes
    GROUP BY 1, 2, 3, 4
    HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_bimba';
