---
unit: 4.learning_loop
wave: 4
title: Wire prediction logging + answer:eval re-baseline (once, post-cutover)
stream: C
worktree: ../MadhavStreamC
blockedBy: [3.cutover, 4.observability]
on_red: rollback
---

## Context (self-contained)
The deterministic data layer is live; the new pipeline is the default. Wire the substrate for the Learning
Layer so the computed-salience formula can later calibrate over time (master plan Track 5; instrumented-but-
uncalibrated at n=1 per native call). Re-baseline `answer:eval` ONCE for this consolidated batch (per the
project's "once per consolidated batch" discipline — never per-PR).

## Scope
- **Prediction logging:** every adapter `onFinish` writes a row to `mcp_predictions` with the deterministic
  stamp `{chart_id, ayanamsha_id, query_hash, salience_formula_version, model_id, predicted_at_iso}` plus the
  outcome-pending slot. The schema (mig 071) already exists from MCP work — wire the producer.
- **LEL serve-time toggle** must still be respected — predictions log even with LEL OFF (LEL is a panel input,
  not a logging gate).
- **answer:eval re-baseline:** run the existing `scripts/answer_eval.ts` against the new deterministic L2.5 +
  unified contract, ONCE, save the baseline JSON as the post-cutover reference. De-judgment will surface
  previously-floored signals — that is INTENDED; record it explicitly in the re-baseline notes.

## Acceptance criteria (all automated)
1. Every chat completion through the adapter pipeline produces a `mcp_predictions` row (test: 10 queries → 10 rows).
2. answer:eval baseline regenerated and committed as the post-cutover reference (one-shot, not per-PR).
3. LEL toggle off → predictions still log; toggle on → panel reads LEL but predictions are independent.

## must_not_touch
`chart_facts`/`l25_*`, `platform/src/lib/synthesis/panel/**` (active), `platform/python-sidecar/**`.

## Commit cadence / rollback
Commits: (1) prediction-log producer + tests, (2) answer:eval re-baseline run + committed baseline. Rollback
= revert (predictions stop logging — no harm; baseline JSON stays).
