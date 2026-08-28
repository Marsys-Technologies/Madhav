# S4 Pipeline Correctness & Door Parity — Stage S5 (AcharyaPlan / planner) report

Investigator: S4 lane, stage S5 only. Test subject: synthetic chart
`1c826d5a-41cb-4450-b4dc-59d440e5f75a` (query_trace_steps evidence below is queried
without a chart_id filter — the table carries no chart_id column — but is scoped by
query_id/user_id from the live dev/synthetic dataset reachable via the read-only Cloud
SQL proxy on 127.0.0.1:55432; the native's real chart `482012f1-…` was never queried).

Code anchors read in full: `platform/src/lib/pariprashna/pipeline/plan_stage.ts`,
`platform/src/lib/pipeline/pipeline_planner.ts` (head), `platform/src/lib/pipeline/
compiled_floor_adapter.ts`, `platform/src/lib/vidhi/compiler.ts`, `platform/src/lib/
pipeline/budget_arbiter.ts`, `platform/src/lib/pipeline/no_leakage_filter.ts`,
`platform/src/lib/pariprashna/pipeline/evidence_stage.ts`, `platform/src/lib/cache/
with_cache.ts`, `platform/src/lib/pipeline/completeness_wiring.ts`,
`platform/src/lib/pariprashna/pipeline/synthesis_stage.ts`,
`platform/src/lib/pipelines/shared/run_adapter_dispatch.ts`,
`platform-mcp/src/resources/vidhi/plan_builder.ts`.

---

## 1. Correctness

### 1a. Is the B.11 compiled floor actually compiled INTO the plan, never "by convention"?

**Yes, structurally.** The LLM planner (`pipeline_planner.ts`) emits `tool_calls` from
its own reasoning, but `plan_stage.ts:262-286` runs a deterministic, code-enforced
sequence after the LLM call returns, independent of what the LLM chose:

1. `arbitrateBudgets` (budget_arbiter.ts) — pure function, trims planner tool budgets.
2. `compileFloorForPlan(plan.scope_tuple, chartId)` (compiled_floor_adapter.ts:262) —
   calls `compileContract` (vidhi/compiler.ts), the deterministic Vidhi compiler, and
   pushes any compiled-floor tool the planner didn't already authorize.
3. `ensureB11WholeChartReadFloor` / `ensureDashaContextFloor` — idempotent guarantees
   that force-inject an L2.5 whole-chart-read tool and a dasha-context tool if still
   absent after step 2.

This is genuinely floor-by-code, not floor-by-LLM-convention — the LLM cannot omit the
floor by failing to think of it. `compileContract` itself throws on a registry-
completeness bug rather than silently compiling a partial contract
(vidhi/compiler.ts:326-328, "must fail loudly rather than silently compile a partial
contract") — verified live in §4 below.

**Finding S5-C1 (Correctness, proposed severity: MEDIUM).**
`compileFloorForPlan`'s own `compileFailed` / `unmappedPrimitives` / `mappedPrimitives`
fields — the honest signal the function computes for exactly this "did the floor
actually compile" question — are **never read by the caller**. `plan_stage.ts:277-284`
only consumes `compiledFloor.toolCalls`; grep-confirmed (test evidence in §4) that
`plan_stage.ts` contains no reference to `compiledFloor.compileFailed`,
`compiledFloor.unmappedPrimitives`, or `compiledFloor.mappedPrimitives` anywhere in the
file. If `compileContract` ever throws in production (the exact "registry-completeness
bug" case the compiler's own header calls out), the turn silently falls through to
whatever `ensureB11WholeChartReadFloor`'s generic fallback provides — no `em.flag()`,
no `judgment_flags` entry, no server log line marks that the INTENT-SPECIFIC compiled
floor (the richer Vidhi floor, not just the generic B.11 minimum) failed to compile at
all. This is the same defect class as §N.8 (Earned-Signal Principle): a real detector
exists and computes the right value, but nothing consumes it, so a genuine floor-
compilation failure is indistinguishable from a healthy turn on every surface a
reader/operator can see.
- Code anchor: `platform/src/lib/pariprashna/pipeline/plan_stage.ts:276-284` (call
  site); `platform/src/lib/pipeline/compiled_floor_adapter.ts:241-252` (the dropped
  fields, `CompiledFloorResult` interface).
- Proposed fix class: when `compiledFloor.compileFailed` is true, or
  `unmappedPrimitives.length > 0`, push a `judgment_flags` entry and `em.flag()`
  exactly as the file already does for NO-LEAKAGE strips and safety exclusions two
  sections later in the same function — the pattern already exists in this file, it's
  just not applied to this signal.
- Rung achieved: INTEGRATION (real code path exercised via a real registry-throw
  mock + grep-verified caller behavior — see §4).

### 1b. `no_leakage_filter.ts` — does it strip correctly without dropping something it shouldn't?

Read in full (61 lines). `filterLeakedCapabilities` strips only capabilities whose
registered `CapabilityDescriptor.calibration_context_only === true`; it explicitly
fail-opens (keeps) any name that doesn't resolve via `resolveToolUri`/`getCapability`
— documented as deliberate ("this filter's only job is to strip... it is not a tool-
name validator"). This is a sound, narrow design: it cannot over-strip an unrelated
capability, and the 2026-08-23 `lel_query` strip-class defect referenced in the task
brief is exactly the kind of bug this narrow-flag design forecloses (an unrelated name
can never be caught by a boolean flag meant for one different capability). All 43
existing tests across the four S5 test files passed (§ test run below), including
`no_leakage_filter_real_catalog.test.ts`, which runs the filter against the real
registry catalog rather than a fixture — this is the regression guard for the
2026-08-23 class of defect and it currently passes.

### Test run (real, INTEGRATION rung)

```
$ npx vitest run \
    src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts \
    src/lib/pipeline/__tests__/no_leakage_filter.test.ts \
    src/lib/pipeline/__tests__/no_leakage_filter_real_catalog.test.ts \
    tests/pipeline/budget_arbiter.test.ts

 Test Files  4 passed (4)
      Tests  43 passed (43)
   Duration  792ms
```

---

## 2. Optimality (test plan §4.2 — all three measured)

### 2a. Floor-coverage completeness — normal vs forced-gap

`completeness_wiring.ts`'s `buildWebCompletenessReceipt` is a genuinely honest receipt
builder: it classifies every compiled floor primitive as `served` / `empty` (with a
specific `empty_reason`: `route_error`, `route_empty`, `route_not_invoked`, or
`web_namespace_gap: …`) / `dark`, and its `channel_note` explicitly warns "A small
served count reflects the namespace gap, not a fully-honored floor" — this is not
security theater, it self-reports its own known incompleteness. Normal-scenario
coverage was confirmed live: the file's own header states only 4 (originally) /
~20-of-23 (post RC-10) distinct MCP `live_tool` names have a web-executable
equivalent at all, and the receipt reports every uncovered one honestly rather than
omitting it.

**Finding S5-O1 (Optimality/Correctness, proposed severity: MEDIUM).**
`buildWebCompletenessReceipt` resolves `live_tool → retrieval tool` using only the
**hand-curated** `LIVE_TOOL_TO_RETRIEVAL` map (`completeness_wiring.ts:106`,
`LIVE_TOOL_TO_RETRIEVAL[item.live_tool]`), while the code path that actually decides
what gets **dispatched** (`compileFloorForPlan` → `resolveLiveTool`,
`compiled_floor_adapter.ts:224-226`) additionally falls back to the **generated**
projection bridge (`resolveGeneratedToolUri`, built from the live catalog). These two
call sites use two different resolution functions for what is documented as "the
SAME... resolution path" concern (`plan_bridge.ts:137-138`: "reuses whatever the web
engine already uses... never a second, divergent resolution path" — a promise this
pair of files breaks). Live-measured (test below, INTEGRATION rung): of 40 distinct
`live_tool` names in the registry, **10** resolve to a real web-executable tool via
the generated bridge but are invisible to the hand map, including major primitives —
`ganita_chart_facts_get`, `ganita_positions_get`, `ganita_dasha_periods_get`,
`ganita_special_lagnas_get`, `mechanism_retrodiction_get`, `kala_yoga_activation_get`,
`kala_muhurta_get`, `bodha_mechanisms_get`, `mimamsa_calibration_get`,
`ganita_medical_get`. For any floor primitive keyed to one of these, `compileFloorForPlan`
DOES dispatch and get results, but `buildWebCompletenessReceipt` reports it as
`web_namespace_gap` (empty/dark) regardless of the true served outcome — the honest-
sounding receipt is **systematically too pessimistic** for ~25% of the registry's
distinct live_tool surface, understating actual floor coverage.
- Code anchors: `platform/src/lib/pipeline/completeness_wiring.ts:106` (narrow
  resolution) vs `platform/src/lib/pipeline/compiled_floor_adapter.ts:224-226`
  (`resolveLiveTool`, the wider resolution actually used for dispatch).
- Proposed fix class: `completeness_wiring.ts` should call `resolveLiveTool` (exported
  from `compiled_floor_adapter.ts`) instead of indexing `LIVE_TOOL_TO_RETRIEVAL`
  directly — one-line fix, same shape as the §N.7 item 3 "reference, not a copy" fix
  this codebase already applies elsewhere (`BAND_BUDGET`/`BAND_PRIORITY`).
- Rung achieved: INTEGRATION (real registry data, real resolvers, both import paths
  exercised — reproduced with `npx vitest run` against the live registry; console
  output captured, saved at `.s4_scratch/s5_probes/zzz_s4_probe_door_parity.test.ts`'s
  sibling probe, not committed to the tree).

Forced-gap scenario: confirmed via §4's `compileFailed` test that when the compiled
floor cannot even build (registry-completeness bug), the receipt-building path
(`completeness_wiring.ts:80-87`) degrades the SAME way `compiled_floor_adapter.ts`
does — catches the throw, returns `null`, and the caller "simply omits the receipt (it
is delivery metadata, never load-bearing)". This is honest (no fabricated receipt) but
compounds Finding S5-C1: a `null` receipt and a "floor compiled fine, just nothing
served" receipt are visually indistinguishable to a downstream reader — both look like
"no completeness data was shown this turn."

### 2b. Tool-selection efficiency = dispatched ÷ actually-used

**Method (stated per instructions):** used live `query_trace_steps` rows (DB-backed,
LIVE-adjacent rung) rather than a synthetic estimate. `compose_bundle`'s
`data_summary.result` field ("N assets · M tools") reports the plan's dispatched tool
count for that turn; `citation_error`/`citation_warn` steps report
`data_summary.citation_count` — the count of tool-sourced signals that actually made
it into a stamped citation in the synthesized reader response. This is an
approximation of "used in adjudication" (citations are a lower bound — a tool result
can inform the model's reasoning without being individually cited — but it is the
only DB-recorded "was this evidence surfaced" signal on this door, so it is reported
as such, not smoothed over).

**Result, real DB query, 14 real turns (query_class = `predictive`, the
scan window's dominant class):**

```
query_id                              | tools dispatched | citations produced
3c9662b9-…, 7fb7d40a-…, 72795caf-…,   | 10 (one: 4)       | 0  (every single turn)
c6b61828-…, 2a6fe278-…, 2d3300d9-…,
11c3c145-…, 89f11605-…, adb253ca-…,
be1acefc-…, 8035968e-…, e5cfbaaa-…,
86d2f98e-…, 05baeb74-…
```
message on every row: `"prescriptive query (predictive) produced 0 citations —
guidance must be grounded"`.

**Tool-selection efficiency for predictive-class turns in this sample: 0 / 10 = 0%.**
This is a real finding under §N.6/§N.8's own doctrine — "a persistently low ratio is
itself a finding (over-dispatch)" is exactly what the task brief predicted, and it is
confirmed at the most extreme value possible: every one of 14 measured predictive
turns dispatched a full 10-tool floor and cited zero of it.

Contrast: the sample's 2 `interpretive`-class turns did **not** appear among the
`citation_error`/`citation_warn` rows (one of them dispatched only 4 tools and
produced no citation-failure flag), suggesting this 0%-efficiency pattern may be
scoped to the `predictive`/prescriptive query class rather than universal — n=2 is too
small to confirm generally, flagged as a scope caveat, not a conclusion.

**Finding S5-O2 (Optimality, proposed severity: HIGH — proposed because it is a
100%-reproducible, DB-confirmed over-dispatch, not a rare edge case).**
Architecturally, this traces back to a genuine double-dispatch design: `evidence_stage.ts`
(pass 1) fetches **every** `toolsAuthorized` tool directly against the registry
(`getToolByName` → `executeWithCache`, evidence_stage.ts:75-103) purely to build the
completeness receipt and extract candidate signal-ids by regex
(`citation_resolver.ts:44-54`, `extractCandidateSignalIds`) — this pass-1 content is
**never** injected into the synthesis prompt (`run_adapter_dispatch.ts:441-448` builds
`bundleSystemContent` from `bundle.assets`, i.e. `asset_bundle` DOCUMENTS, not
`tool_calls` results). Separately, the synthesis model runs its **own** agentic loop
(`run_adapter_dispatch.ts:479-489`, `useAgenticLoop`/`buildChatToolsFromNames`, up to
`maxIterations: 8`) where it is free to call — or not call — any subset of
`toolsAuthorized` itself. The plan's 10-tool B.11/floor authorization guarantees pass-1
gets fetched (cost paid) and the completeness receipt looks fully served, but the
model's own tool-choice in the agentic loop is what actually determines evidence used
in the reader-visible answer, and for predictive-class turns in this sample that
choice yields zero grounded citations 14/14 times.
- Code anchors: `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:75-103`
  (unconditional pass-1 dispatch of all `toolsAuthorized`);
  `platform/src/lib/pariprashna/pipeline/citation_resolver.ts:44-54` (the only
  consumer of pass-1 results); `platform/src/lib/pipelines/shared/
  run_adapter_dispatch.ts:441-489` (agentic loop tool access, separate from pass 1).
- Proposed fix class: either (a) skip pass-1 dispatch for tools the agentic loop will
  redundantly re-call (requires knowing in advance, hard), or (b) feed pass-1 results
  directly into the agentic loop's tool-result cache so a model call for an
  already-fetched tool is served from pass 1 rather than re-dispatched — currently
  `executeWithCache`'s L1/L2 cache keys are keyed off `plan.*` fields shared between
  both call sites, so this may already partially coalesce; the citation-count evidence
  above says whatever coalescing exists is not translating into grounded output for
  predictive turns.
- Rung achieved: DB-backed / LIVE-adjacent (real `query_trace_steps` rows via the
  read-only Cloud SQL proxy, 127.0.0.1:55432, `amjis` database — 14 independent real
  turns, 100% reproduction rate).

### 2c. Plan latency share of turn

Instrumented via the same real `query_trace_steps` table (`step_name='llm_planner'`,
`step_type='llm'`).

```sql
select count(*), avg(latency_ms), percentile_cont(0.5)..., percentile_cont(0.9)...
from query_trace_steps where step_name='llm_planner'
```
→ **N=44, avg 3925 ms, p50 4071 ms, p90 4885 ms, min 1698 ms, max 5091 ms.**

Turn-share, computed two ways (both honestly reported — they diverge a lot, and the
divergence is itself informative):

1. **Share of the measured step-sum "turn"** (sum of every `latency_ms`-bearing step
   for a `query_id` that includes `llm_planner`, N=22 turns): avg turn 12,296 ms, avg
   planner 3,925 ms → **planner ≈ 45.9% of the measured turn.**
2. **Share of the EDIR E-006 81.3 s live-seed reference turn:** 3,925 ms / 81,300 ms
   ≈ **4.8%.**

**Finding S5-O3 (Optimality, informational — not a defect, a measurement-honesty
note).** These two numbers disagree by an order of magnitude because `synthesis`
appears in `query_trace_steps` with **no `latency_ms` recorded at all** (confirmed:
its row in the per-step average query returned a blank `avg_ms`) — the step-sum "turn"
in computation (1) silently excludes the token-streaming synthesis phase, which is
almost certainly the dominant contributor to the 81.3 s E-006 reference turn. Any
naive "planner share of turn" computed from this table alone (interpretation 1) would
overstate the planner's share of end-to-end latency by roughly 10×. The honest number
for "how much of what the reader waits for is planning" is closer to **~5%**
(interpretation 2, using the one available full-turn reference point), not ~46%.
- Code anchor: no code fix — this is an instrumentation-coverage gap. `query_trace_steps`
  never gets a `latency_ms` write for the `synthesis` step name; whichever code emits
  that row (outside S5's `may_touch` scope — likely `synthesis_stage.ts`'s trace sink,
  S6's lane) should be flagged to S6/whoever owns that stage for a
  latency-instrumentation fix, since it silently breaks turn-share math for every
  stage measured this way, not just S5.
- Rung achieved: DB-backed / LIVE-adjacent (44 real planner-call rows, 22 real
  multi-step turns, `amjis` database via the read-only proxy).

---

## 3. Failure-honesty

**Finding S5-F1 (Failure-honesty, proposed severity: MEDIUM — currently latent, not
actively causing evidence loss).**
`budget_arbiter.ts`'s `arbitrateBudgets` can and does reduce a priority-3 tool's
`token_budget` all the way to **0** ("p3 first... floor = 0, can be trimmed away
entirely" — `budget_arbiter.ts:54-66`, confirmed by direct test, §4). If the planner
itself already authorized a B.11 floor tool (e.g. `msr_sql`, a member of
`L2_5_TOOLS`) at priority 3, and arbitration zeroes it, `ensureB11WholeChartReadFloor`
(`compiled_floor_adapter.ts:329-330`) checks **only tool-name presence** —
`toolsAuthorized.some((t) => L2_5_TOOLS.includes(t))` — not whether that tool's
`token_budget` is non-zero. The floor guarantee therefore reports itself satisfied
("no injection needed") for a tool whose own budget field claims 0 tokens, with no
compensating top-up and no disclosure that the nominal floor tool is budget-starved.
Confirmed live in a real (non-mocked) `arbitrateBudgets` + `ensureB11WholeChartReadFloor`
call (§4).

**Why this is currently latent rather than actively starving evidence:** separately
confirmed (Correctness tracing, §1/§2b) that `token_budget` is **not actually consumed**
anywhere on the pass-1 dispatch path — `evidence_stage.ts`'s `executeWithCache` call
(`with_cache.ts:60-107`) takes no budget parameter, and the retrieved tool bundle is
either (a) used only for candidate-signal-id regex extraction, or (b) not injected into
`bundleSystemContent` at all (that's built from `asset_bundle` documents, not
`tool_calls`). So today, a token_budget=0 floor tool still gets fully dispatched and
its full result is still available to the agentic loop if the model chooses to call it.
The bug is real but dormant: the arbiter's documented purpose ("hard cap on
planned_total" to avoid exceeding the synthesis context window) is **not currently
enforced by anything downstream on this door** — meaning both (i) the arbiter's own
stated job is not actually being done on the retrieval path, and (ii) the specific
floor/budget interaction above would become a live evidence-starvation bug the moment
someone wires `token_budget` into actual content truncation, exactly the kind of
"looks fine because nothing reads the value yet" trap §N.8 warns about.
- Code anchors: `platform/src/lib/pipeline/budget_arbiter.ts:54-66` (can zero p3);
  `platform/src/lib/pipeline/compiled_floor_adapter.ts:329-330` (presence-only check);
  `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:75-103` +
  `platform/src/lib/cache/with_cache.ts:60-107` (token_budget never passed to
  dispatch — the reason it's dormant today).
- Proposed fix class: (a) `ensureB11WholeChartReadFloor`/`ensureDashaContextFloor`
  should check `token_budget > 0` (or some minimum), not name presence alone; (b)
  separately, someone should confirm whether `token_budget`'s complete non-use on the
  dispatch path is intentional (the agentic loop's own context management may make the
  pass-1 arbiter genuinely vestigial by design) or a stale wiring gap — worth a
  dedicated finding for whoever owns the overall pipeline architecture, since it's
  bigger than S5 alone.
- Rung achieved: INTEGRATION (real `arbitrateBudgets` + real
  `ensureB11WholeChartReadFloor` called together, no mocking, realistic config values
  — §4).

---

## 4. Demonstrated-can-fail

Two real, run tests (not hypothetical) prove the loud-vs-silent failure boundary:

**Test 1 — the internal detector works (fails loudly at the point of computation):**
mocked `compileContract` to throw (simulating vidhi/compiler.ts's own documented
"registry-completeness bug... must fail loudly" case) and called the REAL
`compileFloorForPlan`. Result: `{ compilerIntent: 'structure_read', toolCalls: [],
mappedPrimitives: [], unmappedPrimitives: [], compileFailed: true }` — confirmed by
running the actual function, not asserting on documentation.

**Test 2 — the caller drops the signal (fails silently at the point of disclosure):**
read the real `plan_stage.ts` source and asserted (a) it does call
`compileFloorForPlan(plan.scope_tuple, chartId)`, and (b) the string
`compiledFloor.compileFailed` (and `.unmappedPrimitives`, `.mappedPrimitives`) does
**not** appear anywhere in the file. Both assertions passed against the real file.

```
$ npx vitest run <probe test file>
✓ compileFloorForPlan DOES set compileFailed:true when compileContract throws
✓ DOCUMENTS that plan_stage.ts never reads compiledFloor.compileFailed / unmappedPrimitives
Test Files  1 passed (1)  Tests  2 passed (2)
```

**Test 3 — the budget/floor interaction (Finding S5-F1) reproduced directly**, no
mocking: real `arbitrateBudgets` config (`max_context: 2000, reserve: 800,
margin: 0.85, min_per_tool: 200`) zeroes a p3 `msr_sql` tool's budget from 2000→0, then
the real `ensureB11WholeChartReadFloor` is called with the resulting `toolsAuthorized`
array and returns `injected: false` (believes the floor is met). Output:
`msr_sql token_budget after arbitration: 0`, `injected? false`.

Together, tests 1+2 constitute the "demonstrated-can-fail... loudly (not silently)"
requirement in the negative direction the task asked to check for: the low-level
mechanism DOES fail loudly (a real Error is thrown and caught, `compileFailed` is
correctly set), but the SYSTEM as a whole (plan_stage.ts's consumption of that signal)
fails silently, because the loud internal signal is discarded one call frame up. This
is Finding S5-C1 restated as a proof rather than an assertion.

Probe test files (not committed to the tree, kept for reproducibility):
`.s4_scratch/s5_probes/zzz_s4_probe_can_fail.test.ts`,
`.s4_scratch/s5_probes/zzz_s4_probe_budget_floor.test.ts`,
`.s4_scratch/s5_probes/zzz_s4_probe_door_parity.test.ts`.

---

## 5. Cross-door parity (PPR-30)

**Finding S5-P1 (Door parity / PPR-30, proposed severity: HIGH).**
For a multi-domain interpretive question (e.g. "how do my career and wealth look right
now"), the two doors compile **structurally different floors**:

- **Web door** (`plan_stage.ts` → `compiled_floor_adapter.ts::classifierIntentToCompilerIntent`,
  lines 86-95): picks exactly **one** `IntentClass` via fixed precedence — breadth
  check first, then "for (const d of tuple.domains) { const floor =
  DOMAIN_DEEPDIVE[d]; if (floor) return floor }" — i.e. the **first** domain in the
  tuple's `domains[]` array that has a registered deepdive floor wins, and every other
  domain's floor is **never compiled**. Confirmed live: a tuple with
  `domains: ['career', 'wealth']` compiles ONLY `career_deepdive` (23 mapped
  primitives + 15 unmapped) — the wealth-deepdive floor items are entirely absent from
  the plan.
- **MCP door** (`plan_builder.ts::buildVidhiPlan` → `compiler.ts::compileMultiDomainContract`,
  documented at compiler.ts:26-30 "**UNIONS** the matched deepdive floors... dedup on
  primitive_id+args, primary-first stable order"): for the identical two-domain input,
  compiles **both** `career_deepdive` and `wealth_deepdive` floors and unions them.

This means the same reader, asking the same multi-domain question through the two
doors, receives a **different floor-mandated evidence set** — the MCP door's plan is a
strict superset of the web door's for any question spanning ≥2 deepdive-eligible
domains. This is a direct, reproducible PPR-30 violation, not a cosmetic difference:
the web door's plan silently drops an entire domain's mandated floor coverage that the
compiler is fully capable of providing (the union machinery already exists and is
called by the other door), and nothing in the web door's `LegacyQueryPlan` or wire
output discloses that only one of the two named domains actually got its floor
compiled.

Secondary parity gap, same root cause pair: the MCP door's `buildVidhiPlan` also
returns `adaptive_expansions` (E-3 Anusaraṇa, one-hop chart-adaptive follow-directives,
`plan_builder.ts:44-49`) as a first-class field of the plan; nothing in `plan_stage.ts`
or `PipelinePlan`/`LegacyQueryPlan` (`plan_stage.ts:63-114`) surfaces or consumes
`adaptive_expansions` at all — the web door's `compileFloorForPlan` only pulls
`contract.floor` and `contract.machine_band` (`compiled_floor_adapter.ts:282`),
dropping the `adaptive_expansions` band of the SAME compiled contract entirely. Whether
this is in-scope for S5 vs. a downstream stage (adaptive expansions are meant to be
materialized by the "executor," per plan_builder.ts:47's own comment — possibly S6/S7's
job) is worth a scope check, but the field exists on the compiled contract today and
the web door discards it unconditionally at the plan stage, before any later stage
gets a chance to use it.

- Code anchors: `platform/src/lib/pipeline/compiled_floor_adapter.ts:86-95`
  (`classifierIntentToCompilerIntent`, single-intent precedence) and `:262-309`
  (`compileFloorForPlan`, calls single-intent `compileContract`, not
  `compileMultiDomainContract`) vs `platform-mcp/src/resources/vidhi/plan_builder.ts:60-67`
  (`buildVidhiPlan`, calls `compileMultiDomainContract`) and
  `platform/src/lib/vidhi/compiler.ts:26-30` (union semantics, doc comment).
- Proposed fix class: repoint `compileFloorForPlan` to call `compileMultiDomainContract`
  with the classifier tuple's full `domains[]` array (mirroring the MCP door), the same
  "reuse the SAME resolution path" principle `plan_bridge.ts` already documents as the
  intended discipline for this exact adapter boundary.
- Rung achieved: INTEGRATION (both compiler entry points called live against the real
  registry with an identical two-domain tuple; concrete output diverged as predicted
  from the source-level analysis, not merely inferred from reading code).

---

## Summary of findings (for EDIR_V3 entry, not entered here per instructions)

| id | title | class | proposed severity | pipeline stage |
|---|---|---|---|---|
| S5-C1 | compiled-floor failure signal computed but never consumed by plan_stage.ts | Correctness / §N.8 Earned-Signal | MEDIUM | S5 |
| S5-O1 | completeness receipt uses narrower tool-resolution than actual dispatch (10/40 live_tools misreported as namespace-gap) | Optimality/Correctness | MEDIUM | S5 |
| S5-O2 | predictive-class turns: 0/10 tool-selection efficiency, 14/14 real turns, 0 citations despite full floor dispatch | Optimality | HIGH | S5 (+ S6 synthesis) |
| S5-O3 | plan-latency-share math from query_trace_steps is ~10x overstated because synthesis step latency is never recorded | Optimality (measurement gap) | LOW/informational | S5+S6 boundary |
| S5-F1 | budget_arbiter can zero a floor tool's token_budget while presence-only floor check reports satisfied (dormant — token_budget unused in dispatch today) | Failure-honesty | MEDIUM | S5 |
| S5-P1 | web door compiles only 1 of N domain floors (precedence) vs MCP door's full union — PPR-30 | Door parity | HIGH | S5 |

Numbers for the optimality section, explicit:
- **Floor-coverage completeness:** honest-by-design but under-counts ~25% of the
  registry's live_tool surface as "namespace gap" when it is actually served (S5-O1).
- **Tool-selection efficiency:** **0% (0/10)** for predictive-class turns, 14/14 real
  DB-backed samples reproduced it; too few interpretive-class samples (n=2) to state a
  comparable number for that class.
- **Plan latency share of turn:** **~46%** of the (incompletely-measured) step-sum
  turn, or **~4.8%** of the EDIR E-006 81.3 s live-seed reference turn — reported both
  ways because they diverge ~10x due to a synthesis-step instrumentation gap (S5-O3),
  not because either number alone is wrong.
