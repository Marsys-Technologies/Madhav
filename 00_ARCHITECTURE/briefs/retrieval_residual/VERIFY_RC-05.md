---
artifact: VERIFY_RC-05.md
residual: RC-05 (R-DEAD) — Sweep ALL dead-tool floor injections
brief: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E Cluster 2
branch: res/rc05-dead-tool-sweep
commit_verified: 07179367
verifier: independent VERIFIER agent (did NOT implement)
verdict: ACCEPT (with 2 non-blocking notes; 1 DONE-bar leg brief-sanctioned-deferred to Wave R-C)
date: 2026-07-22
---

# RC-05 Independent Verification — VERDICT: ACCEPT

Verified against `res/rc05-dead-tool-sweep` @ `07179367` (worktree
`.claude/worktrees/wf_2c9867fc-2f8-1`). All checks run by the verifier, not
trusted from the implementer report.

## (a) Tests — rerun independently

- Target file in isolation: `vitest run compiled_floor_adapter.test.ts`
  → **30 passed (30)**, 1.00s. The report's 24→30 count confirmed.
- Broader touched area: `vitest run src/lib/pipeline src/lib/retrieval`
  → **1524 passed | 137 skipped** (138 files), 0 failures.
- `npx tsc --noEmit` → **exit 0, 0 diagnostics**.

The new `RC-05` describe block is **non-tautological**: it resolves every
floor-injected `tool_call` through the real executable resolver
`getToolByName()` (tool_name_bridge.ts:318/398) across **all 11**
`QueryClassEnum.options` (types.ts:48–60 — factual, interpretive, predictive,
cross_domain, discovery, holistic, remedial, cross_native, classical_grounding,
multi_school_triangulation) and asserts the full 14-name WP-1.7 dead set is
never injected. A dead injection would return `undefined` → test fails. Real
guard, not a stub.

## (b) DONE bar (brief §E RC-05, verbatim) vs. what shipped

Bar has three sub-items:

1. "regression tests on the floor adapter assert no floor of ANY class contains
   an unresolvable required item" — **MET.** `compiled_floor_adapter.test.ts`
   new suite does exactly this via `getToolByName` over `QueryClassEnum.options`
   + a dedicated discovery/remedial case. Verified passing.
2. "planner prompt version-bumped with changelog" — **MET.**
   `PLANNER_PROMPT_v2_0.md` v2.8→**v2.9**, `rc05_amendment` frontmatter block +
   `## Changelog` v2.9 entry (and a backfilled v2.8 entry) present and coherent.
3. "a live discovery-class AND a live remedy-class `prashna_ask` trace each
   return `unresolved_tools:[]`" — **NOT captured in this residual — brief-
   sanctioned deferral, not a gap.** Brief §F Wave R-C states verbatim:
   "RC-05's discovery/remedy live traces (its DONE bar) fold into this wave"
   (the post-deploy live-verification wave). The live MCP connector is also
   unauthenticated in this sandbox (auth-required per session notice), so the
   leg is un-runnable here by design. Static evidence strongly predicts PASS
   (see §c). **The Wave R-C verifier MUST capture both live traces before RC-16
   seal.** This is the only outstanding item and it is correctly sequenced.

## (c) Failure-mode hunt (adversarial)

**Premise check — are `resonance_register`/`cluster_atlas` truly dead?** YES at
the execution layer. `tool_name_bridge.ts:410–422` (WP-1.7 block) lists both
under "no registered cap". `getToolByName` resolves via
`TOOL_NAME_TO_URI[name] ?? resolveGeneratedToolUri(name)` (bridge:398); neither
name has a `TOOL_NAME_TO_URI` entry (grep: only `vector_search`→
`marsys://tool/L0/query_classical_texts` (line 109) and `contradiction_register`
→`marsys://tool/L2/query_contradictions` (line 169) among the relevant set).
`router/retrieval_capability_spec.ts:78–96` DOES define descriptor objects for
both — but that is **planner-facing metadata (description/params catalog), not
the execution registry**; it does not make them resolve. The RC-05 test
correctly grounds truth in `getToolByName`, the same resolver that governs
`unresolved_tools` in a live trace. Premise holds.

