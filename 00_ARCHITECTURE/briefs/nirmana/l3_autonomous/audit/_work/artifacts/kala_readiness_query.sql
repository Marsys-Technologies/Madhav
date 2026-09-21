-- KĀLA READINESS AUDIT — definition-scoped L3 readiness query (§6 item 2)
--
-- STATUS: PROPOSED ARTIFACT, NOT YET WIRED INTO platform/scripts/nirmana/. Reviewed and
-- test-run read-only against the live DB by the KĀLA READINESS AUDIT (2026-09-22); not placed
-- under platform/scripts/nirmana/ directly because that directory is Conductor-owned per charter
-- C5 (propose via a nirmana-adjudication issue; only the Conductor merges) and this audit has no
-- standing to self-merge new shared tooling there. Promote by opening that issue.
--
-- WHY THIS EXISTS RATHER THAN JUST FIXING egate.sql IN PLACE:
--   1. F1 (this audit) found egate.sql's `frozen`/`route` CTEs read
--      nirmana_evidence.nirmana_elevation_campaign_events with NO definition_revision filter —
--      aggregating evidence across all superseded campaign definitions as if it were current.
--      PR #2706 (branch l3/egate-definition-scope) fixes exactly that and MERGED TO MAIN at
--      commit 9b3c3b21970cc4aee4d2edda1b71850b81c89bdf, 2026-09-21T20:08:28Z — confirmed live via
--      `gh pr view 2706 --json state,mergedAt,mergeStateStatus` during this audit cycle. See
--      KALA_CAMPAIGN_RUNBOOK_v1_0.md §1 for the full status writeup, including that this audit's
--      OWN worktree (branch l3/kala-readiness-audit, based on pre-merge main @ 20f4d02dc) has NOT
--      been rebased onto that fix — `grep -c definition_revision platform/scripts/nirmana/egate.sql`
--      in this worktree still returns 0. So even the FIXED egate.sql only ever established C2.1
--      (ancestors frozen) and C2.2 (route recorded) — never physical data state or F13/F14 ladder
--      position, which the campaign also needs per §6 item 2 of PROMPT_0. This query is scoped
--      wider than egate.sql's job on purpose, not as a duplicate of it.
--   2. The campaign needs, per asset, in ONE query: ancestors frozen under the CURRENT definition,
--      route recorded under the CURRENT definition, PHYSICAL data state for the canonical chart
--      (asset_throughput — the table Domain C/T2 confirmed is the only source that can distinguish
--      "never built" from "built once, now empty"), and an F13/F14 ladder-ceiling reading using the
--      event-type -> rung/state admissibility mapping T3 (KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md
--      §2) already worked out and independently spot-verified.
--   3. It must be able to report NOT READY, not merely a less-red "OPEN-PENDING-PIN" — see the
--      gate_verdict CASE below, which adds physical-data-honesty branches egate.sql never had
--      (egate.sql only ever looks at the two campaign-event CTEs; it has no idea a table is empty).
--
-- SCOPING DISCIPLINE (definitions, not inference):
--   - "Current definition" = the row in nirmana_elevation_campaign_definitions with
--     definition_status='frozen', most recent by created_at. There is exactly one such row at any
--     time (t3-2026-09-11-8b884eac as of this audit).
--   - Every event-table read below is filtered `definition_revision = <current_def>` — no
--     aggregation across generations, ever. This is the literal fix for F1's defect class.
--   - F13/F14 ceiling columns follow the admissibility mapping in
--     KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md §2 exactly: only `present`/`qualified` (F13) and
--     `strategy_agreed`/`producer_ready` (F14) have ANY admissible event type today. This query
--     does not invent a `consumed`/`served`/`value_evaluated` reading — those columns are not
--     printed because there is no admissible evidence for them (T3 §4: CONSUMER_INTEGRATED and
--     VALUE_EVALUATED have zero admissible event types in the current schema).
--   - `asset_frozen` is read here ONLY as a boolean "frozen under the current definition" fact —
--     never treated as terminal/consumer-side evidence, per T3 §3's finding that asset_frozen
--     evidences nothing beyond DATA_ACCEPTED.
--
-- Read-only: no INSERT/UPDATE/DELETE/DDL anywhere in this file. Safe against the amjis_app
-- read-only role (source dbenv.sh) with default_transaction_read_only=on.
--
-- Usage:
--   source /Users/Dev/madhav-l3/dbenv.sh
--   psql -Atq -v chart_id="'482012f1-710e-4a25-994a-93821f5871aa'" \
--     -f 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/_work/artifacts/kala_readiness_query.sql
--
-- (bare `psql -f ... ` without -v chart_id falls back to the canonical chart via the \if below.)

