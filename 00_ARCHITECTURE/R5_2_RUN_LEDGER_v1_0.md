---
canonical_id: R5_2_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_2_ACCEPTANCE_v1_0.md)
program: closes the gap R5.1 measured honestly (R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md: 23.7% vs ≥90%).
  Scope = EXACTLY R5.1 punch-list items 1–6 (A1–A6 per the brief). Governing law unchanged: design
  v1.6 + R5.1 acceptance report + R5_AUTHORITY_DOSSIER_v1_0.md. Battery R5_ANSWER_BATTERY_v1_0.md
  FROZEN — the ≥90%/100%-deterministic/all-rubric-floors gate is immutable.
head_at_a0: 614a885e (R5.1 C5 close commit)
scope: A0 preflight through A6 close, per brief phase order. One fix-iteration per run (brief anti-goal).
---

# R5.2 RUN LEDGER — Acceptance Iteration

Append-only. Every phase's close appends here; this document never edits prior entries.

## JL-000 — Scope ruling recorded (native, 2026-07-09)

**Entry:** the native's message dispatching `CLAUDECODE_BRIEF_R5_2_ACCEPTANCE_v1_0.md` constitutes
the scope ruling and ratification-by-kickoff, per the brief's own frontmatter (`status:
READY-FOR-KICKOFF — fully autonomous`, `program: ... native-ratified 2026-07-09`). Scope = exactly
punch items 1–6 (security entitlement, budget/dignity/orphan-wiring, content depth, the 2 Terraform
applies, the acceptance re-run, close). Deferred shelf unchanged and untouchable per brief frontmatter.

Native's follow-up instruction (same day) ratified full-autonomy execution through A2–A6 with one
explicit completion condition on A1 (latency measurement, below) and reaffirmed: one fix-iteration
only; honest close if the ≥90% gate is not met on the A5 re-run.

**Basis:** brief frontmatter + native dispatch message, 2026-07-09.

---

## A0 — PREFLIGHT — CLOSED, no HALT

Deploy-truth confirmed at kickoff: `main` HEAD `a4029231` (this brief's own commit, local-only —
direct push to protected `main` was rejected, confirming branch-protection posture is intact and
unchanged from R5.1). No uncommitted governing-artifact drift found via `git status`. R5.1 baseline
scorecard (the BASELINE this run must strictly improve): **23.7% overall / 25.0% rubric-only**, per
`R5_1_MCP_CONSUME_ACCEPTANCE_v1_0.md` C4. This ledger opened retroactively at A1 close (native
instruction) rather than pre-A1 — a process gap, noted honestly, not hidden: A0/A1 execution actually
happened before this file existed. No governing-artifact or scope violation resulted from the
ordering gap; the JL-000 ratification and all A1 evidence below are reconstructed from the actual
session transcript, not fabricated after the fact.

---

## A1 — SECURITY FIRST, ALONE — CLOSED, deployed, live-verified

### What shipped
Per-call chart entitlement gate on `/api/retrieval/capability` (the path every MCP flagship
instrument routes through). Previously: zero per-chart authorization on this route — any caller with
a valid `X-MCP-Internal-Token` could reach any `scope: 'per_chart'` capability for any `chart_id`,
regardless of grant. Fix: gate every `per_chart` capability through the existing
`authorizeChartAccess` brain (same one `/api/mcp/primitives/[tool]` already used), keyed off
`X-MCP-User` + `chart_id`, with a 30s in-process cache. Denial returns the R5.1 distinct
`entitlement_denied` envelope — never a bare 401, never an empty-result leak.

Principal (`X-MCP-User`/`X-MCP-Key-Id`) threaded through all ~35 call sites across
`platform-mcp/src/tools/registry_bridge.ts` and the 4 `register_p1_*.ts` files that call this route.
`register_p1_ganita.ts` (the per-chart computed-chart tool group — `ganita_strength_get` etc.)
previously never received `principal` at all — confirms the gap was real and exploitable, not
theoretical.

### Verification (pre-merge)
`tsc --noEmit` clean in `platform` and `platform-mcp`. `platform-mcp` vitest suite diffed against a
clean worktree at the same parent commit: 96/509 pre-existing failures (kala_timeline, phala_outlook,
mimamsa_lel_intake — all sidecar/unrelated tools), zero regressions introduced by this change.

### Deploy
PR #498 merged (squash, commit `6db1415b`) after all 9 CI gates passed (Coverage, Governance,
ICR, Naming Governance, Planner Regression, TypeScript ×2, Unit Tests, Secret Scan). `Deploy to
Cloud Run` workflow run `29012672267`: first attempt queued 15 min with no runner ever assigned
(`runner_id: 0`, empty `steps`) and self-cancelled — a transient CI-infra issue, not a code fault (the
push-triggered `CI — Ganga Quality Gate` run for the same commit had already passed cleanly).
`gh run rerun 29012672267` on retry: both `Build & Deploy Web` and `Build & Deploy MCP` completed
`success`. PR #499 (a standalone docs-only PR for the brief file itself, opened because direct push to
protected `main` was rejected) was closed as redundant once confirmed the file had already reached
`main` as an ancestor commit of #498's squash-merge.

### Live gate check — `[verify-against: mcp]`, prod, both flagship-instrument paths
Foreign/unentitled `chart_id` (`00000000-0000-0000-0000-000000000000`) against all 4 gate tools:

| Tool | HTTP status | isError | Denial class | Raw leak? |
|---|---|---|---|---|
| judgment_query | 200 | true | `entitlement_denied` | no |
| graha_portrait | 200 | true | `entitlement_denied` | no |
| pact_query | 200 | true | `entitlement_denied` | no |
| chart_snapshot | 200 | true | `entitlement_denied` | no |

Native's own chart (482012f1) against the same 4 tools: all succeeded normally, response shapes
matched the expected R5.1 C1 budget-capped envelope (109-byte structured-content-only bodies for the
three trimmed instruments; 2,055-byte full snapshot for `chart_snapshot`). **Gate criterion
("unentitled chart_id → clean denial on judgment_query/graha_portrait/pact_query/chart_snapshot; the
native's own calls unaffected") MET, live, on prod.**

### Latency completion item (native instruction, post-initial-report)
Baseline: no dedicated warm-p50 sample exists for these 4 specific tools at R5.1-close time — the
closest recorded per-tool latency data is the R5.1 C4 full-battery run (commit `bcdfed45`, 1 rep per
battery item, mixed native/Abhinandan charts): 16 samples across judgment_query/graha_portrait/
pact_query (chart_snapshot has no historical sample — it shipped later in C2), **median 826.9ms**.
This is the honest best-available comparator, not a perfectly-matched methodology (different sampling
regime) — noted rather than hidden.

Post-A1-deploy warm measurement (native chart, n=10 per tool after 1 discarded warm-up call each,
same prod endpoint):

| Tool | n | p50 (ms) | min | max |
|---|---|---|---|---|
| judgment_query | 10 | 370.8 | 295.5 | 552.6 |
| graha_portrait | 10 | 317.2 | 267.3 | 439.9 |
| pact_query | 10 | 391.1 | 317.1 | 548.8 |
| chart_snapshot | 10 | 206.2 | 160.4 | 282.4 |
| **overall** | **40** | **335.2** | — | — |

**Delta: −491.7ms (−59%) vs the 826.9ms comparator — well within the +50ms ceiling; no regression.**
The entitlement gate's 30s in-process cache adds no observable p50 cost. No caching fix required; A2
proceeds unblocked per the native's own conditional instruction.

### A1 verdict
**CLOSED. No HALT. Proceed to A2.** No chart data touched. No entitlement widened (only narrowed —
correctly). Branches `feature/r5-2-a1-capability-entitlement` and `docs/r5-2-acceptance-brief` deleted
post-merge/close.

---

## A2 — THE DETERMINISTIC GAP — three lanes

### Lane 1 — budget/trim discipline estate-wide (punch #3)
Sweep method: `tools/list` against live prod, then one default-args `tools/call` per tool (129 tools
total) on the native chart, measuring wire bytes. Full results in session scratch (not committed —
ephemeral measurement, not a governing artifact).

**Before (worst offenders found):**

| Tool | Bytes | Class |
|---|---|---|
| holistic_bundle_chart_facts | 544,867 | legacy/scaffold (documented DEFERRED elsewhere, superseded by bodha_bundle_get) |
| phala_outlook | 461,456 | composite L4 bundle (100 anchors + 100 mitigations + 30 windows, no ceiling) |
| query_remedies | 106,510 | single oversized result row (not an array-count problem — see deferral below) |
| vector_search | 47,047 | corpus search |
| list_assets / catalog_assets_* | ~37,970 | registry listing |
| get_remedies / bodha_remedies_get | ~34,600 / 30,989 | remedy prescriptions |
| get_dashas | 33,481 | 50-row dasha listing (reasonable for its stated purpose) |
| bodha_chart_digest_get | 30,633 | chart digest |
| mimamsa_insight_get | 29,955 | L5 insight (STRUCTURAL mode) |

**Fixed (this run, reusing the R5.1 C1 shared `response_budget.ts` trimmer — not a bespoke cut per
tool):**
- `phala_outlook` (`platform-mcp/src/tools/phala_outlook.ts`): 30KB ceiling, 3 trimmable sections
  (anchors minKeep=10, mitigations minKeep=10, auspicious_windows minKeep=5), each with a
  `recover_via` pointer to the corresponding surgical instrument. 461KB → pending live re-measure
  post-deploy (see A2 gate below).
- `holistic_bundle_chart_facts` (`platform-mcp/src/tools/retrieval/holistic_bundle.ts`): 30KB
  ceiling on `bundle_entries` (minKeep=2 of 8), `recover_via: bodha_bundle_get` (its documented
  successor). 544KB → pending live re-measure post-deploy.

**Deferred, honestly, not silently:**
- `query_remedies` (106KB): the oversize is ONE result row, not a repeated-array problem — the
  shared array-trimmer has nothing to shrink by count here. The fix belongs in the platform-side
  `query_remedies` primitive handler's content shape, not this MCP-layer proxy. Needs its own
  investigation pass; not fixed in this run.
- `vector_search`, `list_assets`/`catalog_assets_*`, `get_remedies`/`bodha_remedies_get`,
  `bodha_chart_digest_get`, `mimamsa_insight_get` (30–47KB each): real but an order of magnitude
  smaller than the two "234KB-class" outliers fixed above; judged lower-priority given this run's
  one-iteration budget. Flagged for a follow-up sweep, not silently dropped from the record.

### Lane 2 — dignity field on query_chart_facts (punch #2)
`platform/src/lib/retrieval/registry/layers/register_d7_channel.ts` (`chart_facts_query`
capability, public MCP names `query_chart_facts` / `ganita_chart_facts_get`). Root cause: dignity
facts (`graha_dignity_per_varga`, fact_subject = `D1_<code>`, e.g. `D1_SAT`) and position facts
(`graha_position`, fact_subject = `<code>`, e.g. `SAT`) use DIFFERENT fact_subject keys, so the
EAV-pivot's natural group-by-subject never merges them — a position query has never carried
dignity without a second `get_dignity` call. Fix: after pivoting, any row whose subject is a known
graha code (`GRAHA_CODE_TO_NAME`, `address_resolver.ts`) and carries a `sign` field gets one
additional lightweight join query (`graha_dignity_per_varga` WHERE fact_subject = ANY(D1\_&lt;codes&gt;))
merged in as `dignity` + `fact_ids.dignity` (citing the real fact_id — B.3). Verified against the DB
directly (not fabricated): native chart Saturn D1 `dignity_state='exalted'`, `sign='Libra'` — matches
Saturn's classical exaltation sign per BPHS, an independent sanity cross-check, not an assumption.
No new computation — a join/projection over data already in `chart_facts`, per B.10.

### Lane 3 — wire the orphaned C2 fixes (punch #5)
**Wired:** `query_predictive_anchors` (posterior-provenance fix, R5.1 C2 item 4) — new public MCP
tool `phala_predictive_anchors_get` (`platform-mcp/src/tools/register_p1_aliases.ts`), named
distinctly from the pre-existing `phala_anchors_get` sidecar-backed alias to avoid repeating that
exact naming collision. Read-only.

**Deliberately NOT wired this run:** R5.1 C2 item 3 (denial≠empty on the chart-scoped write paths —
`log_prediction`/`lel_event_record` have no public MCP tool). Wiring a write-path tool is not itself
a chart-data write, but *verifying* it live — this program's own non-negotiable discipline, every fix
gets a live gate check — would require actually calling `log_prediction` or `lel_event_record`
against a real chart, which writes real prediction/LEL rows. This run's own frontmatter
(`must_not_touch`: "chart data (read-only)", "LEL rows"; HALT: "any chart-data write") forbids
exactly that. Rather than half-wire an unverified tool (violating this program's verification
discipline) or violate the must-not-touch boundary to verify it, item 3 is deferred whole, with this
reasoning on record — not silently dropped from "the two orphaned C2 fixes" the brief named.

### A2 verification (pre-merge)
`tsc --noEmit` clean in `platform` and `platform-mcp`. `platform-mcp` vitest: 96/509 pre-existing
failures, unchanged from the A1 baseline — zero regressions from Lane 1/2/3 changes.

---
