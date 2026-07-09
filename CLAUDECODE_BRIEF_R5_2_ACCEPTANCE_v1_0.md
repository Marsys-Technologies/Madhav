---
canonical_id: CLAUDECODE_BRIEF_R5_2_ACCEPTANCE
version: 1.0
status: READY-FOR-KICKOFF — fully autonomous; security-first ordering; the frozen battery is the
  unchanged gate; conductor HALTS-and-reports rather than lowering any bar
created: 2026-07-09
author: Cowork (Beyond-Acharya program) — the acceptance iteration, native-ratified 2026-07-09
program: closes the gap R5.1 measured honestly (R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md: 23.7% vs ≥90%,
  first true rubric-graded run). Scope = EXACTLY the R5.1 punch-list items 1–6, nothing else.
  Governing law unchanged: design v1.6 + R5.1 acceptance report + R5_AUTHORITY_DOSSIER_v1_0.md.
scope_ruling: two charts (482012f1 + 1c826d5a), MCP channel only. Deferred shelf unchanged and
  untouchable (portal, other charts, rate limiting, branch/frontmatter debt, pool opening).
battery: R5_ANSWER_BATTERY_v1_0.md FROZEN — the ≥90% / 100%-deterministic / all-rubric-floors gate is
  IMMUTABLE. The harness (as fixed in R5.1 — rubric floors enforced, Gemini/DeepSeek grading real) is
  the only accepted grader. Add regression items only.
execution_mode: conductor + isolated-worktree lanes + verifier ring (≠ implementer) + Pratinidhi-R
  (dossier-grounded). Per-phase prod deploys, prod-verified ACs. Terminal worktree/branch cleanup =
  exit gate. HALT: canary regression w/ failed rollback · any chart-data write · any entitlement
  WIDENING · gate-lowering of any kind.
may_touch: ["platform/src/app/api/retrieval/capability/** (the entitlement fix)", "platform/src/lib/retrieval/** (budget extension, dignity field, content depth)", "platform-mcp/src/** (tool wiring)", "eval harness assets (bug fixes only, never grading criteria)", "terraform/scheduler config for the two pending applies", "00_ARCHITECTURE run/acceptance/ledger docs"]
must_not_touch: ["orchestrator + build writers", "chart data (read-only)", "salience/priors/constants (frozen)", "LEL rows", "battery item content/grading", "the deferred shelf"]
---

# BRIEF R5.2 — ACCEPTANCE: close the measured gap, pass the unchanged gate

## A0 — PREFLIGHT
Deploy-truth (both services == HEAD) · canary green vs R5.1 close state · `git status` sweep on
governing artifacts · open R5_2_RUN_LEDGER + opening JL entry (native ratification 2026-07-09).
Record the R5.1 battery scorecard as the BASELINE this run must strictly improve.

## A1 — SECURITY FIRST, ALONE (punch #1; its own phase, its own PR, before anything else)
Add per-call chart entitlement to `/api/retrieval/capability` — the path the flagship instruments use.
Pattern already exists in the primitives route (`authorizeChartAccess` + principal headers); port it,
with an in-process short-TTL cache so the fix does not recreate the S4 gate-stack latency (§23).
Denial returns the R5.1 distinct denial envelope state (never empty, never a leaked status code).
**Gate `[verify-against: prod mcp]`:** battery X-2 re-run against the CAPABILITY path specifically —
unentitled chart_id → clean denial on judgment_query/graha_portrait/pact_query/chart_snapshot; the
native's own calls unaffected; latency delta ≤ +50ms p50 on the C1 gate calls. NOTHING else merges
until A1 is deployed and verified.

## A2 — THE DETERMINISTIC GAP (punch #2, #3, #5 — parallel lanes, non-overlapping files)
1. **Budget/trim discipline estate-wide** (punch #3): every MCP-served tool gets the C1 treatment —
   response ceilings, result_clipper, trim_report, drill_pointers-as-overflow. Kill the 234KB class.
   Sweep method: measure every tool's default-call response size on both charts; any tool > its
   class ceiling gets the discipline; record the before/after table.
2. **Dignity/exaltation on query_chart_facts** (punch #2): computed dignity field served on positional
   rows (source: ga_condition/dignity data already in chart_facts — a join/projection, not new
   computation; cite the fact_ids consumed, trap-1 discipline).
3. **Wire the two orphaned C2 fixes** (punch #5) to public MCP tool names (codegen path, not
   hand-edited shims — §19 discipline).
**Gate:** battery deterministic classes (Q1 + X) re-run → 100% on both charts `[verify-against: mcp]`.

## A3 — CONTENT DEPTH (punch #4; the rubric-floor items)
For each rubric-failing battery item, a root-cause note THEN the fix: missing evidence sections in
composite recipes, thin receipts, absent citations at interpretation intent, hedging miscalibrated
vs epistemic grade. Work is in the SERVING synthesis surfaces (recipe assembly, section content,
citation attachment) — never in the battery, never in stored data. Pratinidhi-R rules on any
astrological judgment (checklist element order, what a complete receipt must narrate) with citations.
**Gate:** every previously-failing rubric item re-graded ≥ its floor by the real grader
(Gemini primary / DeepSeek fallback), spot dual-graded 10%.

## A4 — THE TWO TERRAFORM APPLIES (punch #6)
Apply the panchanga-refresh and canary-battery Cloud Scheduler resources; verify one live scheduled
execution of each (or the soonest schedulable). If the session lacks infra permissions: prepare the
exact commands + plan output, HALT-and-report for the native's 5-minute apply, resume on confirmation
— this is the ONE permitted human touchpoint, infrastructure-permissions only.

## A5 — THE ACCEPTANCE RE-RUN (the unchanged gate)
Full frozen battery + all accumulated regression items, BOTH charts, over the MCP channel, real
rubric grading. **Gate (immutable): ≥90% overall · 100% deterministic Q1/X · every rubric floor ·
zero regressions vs the R5.1 baseline.** If the gate fails again: NO third fix-iteration inside this
run — publish the scorecard, root-cause register, and a scoped R5.3 recommendation, and close
honestly. (One iteration per run keeps every measurement clean of in-run drift.)

## A6 — CLOSE
On PASS: `R5_2_ACCEPTANCE_SEAL_v1_0.md` — the program's acceptance certificate: full scorecard vs all
three baselines (R5 untrusted 36.8% · R5.1 true 23.7% · this run), token/latency/call tables, honest
residuals, deferred shelf restated. Program state → **ACCEPTED FOR DAILY MCP USE (two charts)**.
CURRENT_STATE + SESSION_LOG + ledger close · worktrees/branches cleaned (exit gate) · final report.
On FAIL: the honest-close variant per A5. Either way: usage guide updated if any tool contract moved.

## Anti-goals
NO gate-lowering, battery-editing, or harness-criteria changes (harness BUG fixes allowed, logged,
with before/after proof on an unaffected item). NO scope beyond punch 1–6. NO entitlement widening.
NO deferred-shelf resurrection. One fix-iteration per run.
