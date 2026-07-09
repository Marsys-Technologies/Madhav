---
canonical_id: R5_2_ACCEPTANCE_HONEST_CLOSE
version: 1.0
status: CLOSED — honest result; program status is "materially hardened, re-measured, NOT fully
  ACCEPTED" (A5 acceptance gate NOT MET)
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_2_ACCEPTANCE_v1_0.md)
program: closes the gap R5.1 measured honestly (R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md: 23.7% vs
  >=90%). Scope = exactly the R5.1 punch-list items 1-6.
full_run_ledger: 00_ARCHITECTURE/R5_2_RUN_LEDGER_v1_0.md (append-only, full per-phase detail)
---

# R5.2 ACCEPTANCE ITERATION — HONEST CLOSE

## §1 — What this run was

A fully autonomous, six-phase run (A1 security-first → A2 three parallel lanes → A3 content depth
→ A4 the two Terraform applies → A5 the acceptance re-run → A6 close) closing exactly the six
punch items R5.1 measured and left open, per `CLAUDECODE_BRIEF_R5_2_ACCEPTANCE_v1_0.md`. Every
phase deployed to prod and was live-verified before the next began. Two live-verification passes
caught real bugs in this run's own first-attempt fixes (A2's `holistic_bundle_chart_facts` trim
reading the wrong nested JSON path; A4's scheduler jobs failing 401 despite headers provisioned
exactly as documented) — both root-caused, fixed, and re-verified within the same run rather than
asserted correct on unverified grounds.

**This report gives the honest headline result. It does not round up. Where the gate was not met,
that is stated plainly.**

## §2 — What shipped, deployed, and live-verified on prod

| Phase | What | Verification |
|---|---|---|
| A1 | Per-call chart entitlement gate on `/api/retrieval/capability` (the path every flagship instrument routes through) | Clean `entitlement_denied` denial on all 4 flagship tools for an unentitled chart; native's own calls unaffected; warm p50 335ms vs 826.9ms best-available comparator |
| A2 | Budget discipline on `phala_outlook` (461KB→28KB) and `holistic_bundle_chart_facts` (544KB→866B); dignity field on `query_chart_facts` position rows; `phala_predictive_anchors_get` wired to the R5.1 posterior-provenance fix | Live-verified on prod; one real bug caught and fixed mid-run (trim path) |
| A3 | X-2 (raw status leak) and X-3 (`bodha_signals_get` 234KB→15.9KB) fixed; X-7 confirmed a harness false-negative | Live-verified on prod |
| A4 | Both Cloud Scheduler jobs (`panchanga-daily-refresh`, `canary-battery-daily`) applied; a real auth-header collision found and fixed (`x-marsys-cron-secret` replaces `Authorization`) | Both jobs confirmed executing successfully (200) on a real Cloud Scheduler trigger |
| A5 | Full 38-item battery re-run, both charts, real Gemini/DeepSeek grading | 23.7%→31.6% overall, zero regressions — **gate NOT MET** |

## §3 — The gate: NOT MET

| Criterion | Required | Actual | Met? |
|---|---|---|---|
| Overall pass rate | ≥90% | 31.6% (12/38) | **NO** |
| Q1/X deterministic | 100% | 43.8% (7/16) | **NO** |
| Every rubric floor | all met | 16 of 22 rubric-applicable items still below floor | **NO** |
| Zero regressions vs R5.1 baseline | required | confirmed zero (id-by-id diff) | **YES** |

Full per-item root-cause register (every FAIL traced to a specific cause, not guessed) is in
`R5_2_RUN_LEDGER_v1_0.md` §A5. In summary: 5 items are tight byte-ceiling misses or harness
pattern-strictness false negatives (not product gaps); 1 is a pre-existing documented tool-estate
gap (no vargottama lookup); 1 is a real, scoped, not-yet-fixed content gap (D60 rectification-
confidence note); 16 are genuine content-depth/synthesis-quality shortfalls — the real remaining
acceptance gap, now measured for the first time with real LLM rubric grading applied to *this
run's* fixes.

## §4 — Two genuine adjacent findings, surfaced honestly, not fixed

1. **`query_remedies` (106KB)** — an oversized single result row, not an array-count problem the
   shared trimmer can address. Needs its own shape-specific investigation. Deferred (A2).
2. **`amjis-pending-stream-reaper`** — a pre-existing Cloud Scheduler job, unrelated to R5.2, has
   been silently failing in prod with the identical auth-header collision A4 fixed for its own two
   jobs. Discovered live, confirmed via Cloud Logging, **not fixed** — a different job, out of this
   run's scope. Flagged prominently per this program's own discipline, not buried.

## §5 — Program status

**Materially hardened and honestly re-measured. NOT fully ACCEPTED.** The security gap R5.1 flagged
as its single most consequential finding is closed. Two genuine "234KB-class" tools are fixed. The
dignity-field and posterior-provenance gaps are closed. Both scheduled jobs are live. Overall
battery score improved by 7.9 percentage points with zero regressions. The remaining gap to ≥90% is
real, substantial, and now precisely characterized: 16 rubric-graded content-depth items, each
needing dedicated Pratinidhi-R-grounded synthesis work — not a configuration fix, not something a
single further iteration inside this run should attempt (per the brief's own "one fix-iteration
only" discipline).

## §6 — R5.3 recommendation (scoped)

1. Content-depth pass on the 16 below-floor rubric items — the actual remaining acceptance gap.
2. D60 (and other fine-varga) rectification-confidence note on `query_chart_facts`.
3. `amjis-pending-stream-reaper`'s own `x-marsys-cron-secret` fix (mechanical, proven pattern).
4. `query_remedies` 106KB shape-specific investigation.
5. Native ratification on whether the battery's own byte ceilings (Q1-N-3/N-4/A-3) and regex
   patterns (Q1-A-2/X-7) merit a dedicated harness-hygiene pass — this run's authority does not
   extend to editing frozen battery assertion logic unilaterally.

---

*Full per-phase detail, live gate-check tables, and the complete A5 root-cause register:
`R5_2_RUN_LEDGER_v1_0.md`.*
