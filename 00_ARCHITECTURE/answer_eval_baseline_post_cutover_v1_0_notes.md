---
canonical_id: ANSWER_EVAL_BASELINE_NOTES
version: 1.0
status: STUBBED-PENDING-OPERATOR
generated_at: 2026-05-28T14:55:00Z
related_baseline: 00_ARCHITECTURE/answer_eval_baseline_post_cutover_v1_0.json
artifact: answer_eval_baseline_post_cutover_v1_0_notes
---

# answer:eval post-cutover re-baseline — notes

## Status

**STUBBED.** This file is the schema + operator runbook scaffold for the
post-cutover `answer:eval` baseline. The actual run requires live DB +
LLM credentials and was not executable from the autonomous Conductor
session. The operator must run the command in §Operator runbook and
overwrite the baseline JSON with live metrics.

## Why a baseline now

Per project discipline (Learning Layer rule + CLAUDE.md re-baseline marker
in PROGRAM_STATE §3.dejudge), `answer:eval` is re-baselined **once per
consolidated batch** — never per-PR. Wave-4 closes the platform
modernization arc; the cumulative effect of 3.dejudge (strip
`CONFIDENCE_FLOOR` + LL.1 weights + Pancha-MP consolidation), 3.cutover
(G5b_onfinish), 3.legacy_delete (orchestrator trio deletion), and the
Wave-4 substrate (Memorystore caching + observability + edge hygiene) is
the right window to lock the new reference.

## What the re-baseline will surface (predicted)

1. **Weak-tail signals now surface to synthesis.** Pre-de-judge, the
   `CONFIDENCE_FLOOR=0.6` (default) + `0.35` (finance/wealth) cutoffs in
   `msr_sql.ts` suppressed the long tail. Stripping them was intentional
   per re-baseline marker; expect `signals_surfaced_per_query_mean` to
   rise — INTENDED, not a regression.

2. **Tool-call counts may rise slightly.** With the dejudge surfacing
   more signals, planner-context window may select more diverse tools
   per query. Per-tool latency budgets unchanged.

3. **Calibrated confidence average may dip.** Including weak-tail signals
   pulls the average down. This is the *honest* calibration — the floor
   was hiding it. Learning Layer can later calibrate by formula version
   replay (the calibration stamps wired in commit 1/2 enable this).

## Operator runbook

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
# Prerequisites: Vertex ADC; ANTHROPIC_API_KEY; DATABASE_URL pointing at prod;
#                migration 119 applied.
pnpm tsx scripts/answer_eval.ts --baseline --salience-formula-version=v3.0
```

The script writes the live baseline to
`00_ARCHITECTURE/answer_eval_baseline_post_cutover_v1_1.json` (additive
version bump). Commit it on main with the message:

```
4.learning_loop: live post-cutover answer:eval baseline (v1.1)
```

## Calibration loop wiring

The deterministic-stamp producer (`platform/src/lib/predictions/calibration_producer.ts`)
writes one row to `mcp_predictions` per chat completion, keyed on
`(chart_id, ayanamsha_id, query_hash, salience_formula_version)`. The
calibration stamp is **independent of the LEL serve-time toggle** —
predictions log even with LEL off (LEL is a panel input, not a logging
gate per the brief).

Later, the Learning Layer can replay these stamps under a new
`salience_formula_version` and compare aggregate metrics (signals
surfaced, citation hit-rate, downstream-outcome convergence) to decide
whether the new formula version should become default. The stamp is
the substrate for that calibration loop; the actual learning is M-arc
scope, not Wave-4 scope.