**Incomplete-sweep check — other injection sites?** Grepped all
`resonance_register`/`cluster_atlas` refs in `platform/src` + `platform-mcp/src`.
Every remaining reference is benign — NONE is a live runtime floor-injector:
- `compiled_floor_adapter.ts:47–53` — `L2_5_TOOLS` *recognition* set (used only
  by `toolsAuthorized.some(... includes ...)` at line 253 to decide whether a
  floor is already present); injection functions (lines 262–288) push only
  `vector_search` + `marsys://tool/L2/query_signals` + `.../traverse_chart_graph`
  — all resolvable. Verified.
- `gateway/b11_floor.ts:26–48` — `B11_FLOOR_TOOL_NAMES` *allow-list* (which
  tools may run pre-floor). Membership of a dead name is harmless; nothing
  injects it.
- `pipelines/shared/b11_floor_inject.ts:24–66` — **DEPRECATED, explicitly
  "NO production caller (only its own unit test)"** (file header). It still
  injects `pattern_register` for predictive (a stale W6.2/W6.3-era body), but
  being caller-less it cannot affect any live trace. Recorded as a hygiene
  follow-up (below), not an RC-05 blocker.
- `consult/route.ts:152` (`inferLayer`), `run_adapter_dispatch.ts:637`
  (token-accounting buckets), `manifest_compressor.ts`, `trace/types.ts`,
  `mcp/epistemics.ts`, `performance/compliance.ts`, `contract/tool_metadata.ts`,
  `jyotish/domain_labels.ts`, `consume/provenance_assembler.ts` — all
  classification / label / provenance / trace-enum maps. None injects.
- `scripts/checkpoints/eval.ts:298,342` — eval-harness fixtures; golden-set
  recalibration is **RC-06**, explicitly a separate residual.

**Banned-substitution check.** Every substitution respects the rule that would
ban it:
- R-DISC drop-no-substitute — `vector_search` is banned for discovery ("Do NOT
  add cgm_graph_walk or vector_search to discovery queries", prompt L444–445).
  Correct to drop with no substitute; `contradiction_register` (live) remains.
- R7b → `vector_search` — not banned for remedial. Correct.
- R11 main → `vector_search` — banned only in the SIGNAL-DENSITY exception
  branch (preserved unchanged). Correct.
- R15 → `vector_search` — not banned for the keyword holistic/interpretive case.
- R7d drop-no-substitute — `vector_search` IS banned in R7d. Correct to drop.

**Consumer/rename check.** Only 2 files changed (planner .md — not compiled —
and one test file). No code symbol renamed; no consumer to miss. tsc clean.

## (d) Scope / must_not_touch

Diff touches exactly: `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` (may_touch:
"PLANNER_PROMPT_v2_x.md") and
`platform/src/lib/pipeline/__tests__/compiled_floor_adapter.test.ts`
(may_touch: platform source). **No** FROZEN orchestrator / WriterBase /
`ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` writer, **no** chart_facts semantics, **no**
`kala_*`/gochara serving, **no** D-4b branch touched. Scope clean.

## Non-blocking notes (do NOT gate RC-05; log for RC-06 / hygiene)

1. **R7d ↔ R15 precedence overlap (prompt-coherence nit).** For a *single-planet
   interpretive* query that *literally contains* "resonance"/"themes"/
   "alignment"/"central patterns", R15 now says include `vector_search` while
   R7d's NEVER-add list bans `vector_search`. Harmless to RC-05's objective —
   both paths avoid dead tools and `vector_search` is live either way, so no
   `unresolved_tools` risk — but the two rules now disagree on a narrow overlap
   the old prompt harmonized (old R7d carved the keyword case). Recommend a
   one-line R15 "except single-planet interpretive (R7d wins)" clause in RC-06
   or a prompt-hygiene follow-up.
2. **`b11_floor_inject.ts` still injects `pattern_register`.** Caller-less /
   deprecated, so out of RC-05's live scope, but it is a lingering dead-tool
   injector. Recommend deletion under RC-15 hygiene (its header already says
   "Safe to remove once the G5b pipeline seam lands").

## Verdict

**ACCEPT.** The residual's own DONE-bar code/prompt legs (regression test +
version bump) are met and independently verified; the sweep is complete for
every live injection site; substitutions honor every ban; scope is clean. The
single remaining DONE-bar leg — live discovery/remedy `prashna_ask` traces — is
explicitly deferred to Wave R-C by the brief's own dependency graph (§F) and is
strongly predicted to pass by the static evidence. RC-05 is closable now; the
Wave R-C verifier owns capturing the two live traces before the RC-16 seal.
