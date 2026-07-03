---
canonical_id: CLAUDECODE_BRIEF_BA_PG_GROUNDING_PROOF
version: 1.0
status: COMPLETE
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program) — for execution by Claude Code in Antigravity
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase PG (grounding proof; gates P0+)
objective: >
  Verify EVERY load-bearing assumption of the unified plan against the LIVE code, live prod DB, live prod
  serving, and the live UI — so no wave executes on stale or assumed information. Output =
  00_ARCHITECTURE/BA_GROUNDING_REPORT_v1_0.md with per-assumption verdict (GROUNDED-TRUE /
  GROUNDED-FALSE-with-correction / BLOCKED-with-reason), evidence (file:line, SQL result, HTTP probe,
  screenshot), and a PLAN-DELTA list (every plan statement that must change). This brief is READ-ONLY
  against prod data (SELECTs + HTTP GETs/tool calls only; the sole write = the report file + a CURRENT_STATE
  append + the G-14 throwaway test asset which is fully removed before close).
may_touch: ["00_ARCHITECTURE/BA_GROUNDING_REPORT_v1_0.md (create)", "00_ARCHITECTURE/CURRENT_STATE_v1_0.md (append)", "G-14 throwaway test asset (create + REMOVE)", "read access everywhere"]
must_not_touch: ["any functional code", "any migration content", "prod data (no DML/DDL beyond G-14's reversible registry row in a transaction or dev-DB equivalent)", "deploys"]
---

# BRIEF BA-PG — GROUNDING PROOF (assumptions → facts, before any wave)

> For every item: record VERDICT + EVIDENCE. Where reality differs from the plan, write the correction in
> the PLAN-DELTA section — do NOT silently proceed. Use prod (`[via: curl_prod | psql_prod | gcloud]`)
> for serving/data items; repo HEAD (post sync-freeze start SHA) for code items.

## G-1 — Serving state (the "17 MB already resolved" class)
(a) `get_domain_reading(482012f1, career)` default call on PROD: measure actual byte size; verify
max_lenses/max_signals_per_lens honored. (b) `assess_career(482012f1)` on PROD: actual byte size; is ANY
cap active on the assess_* path (audit register_d8_assess_domain.ts at HEAD)? (c) `response_format`
digest/summary/full on get_chart_orientation: three DISTINCT payload sizes? (d) cache: repeat identical
call — served_from_cache true? latency delta? (e) error envelope uniformity spot-check (3 tools).

## G-2 — Deploy truth
Cloud Run revision SHA (web + sidecar) vs origin/main HEAD; list any merged-but-undeployed migrations
(scan both migration dirs vs applied-migrations table).

## G-3 — Latency baseline (for the §2.1-1 budget)
p50/p95 over 10 calls each: list_my_charts, get_chart_orientation(summary), get_signals(limit 50),
get_domain_reading(default), assess_career — cold-ish and warm. Record the table; this is the baseline
P0/P2 budgets measure against.

## G-4 — Tool census + wiring matrix
Enumerate ACTUAL registered MCP tools at HEAD (count + list). For each of: get_strength, get_aspects,
get_argala, get_sade_sati, get_dispositors, get_tajik, get_tara_chandra_bala, plus ga_yoga firings,
ga_transit_anchors, ph_rectification, bo_anveshana, bo_chart_gestalt, ka_jivana_parva, ka_tulana,
mi_darshana: state {handler file exists? registered in retrieval registry? exposed as MCP tool? serving
on prod?} — the definitive 4-column wiring matrix that scopes P1.

## G-5 — Data-population facts (live prod DB, SELECT-only)
(a) `mimamsa_insight_units` table exists? rows? (plan says never-migrated). (b) `bodha_cgm_nodes.pagerank_score`
NULL fraction. (c) `kala_activation`/`kala_activation_predicates` row counts for 482012f1. (d) DEFECT-001
live orphan %: sample 1,000 signals' constituent_facts_array vs chart_facts join. (e) `bodha_contradictions`
rows for both charts. (f) LEL: `life_events` count for 482012f1 (plan says 57). (g) current MD/AD derivable:
run the ga_dashas SELECT for today's date. (h) `bodha_chart_gestalt`/`vw_chart_digest` populated?

## G-6 — Layer-scope discipline (unified plan §2.2-1)
From asset_registry: confirm every L0 asset has `scope='global'` AND its tables carry NO chart_id;
every L1–L5 asset `scope='per_chart'` AND tables ARE chart_id-keyed. List ANY exceptions (they become
plan constraints). Confirm global assets are built once, not per-chart, in the build path.

## G-7 — Seamless DAG fold proof (unified plan §2.2-2; the critical dry-run)
In a TRANSACTION (or against the dev DB if the registry is prod-only): register a throwaway asset
`zz_pg_test_probe` (global scope, trivial count_sql, no-op writer conforming to WriterBase) → verify it
(a) appears in the cockpit DAG/asset views WITHOUT any UI code change, (b) is planned by the build
planner in dependency order, (c) builds green via the standard path, (d) then REMOVE it completely
(registry row + writer) and verify clean. If ANY step requires touching orchestrator/planner/cockpit
code → record CONTRACT-VIOLATION and STOP that section.

## G-8 — UI/UX consistency audit (unified plan §2.2-3)
(a) Trace the cockpit asset views: do they render from the registry (sanskrit_name/english_name) or from
any hardcoded map (grep asset_names.ts / ASSET_NAMES usages — which surfaces still use it)? List every
surface that would NOT automatically show a new asset. (b) Confirm the build page tree
(CockpitShell → DataAssetsView → LayerPanel) is registry-driven. (c) Screenshot-or-DOM-check one chart's
build page as the visual baseline. (d) Portal chat: one reading round-trip works + note latency.

## G-9 — Plan-fact residuals
(a) charts.chart_type absent (confirm at HEAD). (b) Next-free migration number across BOTH dirs at HEAD.
(c) W1 judgment seed package present in repo? (plan says missing — Cowork delivers; confirm current
state). (d) Root CLAUDECODE_BRIEF.md status (must be COMPLETE before new briefs). (e) The
BA governing trio committed and at which SHAs (unified plan + BA_MASTER v2.x + RETRIEVAL_MODERNIZATION).

## OUTPUT — BA_GROUNDING_REPORT_v1_0.md
Sections: §1 verdict table (G-1…G-9, every sub-item); §2 EVIDENCE (verbatim probe outputs, file:line,
SQL results, latency table, wiring matrix); §3 PLAN-DELTA (numbered list of every unified-plan /
BA_MASTER / RM-plan statement that reality contradicts, with proposed correction); §4 GO/NO-GO per phase
(P0–P2 scoping now fact-based). Append a CURRENT_STATE entry. **Rule established by this brief: no P0+
brief may cite an assumption not GROUNDED here (or in a later grounding addendum).**

*Acceptance: report exists with zero UNKNOWN verdicts (BLOCKED allowed only with a named blocker);
G-7 dry-run completed + cleaned; CURRENT_STATE appended; status → COMPLETE.*
