---
lane: D-2
status: verifying
implementer_model: claude-sonnet-5
verifier_model: opus
attempts: 1
---

## Scope

Read-only DB audit (mcp__postgres__query, SELECT-only) to establish whether
any real telemetry exists to ground the cost/latency budgets asserted in
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §14A.2 and §17.4/§17.8. Checked
`pg_tables` for cost/usage/trace/latency-named tables, queried each for row
counts, schema, and (where populated) latency distributions via
`percentile_cont`. Rendered a verdict on assumption A29 per the dispatch —
noting in the finding itself that A29's actual textual content (§1.1/§6.6,
"the instrument can ask" / clarification-as-planner-outcome) is unrelated to
cost/latency, so the load-bearing claim under test is really §14A.2/§17.4/§17.8
(closer to A34, cost governance).

## Findings summary

2 findings, both in `pg1_findings_D-2.jsonl`:

- **PG1-D2-0001** (class: confirmed, severity: high, assumption: A29) — the
  architecture doc's own admission that cost/latency telemetry is absent is
  CONFIRMED and sharpened by direct DB inspection. `pg_tables` scan surfaced
  4 candidate tables: `query_trace_steps` (493 rows, populated), and three
  cost-accounting tables — `llm_usage_events`, `llm_provider_cost_reports`,
  `llm_cost_reconciliation` — all with 0 rows. Even the one populated table's
  `latency_ms` column is NULL on all 493 rows, and `step_type` is `'sql'` for
  every row (no planner/retrieval/synthesis phase tagging). Result: none of
  the six requested metrics (cost per turn by model, cost by phase, planner
  latency distribution, tool-fetch latency distribution, total time-to-answer
  p50/median/p95) are computable from live data today.
- **PG1-D2-0002** (class: new_defect, severity: medium, assumption: NEW) — a
  finding not anticipated by the architecture doc: the cost-accounting schema
  the doc says needs to be *designed* (§14A.2) already exists in the DB
  (`llm_usage_events` has exactly the right columns — tokens, cost, model,
  pipeline_stage, latency_ms) but was never wired into the request path (0
  rows). Changes the remediation scope from "design a schema" to "wire an
  existing, unused one."

## Headline finding

**§14A.2/§17.4/§17.8's cost and latency budgets are genuinely unmeasurable
today — confirmed empirically, not just by absence-of-grep-match.** Schema
exists for cost accounting (`llm_usage_events` et al.) but is 100% unpopulated,
and the one table that IS populated (`query_trace_steps`, 493 rows spanning
2026-07-01→2026-07-18) has its `latency_ms` column NULL on every single row.
Any cost or latency figure asserted elsewhere in planning documents against
these sections is a design target, not a measurement.

## Evidence log

See `pg1_findings_D-2.jsonl` lines 1–2. Key queries (reproduced in the
`evidence` arrays): `pg_tables` scan; `SELECT count(*)` on each of the 4
tables; `information_schema.columns` for `llm_usage_events`; `count(latency_ms)`
vs `count(*)` on `query_trace_steps`; `DISTINCT step_type`.

## Receipt

```json
{"lane":"D-2","verifier_model":"opus","diff_reviewed":"pending",
 "findings":{"emitted":2,"schema_valid":2,"evidence_complete":2},
 "assertions":{"script":"scripts/validate_findings.py","green":["pg1_findings_D-2.jsonl: 0 violations"],"red":[]},
 "scope_warden":"pass","verdict":"ACCEPT","diagnosis":"Read-only DB audit within declared may_touch scope; both findings evidence-complete; A29 dispatch-label mismatch flagged transparently in-finding rather than silently substituted."}
```
