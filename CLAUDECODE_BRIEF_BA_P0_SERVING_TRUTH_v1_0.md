---
canonical_id: CLAUDECODE_BRIEF_BA_P0_SERVING_TRUTH
version: 1.0
status: COMPLETE
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program) — for execution by Claude Code in Antigravity
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P0 (first execution phase; PG grounding folded)
grounding_authority: 00_ARCHITECTURE/BA_GROUNDING_REPORT_v1_0.md — no assumption outside it may be cited
objective: >
  Serving truth: establish the measured latency baseline, close the last serving-integrity gaps
  (assess_* caps, cache contract), disposition the mi_vistara scope violation, and leave the channel
  provably clean so P1 starts from measured reality.
may_touch: ["platform-mcp serving/cap/cache code", "register_d8_assess_domain.ts (caps only)", "mi_vistara registry row / writer scope disposition", "00_ARCHITECTURE/BA_GROUNDING_REPORT (addendum)", "CURRENT_STATE append", "this brief's status"]
must_not_touch: ["retrieval ranking logic (P2)", "any writer computation (P3)", "migrations except a mi_vistara scope fix if chosen", "tool wiring/naming (P1)", "orchestrator/planner/cockpit code"]
---

# BRIEF BA-P0 — SERVING TRUTH + CAPS

## Step 1 — Fresh baseline (PD-8; the blocked PG probes, now with MCP auth)
Re-run G-1 + G-3 + G-8c/d from the PG brief `[verify-against: prod]`:
(a) latency table p50/p95 × {list_my_charts, get_chart_orientation(summary), get_signals(50),
get_domain_reading(default), assess_career} × {cold-ish, warm}; (b) actual payload sizes for
get_domain_reading(default) + assess_career; (c) response_format digest/summary/full → three distinct
sizes; (d) cockpit build page + portal chat round-trip live check. Write results as
`BA_GROUNDING_REPORT_v1_0.md` §5 ADDENDUM — this table is the denominator for every §2.1-1 budget.

## Step 2 — assess_* caps (the one confirmed un-capped path, G-1b)
Apply the F-021R bounding discipline to `register_d8_assess_domain.ts` (all 4 assess_* + any sibling
composite): default token-safe cap + max-param plumbing + drill_pointers for the remainder. AC: assess_career
default ≤ 100k chars on prod, params honored `[verify-against: prod]`.

## Step 3 — Cache contract
`served_from_cache=true` on exact-repeat within TTL; latency delta recorded. If infra prevents it, document
why + file the residual — do not fake the flag. AC `[verify-against: prod]`.

## Step 4 — mi_vistara scope disposition (PD-6)
Choose + implement ONE: (a) migrate scope→'per_chart' (surgical migration, number = max(both dirs)+1); or
(b) keep global + document as a known exception in the registry description + grounding addendum. Match the
table's actual semantics (append-only export ledger keyed by chart — likely (a) is honest). AC: registry
scope matches table reality; exception (if kept) documented.

## Step 5 — Close
CURRENT_STATE append (P0 complete; baseline table reference; program position → P1); SESSION_LOG per
governance; this brief status → COMPLETE.

**Exit gate:** all 53 tools structured-respond within their caps on prod; baseline table exists; cache
verified-or-documented; mi_vistara dispositioned; zero functional/ranking changes made.
