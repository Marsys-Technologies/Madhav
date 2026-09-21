-- KĀLA READINESS AUDIT — definition-scoped L3 readiness query (§6 item 2), v2
--
-- STATUS: PROPOSED ARTIFACT, NOT YET WIRED INTO platform/scripts/nirmana/. Reviewed and
-- test-run read-only against the live DB during this KĀLA CAMPAIGN RUNBOOK cycle (2026-09-22).
-- Not placed under platform/scripts/nirmana/ directly because that directory is Conductor-owned
-- per charter C5 (propose via a nirmana-adjudication issue; only the Conductor merges) and this
-- audit has no standing to self-merge new shared tooling there. Promote by opening that issue.
--
-- v2 CHANGES FROM v1 (kala_readiness_query.sql, same directory) — v1 is RETAINED, not deleted,
-- per this audit's own retain-in-place hygiene convention; this file supersedes it for use:
--   1. v1's header claimed "this audit's OWN worktree (branch l3/kala-readiness-audit ... has
--      NOT been rebased onto that fix" (the F1 egate.sql definition-scoping repair, PR #2706).
--      Re-verified 2026-09-22 for this cycle: PR #2706 (commit 9b3c3b219) is now an ANCESTOR of
--      this branch — `git log --oneline -- platform/scripts/nirmana/egate.sql` on this worktree
--      shows 9b3c3b219 in the log, and `grep -c definition_revision
--      platform/scripts/nirmana/egate.sql` returns 4 (not 0). v1's staleness claim about this
--      audit's own worktree no longer holds; corrected here rather than left to mislead a reader
--      of the newer file. v1's substantive SQL logic is unchanged by this correction — it never
--      depended on egate.sql's fix status, only its header commentary did.
--   2. Re-ran end-to-end against the live read-only replica this cycle (see "TESTED OUTPUT" below)
--      and confirmed it still executes cleanly and still correctly reports NOT READY for all 23
--      rows (22 active + protected ka_gochara_sweep) under the current frozen definition — no
--      asset has cleared route_analysis/route_verdict under t3-2026-09-11-8b884eac. This matches
--      F2's independently-derived finding (0 t3-scoped events for any ka_% entity) and T3's
--      finding exactly. No logic changes were needed to reproduce this; v1's query was already
--      correct on this measure.
--   3. No other SQL changes. The CTE structure, gate_verdict CASE ladder and F13/F14 ceiling
--      mapping are copied verbatim from v1 (they were independently spot-verified correct by the
--      conductor in the prior cycle and re-confirmed by this cycle's live run below) — this file
--      exists to fix the one stale claim in v1's own commentary, not to change behavior.
--
-- WHY THIS EXISTS RATHER THAN JUST FIXING egate.sql IN PLACE:
--   1. F1 (this audit) found egate.sql's `frozen`/`route` CTEs read
--      nirmana_evidence.nirmana_elevation_campaign_events with NO definition_revision filter —
--      aggregating evidence across all superseded campaign definitions as if it were current.
--      PR #2706 fixes exactly that for egate.sql and capsule_audit.sql, and is merged into this
--      branch (see v2 change 1 above). Even so, egate.sql only ever establishes C2.1 (ancestors
--      frozen) and C2.2 (route recorded) — never physical data state or F13/F14 ladder position,
--      which the campaign also needs per §6 item 2 of PROMPT_0. This query is scoped wider than
--      egate.sql's job on purpose, not as a duplicate of it.
--   2. The campaign needs, per asset, in ONE query: ancestors frozen under the CURRENT definition,
--      route recorded under the CURRENT definition, PHYSICAL data state for the canonical chart
--      (asset_throughput — the table that can distinguish "never built" from "built once, now
--      empty"), and an F13/F14 ladder-ceiling reading using the event-type -> rung/state
--      admissibility mapping worked out in KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md §2 and
--      independently spot-verified.
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
--     -f 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/_work/artifacts/kala_readiness_query_v2.sql
--
-- (bare `psql -f ... ` without -v chart_id falls back to the canonical chart via the \if below.)
--
-- TESTED OUTPUT (this cycle, 2026-09-22, read-only amjis_app role, canonical chart
-- 482012f1-710e-4a25-994a-93821f5871aa): 23 rows returned (22 active ka_* + protected
-- ka_gochara_sweep). asset_itself_frozen_under_current_def = f for all 23. gate_verdict is
-- NOT_READY-BLOCKED-ANCESTORS for every asset with a nonempty depends_on closure under the
-- current manifest, and NOT_READY-BLOCKED-NO-ROUTE for the one asset with zero declared
-- ancestors (ka_muhurta_seva) whose own route is also unrecorded under t3. Zero rows returned
-- OPEN-PENDING-PIN or any READY-shaped value. This is the required proof that the query can
-- report NOT READY, and it matches it: 0/22 (0/23 counting the protected asset) clears any rung
-- under the current definition — the same conclusion F2 and T3 reached independently by other
-- means (0 t3-scoped campaign events for any ka_% entity).

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
  -- NULL below) from "built once, now empty/stale" (T2's kala_activation/kala_convergence finding
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