\if :{?chart_id} \else \set chart_id '''482012f1-710e-4a25-994a-93821f5871aa'''  \endif

WITH RECURSIVE current_def AS (
  SELECT definition_revision
  FROM nirmana_evidence.nirmana_elevation_campaign_definitions
  WHERE definition_status = 'frozen'
  ORDER BY created_at DESC
  LIMIT 1
), assets AS (
  SELECT a->>'asset_id'   AS id,
         a->>'layer'      AS layer,
         COALESCE(a->'depends_on','[]'::jsonb) AS deps
  FROM nirmana_evidence.nirmana_elevation_campaign_definitions d,
       jsonb_array_elements(d.manifest->'assets') a,
       current_def cd
  WHERE d.definition_revision = cd.definition_revision
    AND a->>'layer' = 'L3'
), edges AS (
  SELECT id, jsonb_array_elements_text(deps) AS dep FROM assets WHERE jsonb_array_length(deps) > 0
), anc AS (
  SELECT id, dep AS ancestor FROM edges
  UNION
  SELECT a.id, e.dep FROM anc a JOIN edges e ON e.id = a.ancestor
), frozen AS (
  -- C2.1-adjacent fact: which ancestors (or the asset itself) are frozen UNDER THE CURRENT
  -- DEFINITION ONLY. This is the exact F1 fix: definition_revision is filtered here.
  SELECT DISTINCT ev.entity_id AS id
  FROM nirmana_evidence.nirmana_elevation_campaign_events ev, current_def cd
  WHERE ev.event_type = 'asset_frozen'
    AND ev.entity_type = 'asset'
    AND ev.definition_revision = cd.definition_revision
), route AS (
  -- C2.2: asset_analysis_accepted + optimization_verdict_accepted, UNDER THE CURRENT DEFINITION.
  SELECT ev.entity_id AS id,
         bool_or(ev.event_type = 'asset_analysis_accepted')       AS analysis_ok,
         bool_or(ev.event_type = 'optimization_verdict_accepted') AS verdict_ok
  FROM nirmana_evidence.nirmana_elevation_campaign_events ev, current_def cd
  WHERE ev.entity_type = 'asset'
    AND ev.definition_revision = cd.definition_revision
  GROUP BY ev.entity_id
), producer_ready AS (
  -- F14 "producer ready" admissible family per KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md §2's
  -- mapping table: accepted_rebuild_observed / integrity_verified / probe_accepted / the
  -- disposition family (producer_covered, empty_accepted, source_accepted, static_accepted).
  -- implementation_accepted and asset_analysis_accepted are explicitly BARRED alone ("code
  -- existence" / commit-only) so they are NOT included here.
  SELECT ev.entity_id AS id,
         bool_or(ev.event_type IN ('accepted_rebuild_observed','integrity_verified','probe_accepted',
                                    'producer_covered','empty_accepted','source_accepted',
                                    'static_accepted')) AS producer_ready_ok
  FROM nirmana_evidence.nirmana_elevation_campaign_events ev, current_def cd
  WHERE ev.entity_type = 'asset'
    AND ev.definition_revision = cd.definition_revision
  GROUP BY ev.entity_id
), blocked AS (
  SELECT anc.id,
         count(*) FILTER (WHERE f.id IS NULL) AS unfrozen_ancestors,
         string_agg(anc.ancestor, ', ' ORDER BY anc.ancestor) FILTER (WHERE f.id IS NULL) AS waiting_on
  FROM anc LEFT JOIN frozen f ON f.id = anc.ancestor
  GROUP BY anc.id
), physical AS (
  -- Per-chart physical build state. Distinguishes "never built for this chart" (no row at all,
  -- NULL below) from "built once, now empty/stale" (T2's kala_activation/kala_convergence finding)
  -- from "genuinely lit with rows" — a distinction F7's row-count census alone cannot make.
  SELECT asset_id, state, rows_written, last_built_at, last_error
  FROM asset_throughput
  WHERE chart_id = (:chart_id)::uuid
)
SELECT
  a.layer,
  a.id                                                    AS asset_id,
  cd.definition_revision                                  AS current_definition,
  COALESCE(b.unfrozen_ancestors, 0)                        AS unfrozen_ancestors_under_current_def,
  b.waiting_on,
  (a.id IN (SELECT id FROM frozen))                        AS asset_itself_frozen_under_current_def,
  COALESCE(r.analysis_ok, false)                            AS route_analysis_under_current_def,
  COALESCE(r.verdict_ok,  false)                            AS route_verdict_under_current_def,
  COALESCE(pr.producer_ready_ok, false)                     AS producer_ready_evidence_under_current_def,
  p.state                                                   AS physical_state,
  p.rows_written                                            AS physical_rows_written,
  p.last_built_at                                           AS physical_last_built_at,
  p.last_error                                              AS physical_last_error,
  -- F13 ceiling: only present/qualified are ever reachable under the current event vocabulary.
  CASE
    WHEN COALESCE(r.verdict_ok, false)   THEN 'qualified'
    WHEN COALESCE(r.analysis_ok, false)  THEN 'present'
    ELSE 'none'
  END                                                        AS f13_rung_ceiling,
  -- F14 ceiling: only strategy_agreed/producer_ready are ever reachable (T3 §4: integrated,
  -- deployed_operationally_accepted, consumer_value_demonstrated, empirically_evaluated all have
  -- zero admissible per-asset event types today).
  CASE
    WHEN COALESCE(pr.producer_ready_ok, false) THEN 'producer_ready'
    WHEN COALESCE(r.verdict_ok, false)         THEN 'strategy_agreed'
    ELSE 'none'
  END                                                        AS f14_state_ceiling,
  -- Gate verdict. Ancestors block first (structural, nothing to do); then route (the campaign's
  -- own work, never gated); then PHYSICAL DATA HONESTY (egate.sql has no equivalent of this —
  -- this is the concrete "must be able to report NOT READY" requirement in §6 item 2); then
  -- freeze status. Never prints a bare "OPEN" or "READY" — same §N.8 discipline as egate.sql's own
  -- documented reason for never printing "OPEN".
  CASE
    WHEN COALESCE(b.unfrozen_ancestors, 0) > 0
      THEN 'NOT_READY-BLOCKED-ANCESTORS'
    WHEN NOT (COALESCE(r.analysis_ok, false) AND COALESCE(r.verdict_ok, false))
      THEN 'NOT_READY-BLOCKED-NO-ROUTE'
    WHEN p.asset_id IS NULL
      THEN 'NOT_READY-NEVER-BUILT-FOR-CHART'
    WHEN COALESCE(p.rows_written, 0) = 0
      THEN 'NOT_READY-ZERO-ROWS-FOR-CHART'
    WHEN p.state = 'error'
      THEN 'NOT_READY-BUILD-ERROR'
    WHEN p.state = 'incomplete'
      THEN 'NOT_READY-INCOMPLETE-SUBSTEP-PLAN'
    WHEN p.state = 'stale'
      THEN 'NOT_READY-STALE-DATA'
    WHEN NOT (a.id IN (SELECT id FROM frozen))
      THEN 'NOT_READY-UNFROZEN-UNDER-CURRENT-DEFINITION'
    ELSE 'OPEN-PENDING-PIN'
  END                                                        AS gate_verdict
FROM assets a
CROSS JOIN current_def cd
LEFT JOIN blocked        b  ON b.id = a.id
LEFT JOIN route          r  ON r.id = a.id
LEFT JOIN producer_ready pr ON pr.id = a.id
LEFT JOIN physical       p  ON p.asset_id = a.id
ORDER BY
  CASE
    WHEN COALESCE(b.unfrozen_ancestors, 0) > 0 THEN 5
    WHEN NOT (COALESCE(r.analysis_ok, false) AND COALESCE(r.verdict_ok, false)) THEN 4
    WHEN p.asset_id IS NULL OR COALESCE(p.rows_written,0) = 0 THEN 3
    WHEN p.state IN ('error','incomplete','stale') THEN 2
    ELSE 1
  END,
  a.id;
