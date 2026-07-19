---
lane: R-3
wave: PG-1 (Paripraśna Grounding Audit)
status: CLOSED
role: real-reasoning lane (planning path + unified-plan-type falsification)
audit_target: 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §1.1 (A6/A7/A8), §9, §6.3
authored_by: Claude Code (Opus 4.8, 1M), Lane R-3 agent, 2026-07-19
attempts: 2 (attempt 1 died mid-response on a transient API error, wrote nothing; this is the clean retry)
findings: 7 (pg1_findings_R-3.jsonl)
---

# PG1 Lane R-3 — Planning Path Trace + Unified-Plan-Type Falsification

READ-ONLY audit. Wrote only to `pg1_findings_R-3.jsonl` and this file. No writes to
`platform/src/**`, `platform-mcp/src/**`, migrations, infra, workflows, or governance
manifests.

## 1. The planner trace ("what does my career look like this year")

Static trace of ONE identical question through every live planner. Result: there are
**FOUR distinct planner surfaces, two live-but-structurally-incompatible, two dead
islands.**

| # | Surface | Wired? | Emits | Has floor/dark/CR/capability_version? |
|---|---|---|---|---|
| 1 | `pipeline_planner.ts:269` `callPipelinePlanner` (web consult) | **LIVE** — `consult/route.ts:436` `runPlanner(...)` | `PipelinePlan` (query_class + LLM-chosen `tool_calls[{tool_name,params,priority,reason}]` + `asset_bundle`) | **NO** — none of it |
| 2 | `plan_builder.ts:52` `buildVidhiPlan` (MCP `plan_retrieval`) | **LIVE** — `server.ts:388` `registerVidhiPlanTool` | `VidhiPlan` (floor + machine_band + `completeness_receipt` served/empty/dark + `capability_version`) | **YES** — all of it |
| 3 | `retrieval/router/router.ts` `route()` "D2 Query Router" | **DEAD ISLAND** — zero production importer (only its own test + barrel) | `RouteResult` (rule classifier → tool chain) | partial |
| 4 | `lib/vidhi/compiler.ts` `compileContract` (D-2 Lane V-1) | **DEAD ISLAND** — zero production importer | `CompiledContract` (a duplicate of #2's compiler) | YES but unused |

**The determinative fact:** for the identical career question, the live web channel
produces a `PipelinePlan` and the live MCP channel produces a `VidhiPlan` — two
non-interoperating plan objects — while a third (retrieval router) and fourth (platform
vidhi compiler) planner implementation sit unwired. The live web decision is one
constrained-LLM call (`pipeline_planner.ts:336` `runAdapter({callType:'planner_fast'...})`,
`temperature:0`, `responseSchema: PipelinePlanInputJsonSchema`); the route then stamps
`query_plan_id`/`query_text`/`audience_tier`/`manifest_fingerprint` (route.ts:779-782) —
note `audience_tier` is still stamped (route.ts:781), in tension with A-35's "excise
audience_tier", flagged for the relevant lane, not pursued here.

The runtime single-pass-vs-agentic split is NOT made by the `lib/pipelines/` selector —
it is inline at `run_adapter_dispatch.ts:314` (`useAgenticLoop && loopConfig ?
runAgenticLoop(...) : adapter.chat(adapterChatReq)`), onfinish hardcoded
`pipelineKind:'agentic'` (run_adapter_dispatch.ts:494).

→ **A-06 verdict: target-state, confirmed UNBUILT.** Reality is worse than the doc's
"three planners": four surfaces, two live-divergent. (PG1-R3-0001)

## 2. A7 / A8 verdicts

**A-07 ("one agentic loop, two doors; MCP gets `prashna_ask`") — PARTIAL (half-built).**
The loop IS extracted into a standalone module `synthesis/agentic_loop.ts:288`
`runAgenticLoop` with a swappable tool executor (`mcp_tool_executor.ts`). But it is NOT
proven channel-agnostic: its ONLY live caller is `run_adapter_dispatch.ts:314` (the
web-route dispatch path, route-coupled per C-2), and the second door **does not exist** —
`grep 'prashna_ask'` across `platform/src` + `platform-mcp/src` = **ZERO hits**; the
apparent matches were the substring of the unrelated horary tool `prashna_undertaking_get`
(`register_p1_synthesis.ts:733`). So "two doors" is one door. Matches R-1's "prashna_ask
= Proposed". (PG1-R3-0002)

**A-08 ("neutral store `conversation_messages` + `message_parts` child rows; replaces
UIMessage blob") — PARTIAL and mis-specified.** `conversation_messages` EXISTS
(`001_baseline.sql:270`), written by `conversation_writer.ts`, read by many live routes —
BUT parts are stored as a JSON **blob column** `parts_json` (GIN-indexed on
`parts_json::TEXT`, `001_baseline.sql:289`), **not** normalized `message_parts` child
rows. So the "child rows" half of A-08 is not the shipped shape — it is still a blob,
merely relocated onto the row. And `UIMessage` remains in active use across ~10 live
surfaces (consult route, continue, export, `AssistantMessage.tsx`, ...) — it has NOT been
replaced. A-08 is neither fully built nor accurate as written. (PG1-R3-0003)

## 3. The `single_pass` full importer list (charge item 2)

**Production importers — exactly TWO, both internal to `lib/pipelines/`:**
- `pipelines/index.ts:9` — barrel re-export `export { singlePassPipeline } from './single_pass'`
- `pipelines/selector.ts:9` — import, used at `selector.ts:22,28`

**Test importers:** `pipelines/__tests__/selector.test.ts:8`,
`single_pass/__tests__/single_pass.test.ts:2`,
`app/api/chat/__tests__/onfinish_parity.golden.test.ts:237`.

**Zero importers outside `lib/pipelines/`.** Crucially, the selector's own exports
(`selectPipelineForRequest`/`getPipeline`/`selectPipelineKind`) also have **no production
importer** — the selector never runs live. `singlePassPipeline` is an INERT descriptor
(`single_pass/index.ts:23` — only `{kind, describe()}`, no `run()`; its own comment: "the
body still lives there [route.ts] pending G5b").

**Precise status (supersedes both prior verdicts):** a *test-load-bearing structural
scaffold, NOT on the runtime path*. The arch-doc's "dead branch / operationally
unreachable" is right that the selector never reaches it; C-3's "conditionally reached,
do not delete" is right that it's not orphan-deletable (barrel + tests break). Neither is
precise. The live single-pass CODE PATH is the inline `adapter.chat` branch at
`run_adapter_dispatch.ts:320`, not the module. (PG1-R3-0004)

## 4. PlanReceipt reality (charge item 3 — reconcile R-2's zero hits)

**Absent from code entirely.** `grep 'PlanReceipt'` across the whole repo matches ONLY
documentation + audit artifacts (the arch doc, briefs, R-1 deliverables) — **zero `.ts`
matches** in `platform/src` or `platform-mcp/src`. No interface, type alias, class, or
construction site anywhere. So R-2's "zero hits" = **absent-from-code-entirely**,
definitively NOT type-only-with-no-instances. The nearest shipped analogue is the MCP
`VidhiPlan` (`plan_builder.ts:29`) + `CompletenessReceipt` (`completeness_receipt.ts`) —
the same idea, never given the name `PlanReceipt` in code. (PG1-R3-0005)

## 5. Dark-item findings (charge item 4)

The "dark" concept is **real and shipped — MCP channel only.** A dark item = a compiled
floor item whose backing primitive has a non-null `known_gap` (a `CR-N` pointer) and was
not served; emitted in `completeness_receipt.ts` `dark[]` as `{floor_item_id, cr_row}`,
`cr_row` matching `/^CR-\d+$/`, guaranteed OPEN/LOGGED (never CLOSED) via
`isCitableKnownGap`. Receipt invariant: `served ∪ empty ∪ dark` = full deduped floor set
(TOTAL), pairwise DISJOINT.

**Concrete count for the traced career question** (`career_deepdive`, 12 floor items):
**5 dark at issuance**, citing:
- **CR-56** — `dhana_yoga_scan` (house-lord yoga detector absent; ELEVATED #1 acharya-grade blocker)
- **CR-64** — `nakshatra_semantics` (never rank)
- **CR-24** — `mechanism_read` (chain/circuit motif not first-class)
- **CR-66** — `taranga_curve` (Phala domain anchors still zero)
- **CR-69** — `intervention_synthesis` (no leverage_index axis)

Registry-wide: 12 `known_gap` primitives out of 114 (CR-16/24/30/37/56/61/64/66/67/68/69/73);
a single-intent plan carries only the subset on its floor. The live web `PipelinePlan`
carries **no** dark concept at all — a channel asymmetry. (PG1-R3-0006)

## 6. THE FALSIFICATION EXERCISE (PC-3) — load-bearing output

**VERDICT: WEEK-SCALE INTEGRATION, NOT A CONTRADICTION.** ~80% of the unified plan type
already exists, unrecognized, as the MCP `VidhiPlan`. No type-theoretic impossibility.

### Sketch of the unified type U

```
type UnifiedPlan = {
  capability_version: string        // content-hash of registry + compiler
  scope_tuple: {intent, domains, width, depth, horizon, intervention?, entitlement}
  items: PlanItem[]                 // floor ∪ machine_band ∪ llm_extensions — ONE addressable set
}
type PlanItem = {
  item_id: string                   // = primitive_id for floor/band; minted id for llm extensions
  band: 'acharya_floor' | 'machine_band' | 'llm_extension'
  tool: string                      // resolved live MCP tool name
  args: Record<string, unknown>     // resolved against chart_id (+ capability_version)
  status: 'served' | 'empty' | 'dark'
  cr_row?: string                   // iff status==='dark'; /^CR-\d+$/, OPEN/LOGGED
  empty_reason?: string             // iff status==='empty'
}
subsumes(a, b): boolean =
  ∀ i ∈ b.items where i.band !== 'llm_extension' :
      ∃ j ∈ a.items with j.item_id === i.item_id     // finite set-containment → decidable
```

### Why this is buildable, not contradictory

The MCP path already realizes almost all of U:
- **floor+machine-band as one addressable set** — DONE. `completeness_receipt.ts:76`
  `uniqueFloorItems()` already collapses `[...floor, ...machine_band]` into one deduped
  set keyed by `primitive_id`.
- **per-item served/empty/dark with CR refs** — DONE. `completeness_receipt.ts` with the
  OPEN/LOGGED CR guarantee.
- **tool+args resolved against capability_version** — DONE. `CompiledFloorItem.live_tool`
  + `compileContract(chart_id)`, versioned by `VIDHI_CAPABILITY_VERSION`
  (`capability_version.ts:44`, a content-hash with a staleness-kill).
- **decidable subsumption** — trivial: both operands are finite sets of string `item_id`s;
  set-containment is decidable.

### Where the real cost lives (the honest week — three gaps, none fatal)

1. **NAMESPACE UNIFICATION (load-bearing).** A-06's actual subsumption need is "does the
   LIVE web plan cover the deterministic floor?" — but web `PipelinePlan.tool_calls` are
   keyed by `tool_name` = "one of the tool_names in CAPABILITY_MANIFEST.json"
   (`types.ts:108`), and its few-shots emit R-alias names
   (`multi_school_signal_lookup`, `convergence_score_lookup`), whereas `VidhiPrimitive`
   keys on `live_tool` = bare MCP tool names (`ganita_chart_facts_get`, ...). These are
   OVERLAPPING-BUT-DISTINCT namespaces. Subsumption is decidable ONLY given a TOTAL map
   `tool_name → primitive_id`; today only a replay-oriented `tool_name_bridge.ts` exists
   (per C-3, not a planner-floor map). Building + CI-verifying that total map is the bulk
   of the week.
2. **LLM band-3 not addressable.** Today band-3 is a free-text `llm_extension_note` on
   `VidhiPlan`, not typed items — so "per-item served/empty/dark" can't cover LLM-chosen
   extensions until they are promoted to `PlanItem`s with minted ids. Modest.
3. **Two runtimes.** Deterministic vidhi is MCP-only; the live web route runs
   `PipelinePlan` with no floor/receipt/dark/capability_version. Unifying = wire the web
   consult route through the already-built vidhi compiler and emit U — which C-2
   independently showed touches `consult/route.ts` (planner call `route.ts:436` + the
   dispatch). So the unification is coupled to the same route reorder C-2 priced.

### Why NOT a contradiction

The only contradiction candidate was "a deterministic floor cannot contain a
non-deterministic LLM plan in one addressable set." It resolves: floor/band items are
deterministic, LLM items are additive-only (`band==='llm_extension'`), and `subsumes` is
DEFINED to ignore `llm_extension` items — determinism of the floor is preserved while the
LLM layer stays per-item accountable. Nothing forces the LLM output to be deterministic;
A-06 only requires the LLM plan be VALIDATED-as-covering the deterministic floor, which
set-containment provides.

### Honest verdict

**A WEEK (5-8 working days)**, dominated by gap #1 (total `tool_name ↔ primitive_id` map
+ CI proof) and gap #3 (route reorder to emit U instead of `PipelinePlan`). NOT a day
(the namespace map + route reorder are real). NOT a contradiction (the type closes; MCP
already runs ~80% of it). The negative-for-contradiction is the value: the architecture's
unified plan type is **INTEGRATION DEBT** (two live divergent planners + two dead
islands), not a design impossibility. (PG1-R3-0007)

## Findings ledger

| id | assumption | class | severity | headline |
|---|---|---|---|---|
| PG1-R3-0001 | A6 | new_defect | high | 4 planner surfaces, 2 live-divergent (PipelinePlan vs VidhiPlan), 2 dead islands |
| PG1-R3-0002 | A7 | partial | medium | loop extracted as module; `prashna_ask` second door = 0 hits (absent) |
| PG1-R3-0003 | A8 | partial | medium | `conversation_messages` exists but parts are a `parts_json` blob, not child rows; UIMessage not retired |
| PG1-R3-0004 | A8 | partial | low | `single_pass` = test-scaffold not on runtime path; full importer list; supersedes arch-doc + C-3 |
| PG1-R3-0005 | A6 | confirmed | informational | `PlanReceipt` absent from code entirely (docs-only); analogue = MCP `VidhiPlan` |
| PG1-R3-0006 | A6 | confirmed | informational | career plan carries 5 dark items citing CR-56/64/24/66/69; MCP-only |
| PG1-R3-0007 | NEW | new_defect | high | FALSIFICATION = WEEK-scale integration, NOT a contradiction; ~80% already in MCP VidhiPlan |

## Cross-lane reconciliations

- **C-3** (single_pass "not dead, conditionally reached") — refined: it is a
  test-load-bearing scaffold NOT on the runtime path; the live single-pass path is the
  inline `adapter.chat` branch, not the selector. See PG1-R3-0004.
- **C-2** (route reorder needed for §12.3) — the unified-plan unification (#3 above) is
  coupled to the SAME `consult/route.ts` reorder C-2 priced; the two workstreams share a
  route touch.
- **R-1** (`PlanReceipt` "zero hits, low confidence") and **R-2** ("zero hits" flagged) —
  reconciled: absent-from-code-entirely, not type-only. See PG1-R3-0005.
- **R-1** (`prashna_ask` "Proposed") — confirmed: zero hits in source. See PG1-R3-0002.

## CORRECTED post-verification (2026-07-19, attempt 2)

Phase-1 verifier REJECTED PG1-R3-0001: its first evidence entry cited
`consult/route.ts:758` for the `runPlanner(...)` quote, but line 758 holds unrelated
`step_done` telemetry (`conversation_id: finalConversationId`). The live planner call
site is actually **`consult/route.ts:436`** — `plan = await runPlanner(` (call spans
436–444), where `runPlanner` is the alias for `callPipelinePlanner` imported at
`route.ts:72`. The `758` was a stale/mis-copied line number; the CLAIM about the call
being the live constrained-LLM planner surface is unchanged and correct.

Corrections applied (line number only; no substantive finding change):
- PG1-R3-0001 evidence[0]: `line 758 → 436`; quote set to verbatim `plan = await runPlanner(`.
- PG1-R3-0001 reality prose: `route.ts:758` → `route.ts:436` (+ note it is imported as `runPlanner` at route.ts:72).
- PG1-R3-0007 reality prose carried the same wrong `route.ts:758` for the planner call site → corrected to `route.ts:436` (same factual error surfaced by this investigation).
- This state doc: the `consult/route.ts:758` in the §1 planner table and the §6 gap-3 prose → both corrected to `route.ts:436`.

The verifier confirmed 7/8 other citations checked out; those were left untouched.
