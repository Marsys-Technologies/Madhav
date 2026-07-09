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
  `recover_via` pointer to the corresponding surgical instrument. **461,456B → 28,125B live on prod,
  verified.**
- `holistic_bundle_chart_facts` (`platform-mcp/src/tools/retrieval/holistic_bundle.ts`): 30KB
  ceiling on `bundle_entries` (minKeep=2 of 8), `recover_via: bodha_bundle_get` (its documented
  successor). **544,867B → 866B live on prod, verified.**

**Live-verification round caught two real bugs the first deploy missed (PR #501, commit
`b7666adf`), fixed and re-deployed within the same run:**
1. `holistic_bundle_chart_facts`'s `bundle_entries` array is nested under `envelope.bundle_entries`,
   not the result's top level — the first version of the trim section read the wrong path and found
   nothing to cut (confirmed live: 544KB in, 544KB out, `trim_report` showed the hard-cap fallback
   firing on zero actual trims — an honest signal the mechanism itself surfaced correctly, which is
   how this was caught). Fixed to read/write the correct nested location.
2. Both fixed tools pretty-printed their final JSON (`, null, 2`), inflating wire bytes past what
   `applyResponseBudget` measured (compact serialization) — `phala_outlook` shipped 38,351B against
   its declared 30KB ceiling on the first deploy. Switched both to compact serialization; second
   live measurement (28,125B) confirms the fix.

This is exactly the "live gate check catches what static review can't" discipline this program is
built on — recorded honestly rather than smoothing over the first-pass miss.

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

### A2 live gate check — `[verify-against: mcp]`, prod, both PRs deployed (commits `52c409bc` then `b7666adf`)

| Lane | Check | Result |
|---|---|---|
| 1 — phala_outlook | wire bytes | 461,456 → 28,125 (−93.9%), under 30KB ceiling |
| 1 — holistic_bundle_chart_facts | wire bytes | 544,867 → 866 (−99.8%), under 30KB ceiling |
| 2 — dignity join | `ganita_chart_facts_get` category=graha_position, native chart | JUP: `dignity:"own"` (fact_ids.dignity cited); KET_MEAN: `"exalted"`; MAR/MER: `"neutral"`; LAGNA correctly has no dignity field (not a graha) |
| 3 — phala_predictive_anchors_get | tool reachable + shape | `anchors[]` present, each with real `posterior_provenance` (model_formula, base_rate_source narrative, honest `cardinality: null`) — matches the R5.1 C2 item-4 fix exactly, now actually reachable |

