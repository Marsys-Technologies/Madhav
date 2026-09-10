-- NIRMĀṆA campaign — capsule integrity audit
-- Conductor-owned shared campaign tooling (charter C5). Read-only: SELECT only.
--
--   psql "$DATABASE_URL" -f platform/scripts/nirmana/capsule_audit.sql
--
-- This is the Phase-Z 128/128 audit instrument, written early and run continuously so the
-- campaign's terminal claims are checked as they are made rather than all at once at the end.
-- It answers, by SQL and never from any session's narration, three questions:
--
--   §1  Does every frozen asset have a COMPLETE evidence chain behind it?
--   §2  Was the implementer != certifier identity split ever crossed?
--   §3  Where does the campaign actually stand, per layer?
--
-- §1 and §2 are the load-bearing ones: both are written so that a PASS requires a real absence
-- of violations, and both would report a violation if one existed. A audit that could only ever
-- print "clean" would be the §N.8 defect wearing an auditor's coat.

\echo ''
\echo '════ §1 — frozen assets with an INCOMPLETE evidence chain (expect 0 rows) ════'
\echo 'Every asset_frozen must be backed by: a W2 route (analysis + verdict), some terminal'
\echo 'acceptance (rebuild / probe / static / empty / producer_covered / source / retired), and'
\echo 'an integrity_verified. Any row here is a capsule asserting more than its evidence supports.'

WITH ev AS (
  SELECT entity_id, event_type
  FROM nirmana_evidence.nirmana_elevation_campaign_events
  WHERE entity_type = 'asset'
), agg AS (
  SELECT entity_id,
    bool_or(event_type = 'asset_analysis_accepted')       AS w2_analysis,
    bool_or(event_type = 'optimization_verdict_accepted') AS w2_verdict,
    bool_or(event_type = 'integrity_verified')            AS integrity_verified,
    bool_or(event_type = 'asset_frozen')                  AS frozen,
    bool_or(event_type IN ('accepted_rebuild_observed','probe_accepted','static_accepted',
                           'empty_accepted','producer_covered','source_accepted',
                           'retired_with_disposition'))   AS terminal_acceptance
  FROM ev GROUP BY entity_id
)
SELECT entity_id, w2_analysis, w2_verdict, terminal_acceptance, integrity_verified
FROM agg
WHERE frozen AND NOT (w2_analysis AND w2_verdict AND integrity_verified AND terminal_acceptance)
ORDER BY entity_id;

\echo ''
\echo '════ §2 — identity separation: every event vs the identity it required (expect no crossings) ════'
\echo 'server_reconstructed events (integrity_verified, asset_frozen, probe_accepted,'
\echo 'stage_transition_accepted, foundation_lane_accepted) must carry the verifier-side ingress'
\echo 'writer; everything else the executor-side control writer. A crossing is a hard-floor breach'
\echo '(implementer certifying its own asset), not a style issue.'

SELECT
  CASE WHEN event_type IN ('integrity_verified','asset_frozen','probe_accepted',
                           'stage_transition_accepted','foundation_lane_accepted')
       THEN 'verifier' ELSE 'executor' END AS required_identity,
  event_type, source_kind, writer_identity, count(*) AS events,
  CASE
    WHEN event_type IN ('integrity_verified','asset_frozen','probe_accepted',
                        'stage_transition_accepted','foundation_lane_accepted')
      THEN CASE WHEN source_kind = 'server_reconstructed'
                 AND writer_identity = 'nirmana_evidence_ingress_writer'
                THEN 'ok' ELSE '*** CROSSED ***' END
    ELSE CASE WHEN source_kind <> 'server_reconstructed'
               AND writer_identity = 'nirmana_campaign_control_writer'
              THEN 'ok' ELSE '*** CROSSED ***' END
  END AS verdict
FROM nirmana_evidence.nirmana_elevation_campaign_events
GROUP BY 1,2,3,4
ORDER BY verdict DESC, 1, 2;

\echo ''
\echo '════ §3 — campaign position per layer, against the frozen definition ════'

WITH assets AS (
  SELECT a->>'asset_id' AS id, a->>'layer' AS layer
  FROM nirmana_evidence.nirmana_elevation_campaign_definitions d,
       jsonb_array_elements(d.manifest->'assets') a
  WHERE d.definition_status = 'frozen'
), ev AS (
  SELECT entity_id, event_type FROM nirmana_evidence.nirmana_elevation_campaign_events
  WHERE entity_type = 'asset'
)
SELECT
  a.layer,
  count(*)                                                                    AS assets,
  count(*) FILTER (WHERE COALESCE(e.frozen, false))                           AS frozen,
  count(*) FILTER (WHERE COALESCE(e.routed, false)
                     AND NOT COALESCE(e.frozen, false))                       AS routed_not_frozen,
  -- COALESCE is load-bearing, not defensive noise. An asset with NO events at all
  -- yields NULL from the lateral, and `NOT NULL` is NULL, so a bare `NOT e.routed`
  -- silently counts zero -- making a layer that has not started look identical to a
  -- layer that is fully routed. Caught by running this audit against L1-L5 while they
  -- were empty and getting `unrouted = 0` for 88 assets that had never been touched.
  count(*) FILTER (WHERE NOT COALESCE(e.routed, false))                       AS unrouted,
  round(100.0 * count(*) FILTER (WHERE COALESCE(e.frozen, false)) / count(*), 1) AS pct_frozen
FROM assets a
LEFT JOIN LATERAL (
  SELECT bool_or(event_type = 'asset_frozen') AS frozen,
         bool_or(event_type = 'asset_analysis_accepted')
           AND bool_or(event_type = 'optimization_verdict_accepted') AS routed
  FROM ev WHERE ev.entity_id = a.id
) e ON true
GROUP BY ROLLUP (a.layer)
ORDER BY a.layer NULLS LAST;