### A2 verdict
**CLOSED. No HALT. Proceed to A3.** Both PRs (#500 lanes 1-3; #501 the live-verification-caught
trim-path + serialization fix) merged and deployed. Every claim in this section is a live prod
measurement, not a pre-deploy assertion. No chart data written (Lane 3's write-path deferral held).
No entitlement touched. Branches `feature/r5-2-a2-budget-dignity-orphans` and
`fix/r5-2-a2-bundle-trim-path` deleted post-merge.

---

## A3 — CONTENT DEPTH

### Checkpoint methodology (before further content work)
Ran the full R5.1 W4 battery harness (`evals/r5-w4-full-battery/battery_runner.ts`) live against
prod at commit `87feb280` (A1+A2 already deployed), with both `GOOGLE_GENERATIVE_AI_API_KEY` and
`DEEPSEEK_API_KEY` available locally — real LLM grading is genuinely runnable in this environment,
not assumed. Result written to `evals/r5-w4-full-battery/results_87feb280.json` (committed alongside
the two prior baseline result files already in the repo).

**Structural finding, load-bearing for the rest of A3:** every Q2–Q9 item (the rubric-graded,
full-NL-answer class — exactly what A3's "content depth" punch item targets) returned
`INCONCLUSIVE BY DESIGN`. `battery_runner.ts` itself documents why (line 835): it has no
orchestrating answering-LLM to read a free-text turn-1 answer and issue a genuine follow-up tool
call — it can only exercise individual MCP tool calls directly, not a real multi-turn NL
conversation. This is **not a bug this run can fix** — it is a documented, honest harness
limitation (not a "grading criteria" change to make, and not something a code fix here resolves).
The only Q2–Q9 rubric data that exists anywhere is the earlier `results_bcdfed45.json` run,
presumably produced by a differently-configured harness invocation (a live answering-LLM loop) not
reproduced by this run's tooling. **Practical consequence:** A3's rubric-floor gate cannot be
independently re-verified by this run's own tooling; the fixes below target the deterministic Q1/X
findings this harness CAN verify, which is where genuine, provable progress was available.

### Deterministic Q1/X findings — root cause then fix

**X-2 (entitlement, `no_raw_401_403_text` assertion) — FIXED.** Root cause: `callRegistryCapability`
(and its 4 sibling copies in the `register_p1_*.ts` files) used a generic error message —
`` `capability call failed (${res.status}): ...` `` — for every non-ok response, including the clean
`entitlement_denied` case A1 already produces server-side. The MCP-facing error text therefore
still embedded the literal transport status code, which the battery's own leak-detector correctly
flags. `describeProxyFailure` (already built and already used by `callPlatformPrimitive`, per an
R5.1 C2 fix) produces the clean, denial-specific message without a raw status code — this run wires
it into `callRegistryCapability` and all 4 sibling copies, closing the same gap uniformly across
every capability-route caller, not just the one X-2 happens to exercise.

**X-3 (budget, `response_le_ceiling` assertion) — FIXED.** `bodha_signals_get` at `top_k=200` (the
schema max) measured 234,278 wire bytes live — the exact "234KB class" the brief names, on a tool
C1 never touched (C1's scope was judgment_query/graha_portrait/pact_query only; A2's estate sweep
used default args and didn't surface this specific abuse-case size). Replaced the generic `regAlias`
registration with a bespoke one that applies the same shared `response_budget.ts` trimmer (25KB
ceiling, `signals` section, minKeep=20) already used everywhere else in this run.

**Q1-A-2 dignity check (`pisces_h12_exalted_present`) — already fixed by A2 Lane 2**, confirmed by
this checkpoint run (`True`) without further work.

**X-7 (`lagna_frame_scorpio_h8_confirmed`) — investigated, confirmed NOT a product gap.** Queried
`chart_facts` directly for Abhinandan's Saturn: `sign="Scorpio"`, `house_d1=8` — both facts are
genuinely correct (Scorpio is the 8th sign from an Aries lagna under whole-sign houses). The
assertion's own regex (`/house\D?8/i`, allowing at most one non-digit character between "house"
and "8") cannot match the real field name `"house_d1":8` (five characters between "house" and "8").
This is a harness pattern-strictness false negative, not touched — editing the frozen battery's own
assertion logic is out of this run's authority (harness *bug* fixes are permitted with before/after
proof on an unaffected item; a deterministic pass/fail *pattern* is closer to grading criteria than
this run should touch unilaterally).

**Deferred, honestly, not silently:**
- **X-6** (`time_sensitivity_grade_present` on D60 divisional-chart queries): a genuine, real gap —
  `query_chart_facts` has no confidence/rectification caveat when serving fine vargas like D60,
  which are classically far more birth-time-sensitive than D1. A correct fix would cite
  `phala_rectification`'s existing confidence data, not fabricate a new note — real cross-subsystem
  work, not completed this iteration.
- **X-8** (stale-note residue): already flagged in R5.1 as "mostly fixed by C2's E-2 work, one
  marker still present" — a known, small pre-existing residual, not re-investigated this run.
- **Q1-N-3/N-4/A-1/A-3** (tight 1–2KB byte-ceiling overages on `query_chart_facts`/
  `ganita_dashas_get`, 2.3–3.5KB observed): real but an order of magnitude smaller than the
  234KB-class items fixed above; these ceilings are tighter than any budget-discipline precedent
  elsewhere in this program (8–30KB). Judged lower priority given the one-iteration budget.
- **Q3-A-2, Q6-N-1, Q8-N-1, Q8-A-1, Q9-A-1** (the actual rubric-floor items A3 was scoped to fix):
  live-tool spot checks this run (muhurta_finder, get_remedies, judgment_query, graha_portrait) show
  the underlying MCP tool responses are substantively rich (ranked windows with real factors/
  citations, real posterior_provenance, real dignity data) — but per the structural finding above,
  there is no way for this run's own tooling to re-grade the actual rubric-floor question, because
  the rubric grades a full NL answer this harness cannot generate. Pratinidhi-R-style content
  rulings on these 5 items are deferred to a session with the answering-LLM harness available,
  rather than asserted fixed on unverifiable grounds.

### A3 verification (pre-merge)
`tsc --noEmit` clean. vitest: 96/509 pre-existing failures, unchanged — zero regressions.

### A3 live gate check — `[verify-against: mcp]`, prod, commit `f28f09d6` deployed

| Item | Check | Result |
|---|---|---|
| X-2 | `judgment_query` foreign chart_id, error text | No raw `(401)` substring; clean `ENTITLEMENT_DENIED` message present |
| X-3 | `bodha_signals_get` top_k=200, wire bytes | 234,278 → 15,860 (−93.2%), `trim_report` present citing the real original/kept counts |

### A3 verdict
**CLOSED. No HALT. Proceed to A4.** Two real deterministic gaps (X-2, X-3) fixed and live-verified.
One (X-7) confirmed a harness false-negative, not touched. Rubric-floor items (Q3-A-2, Q6-N-1,
Q8-N-1, Q8-A-1, Q9-A-1) and X-6/X-8/tight-Q1-ceilings deferred with reasoning — this run's own
tooling cannot independently re-grade a full NL answer (no orchestrating answering-LLM in the
harness), so no rubric-floor claim is asserted here that couldn't be verified. Branch
`feature/r5-2-a3-content-depth` deleted post-merge.

---
