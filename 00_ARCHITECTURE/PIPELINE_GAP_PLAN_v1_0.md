---
artifact: PIPELINE_GAP_PLAN_v1_0.md
version: 1.0
status: ACTIVE
session_count: 4
authored_by: claude-sonnet-4-6 (architect subagent, Cowork session)
authored_on: 2026-05-11
drives:
  - QP-S1  fix/planner-gap-qp-s1
  - QP-S2  fix/cleanup-qp-s2
  - QP-S3  fix/golden-set-qp-s3
  - QP-S4  fix/eval-governance-qp-s4
prerequisite: Pipeline-Transform-S1 merged to main (PR #15, commit 85dfca5)
convergence_targets:
  avg_tool_recall:           "≥ 0.963"
  avg_tool_precision:        "≥ 0.986"
  avg_asset_bundle_recall:   "≥ 0.971"
  asset_bundle_floor_violations: 0
  new_golden_entries_gate:   "≥ 8/12 rubric score per GT.030+"
---

# PIPELINE GAP PLAN v1.0 — Post-Transform Gap Closure

## §1 Executive Summary

Pipeline-Transform-S1 successfully collapsed the dual `classify()+callLlmPlanner()` architecture
into a single `callPipelinePlanner()→hydrateBundle()→synthesize()` pipeline. The refactor
established `PipelinePlan` (types.ts) as the authoritative contract, eliminated the
`plannerParamsMap` runtime merge, and reduced LLM calls per request from up to 4 to exactly 2.
The eval harness confirmed the new prompt (`PLANNER_PROMPT_v2_0.md` at v2.0.1) meets or exceeds
the v1.7 baseline: recall=0.963, precision=0.986, asset_bundle_recall=0.971 on 29 golden entries.

However, the post-merge commit analysis exposed ten residual gaps. Six are semantic gaps in
the planner prompt: two critical fields present in the schema (`time_window`,
`graph_seed_hints`) have zero prompt rules governing their population, and three query classes
(`discovery`, `cross_domain`, `factual`) are underspecified or untested. Three are housekeeping
gaps: leftover debug console.log statements, a stale import in route.ts pointing to the deleted
`@/lib/router/types` namespace, and untracked eval scratch files. The tenth is a known residual
recall issue on GT.017 (life-path holistic query missing `cgm_graph_walk`).

This plan closes all ten gaps across four parallel Claude Code sessions. Sessions QP-S1, QP-S2,
and QP-S3 are fully parallel with zero file overlap: S1 edits only the planner prompt, S2
edits only code and config files, and S3 edits only the golden set. Session QP-S4 depends on
S1 and S3 being merged to main first; it runs the full expanded eval, verifies all five
convergence gates, and writes the governance close artifacts. All sessions branch from main
post-PR-15 and target the `claude-opus-4-6` executor model.

---

## §2 Gap Register

| ID     | Description                                          | Priority | Closed By |
|--------|------------------------------------------------------|----------|-----------|
| GAP-1  | `time_window` has no prompt rules; eclipse + named-antardasha patterns lost from deleted router/prompt.ts | CRITICAL | QP-S1 |
| GAP-2  | `graph_seed_hints` has no prompt rules; holistic karaka/yoga/dasha-lord pattern lost from deleted fix | HIGH | QP-S1 |
| GAP-3  | `discovery` class: 2 sentences of definition, no tool-selection rule, 0 golden entries | HIGH | QP-S1, QP-S3 |
| GAP-4  | `cross_domain` class: no tool-selection rule, 0 golden entries | MEDIUM | QP-S1, QP-S3 |
| GAP-5  | `factual` class: no tool-selection rule, 0 golden entries | MEDIUM | QP-S1, QP-S3 |
| GAP-6  | GT.017 known recall residual: life-path holistic misses `cgm_graph_walk`; R14a trigger too narrow | MEDIUM | QP-S1 |
| GAP-7  | `cross_native` class: no native-2 data exists | LOW (deferred to M5) | — |
| GAP-8  | Debug console.log calls in StreamingAnswer.tsx + useChatSession.ts (commit b3fcb77) | LOW | QP-S2 |
| GAP-9  | route.ts line 41: stale `import type { QueryPlan } from '@/lib/router/types'` | LOW | QP-S2 |
| GAP-10 | eval-results/ untracked scratch logs; results_gemini_retry6_20260511.json uncommitted | LOW | QP-S2 |

---

## §3 Pipeline Architecture Analysis

### Legacy pipeline (pre-Pipeline-Transform-S1)

```
query
  │
  ├─► classify()          — router/router.ts, 8-class enum from QueryPlan (router/types.ts)
  │                          one LLM call
  │
  ├─► callLlmPlanner()    — manifest_planner.ts, 6-class PlanSchema
  │     │                    one LLM call
  │     └─► plannerParamsMap   — runtime merge: graft classify()'s query_class + domains
  │                              onto the 6-class tool plan. P2/P6/P8 incoherence.
  │
  ├─► rule_composer.ts    — deterministic asset selection from composition_rules.ts
  │                          (now deleted Phase 4)
  │
  ├─► context_assembler.ts — 3rd LLM call to produce synthesis guidance
  │                           (CONTEXT_ASSEMBLY_ENABLED flag)
  │
  └─► synthesis LLM        — 4th LLM call (worst case)
```

The dual-planner architecture produced plans where `query_class` (from classify) and
tool selection (from the 6-class manifest planner) were frequently out of sync. `plannerParamsMap`
was a silent runtime patch that masked the taxonomy mismatch.

### New pipeline (post-Pipeline-Transform-S1)

```
query
  │
  └─► callPipelinePlanner()   — pipeline_planner.ts
        │  system prompt: PLANNER_PROMPT_v2_0.md §3+§4 (loaded lazily via readFileSync)
        │  one LLM call (tool-call mode: submit_plan)
        │  emits: PipelinePlan — 8-class query_class, asset_bundle[], tool_calls[],
        │         synthesis_guidance, time_window, graph_seed_hints, ...
        │
        ├─► PipelinePlanSchema.safeParse()  — Zod validation; fail → HTTP 422 (no fallback)
        │
        ├─► hydrateBundle()    — bundle_hydrator.ts
        │     resolves asset_bundle[] → GCS content
        │     enforces FORENSIC+CGM floor
        │
        ├─► retrieval layer    — budget_arbiter.ts + tool execution
        │
        └─► synthesis LLM      — 2nd and final LLM call
              receives: hydrated assets + tool results + synthesis_guidance
```

**What changed:** single schema contract (`PipelinePlan`) replaces the dual `PlanSchema`+`QueryPlan`
pair; `plannerParamsMap` deleted; `rule_composer.ts`+`composition_rules.ts` deleted; 
`context_assembler.ts` deleted; LLM calls per request reduced to exactly 2.

**What is not yet wired:** `time_window` and `graph_seed_hints` are present in the schema and
validated by Zod, but the planner prompt has zero rules instructing the model when to populate
them. The schema contract is complete; the prompt-level behavioral specification is not.

---

## §4 Session Definitions

---

### QP-S1 — Planner Prompt Gap Closure

| Field | Value |
|-------|-------|
| Session ID | QP-S1 |
| Branch | `fix/planner-gap-qp-s1` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Madhav-gap` |
| Executor model | `claude-opus-4-6` |
| Estimated duration | 45–75 min |
| Closes gaps | GAP-1, GAP-2, GAP-3, GAP-4, GAP-5, GAP-6 |

**may_touch:**
- `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`

**must_not_touch:** every other file in the repository.

**Work breakdown:**

1. **R-TW1 (time_window — eclipse trigger).** Add a new rule block after the existing TOOL_CALLS
   HARD RULES section. Rule: when a query contains "eclipse" (solar or lunar, predictive scope),
   set `eclipse_query: true` (via `forward_looking` flag) and populate `time_window` with the
   window that brackets the queried eclipse event. Default window: `{ start: <today>, end: <today+90d> }`
   if no explicit dates are stated; use stated dates when the query names them. Emit `planets: ["Moon"]`
   for lunar eclipses, `planets: ["Sun", "Moon"]` for solar. Hypothesis: restores F016/F019 eclipse
   pattern from deleted router/prompt.ts (commit 099937e).

2. **R-TW2 (time_window — named antardasha with date range).** Rule: when a query names a
   specific antardasha period AND specifies a date range or year span (e.g. "my Mercury
   antardasha from 2025 to 2027"), set `dasha_context_required: true` and populate `time_window`
   with `{ start: "<year>-01-01", end: "<year>-12-31" }` anchored to the stated range. When
   no exact dates are given but the named period is resolvable from the native's dasha schedule,
   emit the resolved window. Hypothesis: restores F019 named-antardasha temporal scoping from
   commit 099937e.

3. **R-GSH (graph_seed_hints population).** Rule: for HOLISTIC or INTERPRETIVE queries that
   explicitly reference atmakaraka/amatyakaraka or other karakas by name, named yogas (Lakshmi
   Yoga, Sasha Yoga, etc.), or explicit dasha lords by name in an architectural/mapping context,
   populate `graph_seed_hints` with the relevant KRK.*, YOG.*, and DSH.* namespace node IDs
   derived from the query signals. Do not populate graph_seed_hints for queries that do not
   name specific karaka, yoga, or dasha-lord nodes. Hypothesis: restores F022/F024 holistic
   graph-seed pattern from deleted commit 884b99c.

4. **R-DISC (discovery class tool rule).** Expand the discovery query class definition from
   2 sentences to a full tool-selection rule. Discovery class should always produce all four
   L2.5 discovery registers as a set: `pattern_register` (priority 1) + `contradiction_register`
   (priority 1) + `resonance_register` (priority 2) + `cluster_atlas` (priority 2). Add
   `msr_sql` at priority 3 only when the discovery query names a specific domain. Asset bundle
   for discovery: FORENSIC (floor) + CGM (floor) + UCN (priority 2) + CDLM (priority 2).
   Hypothesis: fills GAP-3 discovery class specification.

5. **R-CDOM (cross_domain tool rule).** Add an explicit tool-selection rule for cross_domain
   class: use `msr_sql` (priority 1) + `vector_search` (priority 1, one call per named domain)
   as the default set. Add `cgm_graph_walk` at priority 2 when the query contains explicit
   domain-interaction language ("how does X affect Y", "interaction between", "relationship
   between X and Y domains"). Asset bundle for cross_domain: FORENSIC + CGM (floors) + UCN
   (priority 2) + CDLM (priority 2, as the cross-domain linkage surface). Hypothesis: fills
   GAP-4 cross_domain specification.

6. **R-FACT (factual tool rule clarification).** Tighten the factual class rule: factual
   queries use exactly one tool — `msr_sql` for chart-lookup queries ("what is my lagna",
   "which house is Saturn in") or `remedial_codex_query` for codex-lookup factual queries.
   No synthesis_guidance. No asset bundle beyond FORENSIC + CGM floors. Expected output shape:
   `single_answer`. Hypothesis: fills GAP-5 factual specification.

7. **R14a amendment (GT.017 fix).** Expand R14a's trigger phrases for `cgm_graph_walk` in
   holistic queries. Current R14a: fires on "structural chart topology" or "domain interaction"
   language. Add to the trigger list: "life path", "life arc", "arc of my life", "overall life
   direction", "life trajectory". Hypothesis: enables cgm_graph_walk on the GT.017 query
   "Give me a comprehensive overview of my life path across all major domains" (recall 0.75 →
   expected 1.0 on this entry).

8. **Version bump.** Update the YAML frontmatter `version:` field from `2.0.1` to `2.1`.
   Update `patched_on:` to today's date. Record all 6 new rules in a `gap_closure_patch:` block
   in the frontmatter with hypothesis statements.

9. **§4 few-shot additions.** Add the following six new examples to §4 (after the existing
   eleven, numbered 4.12–4.17):
   - 4.12: Eclipse predictive query with `time_window` + `planets: ["Moon"]`
   - 4.13: Named antardasha + date range with `time_window` + `dasha_context_required: true`
   - 4.14: Holistic karaka/yoga architectural query with `graph_seed_hints`
   - 4.15: Discovery class query — all four L2.5 registers
   - 4.16: Cross_domain query — two named domains, `msr_sql` + `vector_search` ×2
   - 4.17: Factual class query — single `msr_sql` call, no synthesis_guidance

**Acceptance criteria:**

1. All six new rules (R-TW1, R-TW2, R-GSH, R-DISC, R-CDOM, R-FACT/R14a) are present in
   the system prompt body (§3), each with an explicit `Hypothesis:` annotation.
2. The output schema block (§2 interface) in the document is NOT modified — no new fields,
   no type changes.
3. Rules R1–R20 and R21–R26 that govern categories with passing golden entries are not
   modified except for the R14a amendment (which is a trigger-list expansion, not a semantic
   change to the rule's core).
4. YAML frontmatter `version:` reads `2.1` and `gap_closure_patch:` block is present.
5. Six new few-shot examples (4.12–4.17) are present in §4, each containing a complete
   `expected_plan` with `asset_bundle[]`, `tool_calls[]`, and any relevant new fields
   (`time_window`, `graph_seed_hints`).

**Worktree setup command:**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add ../Madhav-gap -b fix/planner-gap-qp-s1
```

---

### QP-S2 — Code Cleanup

| Field | Value |
|-------|-------|
| Session ID | QP-S2 |
| Branch | `fix/cleanup-qp-s2` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Madhav-cleanup` |
| Executor model | `claude-opus-4-6` |
| Estimated duration | 20–35 min |
| Closes gaps | GAP-8, GAP-9, GAP-10 |

**may_touch:**
- `platform/src/components/consume/StreamingAnswer.tsx`
- `platform/src/hooks/useChatSession.ts`
- `platform/src/app/api/chat/consume/route.ts`
- `.gitignore`
- `platform/scripts/eval/results_gemini_retry6_20260511.json` (delete or move)

**must_not_touch:** every other file in the repository, especially
`00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`, `platform/tests/eval/planner_golden_set.json`,
and any file under `platform/src/lib/pipeline/`.

**Work breakdown:**

1. **Remove debug console.logs from StreamingAnswer.tsx.** Identify all `console.log` calls
   introduced in commit b3fcb77. Remove them or gate with `if (process.env.NODE_ENV !== 'production')`.
   Do not remove any console.log that was present before b3fcb77 (check git blame).

2. **Remove debug console.logs from useChatSession.ts.** Same procedure as step 1 for this
   file.

3. **Fix stale import in route.ts.** Line 41 currently reads:
   ```ts
   import type { QueryPlan } from '@/lib/router/types'
   ```
   The `@/lib/router/types` module was deleted in Pipeline-Transform-S1. Replace with:
   ```ts
   import type { PipelinePlan } from '@/lib/pipeline/types'
   ```
   Verify that `QueryPlan` is not referenced anywhere else in route.ts. If the identifier
   `QueryPlan` appears in any type annotation in the file, replace all occurrences with
   `PipelinePlan`. Run `tsc --noEmit` to confirm no type errors remain.

4. **Add eval-results/ to .gitignore.** Append the following to `.gitignore`:
   ```
   # Eval scratch logs (committed results live in platform/tests/eval/)
   eval-results/
   platform/scripts/eval/eval_results_*.json
   platform/scripts/eval/results_*.json
   ```

5. **Handle results_gemini_retry6_20260511.json.** Determine if this file contains unique
   eval data worth preserving. If it does, move it to `platform/tests/eval/` with a
   descriptive rename (e.g. `eval_results_gemini_retry6_20260511.json`). If it is a
   scratch/duplicate, delete it. Either way, ensure the .gitignore pattern from step 4
   covers the source location so future scratch runs do not pollute the tree.

**Acceptance criteria:**

1. `git diff b3fcb77..HEAD -- platform/src/components/consume/StreamingAnswer.tsx` shows
   no `console.log` calls remaining from that commit.
2. `git diff b3fcb77..HEAD -- platform/src/hooks/useChatSession.ts` shows no `console.log`
   calls remaining from that commit.
3. `grep -r "@/lib/router/types" platform/src/` returns zero matches.
4. `cd platform && npx tsc --noEmit` exits 0.
5. `git status` shows `eval-results/` and `platform/scripts/eval/results_*.json` as
   ignored (not untracked).

**Worktree setup command:**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add ../Madhav-cleanup -b fix/cleanup-qp-s2
```

---

### QP-S3 — Golden Set Expansion

| Field | Value |
|-------|-------|
| Session ID | QP-S3 |
| Branch | `fix/golden-set-qp-s3` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Madhav-eval` |
| Executor model | `claude-opus-4-6` |
| Estimated duration | 45–60 min |
| Closes gaps | GAP-1/2/3/4/5 test coverage |

**may_touch:**
- `platform/tests/eval/planner_golden_set.json`

**must_not_touch:** every other file in the repository. In particular, do NOT modify
`PLANNER_PROMPT_v2_0.md` or any source file.

**Work breakdown:**

Add GT.030–GT.046 (17 new entries) to the `entries` array. All entries must follow the
existing schema: `id`, `query`, `query_class`, `category`, `expected_tools`, `required_tools`,
`forbidden_tools`, `notes`, `required_asset_ids`. The `notes` field should state why the
expected plan is correct (cite prompt rules by number where applicable). Bump
`"$schema_version"` to `"1.2"` and update `category_distribution` to include the new counts.

**GT.030–GT.032: factual class (3 entries)**

- GT.030: `"What is my lagna?"` — query_class: factual, expected: [msr_sql], required: [msr_sql],
  forbidden: [cgm_graph_walk, cluster_atlas, resonance_register], required_asset_ids: [FORENSIC, CGM].
  Notes: Single chart-lookup. R-FACT: 1 tool, no synthesis_guidance. expected_output_shape: single_answer.

- GT.031: `"Which house is Jupiter placed in?"` — query_class: factual, expected: [msr_sql],
  required: [msr_sql], forbidden: [vector_search, pattern_register], required_asset_ids: [FORENSIC, CGM].
  Notes: Positional lookup — one msr_sql call sufficient.

- GT.032: `"What gemstone does the Marakacharya prescribe for Venus?"` — query_class: factual,
  expected: [remedial_codex_query], required: [remedial_codex_query], forbidden: [msr_sql, vector_search],
  required_asset_ids: [FORENSIC, CGM].
  Notes: Codex lookup factual — no chart analysis required.

**GT.033–GT.035: discovery class (3 entries)**

- GT.033: `"What's the most interesting or unusual thing about my chart?"` — query_class: discovery,
  expected: [pattern_register, contradiction_register, resonance_register, cluster_atlas],
  required: [pattern_register, contradiction_register], forbidden: [remedial_codex_query],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: R-DISC: all 4 L2.5 registers. Open-ended exploration — no domain anchor.

- GT.034: `"Surprise me — what patterns in my chart haven't I asked about yet?"` — query_class: discovery,
  expected: [pattern_register, contradiction_register, resonance_register, cluster_atlas],
  required: [pattern_register, cluster_atlas], forbidden: [remedial_codex_query, msr_sql],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: Classic discovery trigger language. msr_sql forbidden: no domain signal.

- GT.035: `"What stands out in my career domain that I might be overlooking?"` — query_class: discovery,
  expected: [pattern_register, contradiction_register, resonance_register, cluster_atlas, msr_sql],
  required: [pattern_register, msr_sql], forbidden: [remedial_codex_query],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: Discovery with named domain ("career") — msr_sql added at priority 3 per R-DISC exception.

**GT.036–GT.038: cross_domain class (3 entries)**

- GT.036: `"How does my Mars affect both my career and my relationships?"` — query_class: cross_domain,
  expected: [msr_sql, vector_search], required: [msr_sql, vector_search], forbidden: [remedial_codex_query],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: R-CDOM: two named domains → msr_sql + vector_search ×2 (one per domain).

- GT.037: `"What is the relationship between my spiritual growth and financial stability in my chart?"` —
  query_class: cross_domain, expected: [msr_sql, vector_search, cgm_graph_walk],
  required: [msr_sql, vector_search], forbidden: [remedial_codex_query, pattern_register],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: Two domains named + "relationship between" interaction language → cgm_graph_walk added per R-CDOM.

- GT.038: `"Tell me how career, health, and relationships are connected in my chart."` —
  query_class: cross_domain, expected: [msr_sql, vector_search, cgm_graph_walk],
  required: [msr_sql, cgm_graph_walk], forbidden: [remedial_codex_query, pattern_register],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: Three domains named + "connected" interaction language → cgm_graph_walk required.

**GT.039–GT.040: time_window population (2 entries)**

- GT.039: `"Will there be any significant lunar eclipses affecting me in the next 3 months?"` —
  query_class: predictive, expected: [msr_sql, pattern_register], required: [msr_sql, pattern_register],
  forbidden: [vector_search, cgm_graph_walk], required_asset_ids: [FORENSIC, CGM, LEL].
  Notes: Eclipse trigger → R-TW1: time_window required in plan, planets: ["Moon"]. Transit
  predictive — R7c bans vector_search. Verify plan includes time_window field populated.
  Add field: `required_plan_fields: ["time_window"]`.

- GT.040: `"What can I expect during my Mercury antardasha from 2025 to 2027?"` —
  query_class: predictive, expected: [msr_sql, pattern_register], required: [msr_sql, pattern_register],
  forbidden: [vector_search, remedial_codex_query], required_asset_ids: [FORENSIC, CGM, LEL].
  Notes: Named antardasha + date range → R-TW2: dasha_context_required: true, time_window:
  {start: "2025-01-01", end: "2027-12-31"}. Add field: `required_plan_fields: ["time_window", "dasha_context_required"]`.

**GT.041–GT.042: graph_seed_hints population (2 entries)**

- GT.041: `"Map out the architectural role of my Atmakaraka and Amatyakaraka across all major yogas."` —
  query_class: holistic, expected: [msr_sql, cgm_graph_walk, cluster_atlas, pattern_register],
  required: [msr_sql, cgm_graph_walk], forbidden: [remedial_codex_query, resonance_register],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: Explicit AK/AmK + yoga mapping → R-GSH: graph_seed_hints required with KRK.* + YOG.* entries.
  Add field: `required_plan_fields: ["graph_seed_hints"]`.

- GT.042: `"How do Lakshmi Yoga and Sasha Yoga interact with my current Mercury mahadasha?"` —
  query_class: interpretive, expected: [msr_sql, pattern_register, cgm_graph_walk],
  required: [msr_sql, pattern_register], forbidden: [remedial_codex_query, resonance_register],
  required_asset_ids: [FORENSIC, CGM, UCN].
  Notes: Named yogas + named dasha lord → R-GSH: graph_seed_hints with YOG.LAKSHMI, YOG.SASHA,
  DSH.MD.MERCURY. Add field: `required_plan_fields: ["graph_seed_hints"]`.

**GT.043–GT.044: additional predictive edge cases (2 entries)**

- GT.043: `"When is the most favorable window for career advancement in the next 2 years?"` —
  query_class: predictive, expected: [msr_sql, pattern_register],
  required: [msr_sql, pattern_register], forbidden: [vector_search, cgm_graph_walk],
  required_asset_ids: [FORENSIC, CGM, LEL].
  Notes: Temporal window predictive — R7a: pattern_register required. No transit language so R7c
  transit ban does not apply; but vector_search still forbidden (no domain document signal).

- GT.044: `"Will my health improve after my Saturn mahadasha ends in 2027?"` —
  query_class: predictive, expected: [msr_sql, pattern_register],
  required: [msr_sql, pattern_register], forbidden: [vector_search, remedial_codex_query],
  required_asset_ids: [FORENSIC, CGM, LEL].
  Notes: Mahadasha end event + health domain + year-anchored → time_window encouraged.
  No remedial prescription asked, so remedial_codex_query forbidden.

**GT.045: GT.017 life-path variant (1 entry)**

- GT.045: `"Give me an overview of the arc of my life across all major domains."` —
  query_class: holistic, expected: [msr_sql, cgm_graph_walk, cluster_atlas, pattern_register],
  required: [msr_sql, cgm_graph_walk], forbidden: [remedial_codex_query, resonance_register],
  required_asset_ids: [FORENSIC, CGM, UCN, CDLM].
  Notes: "arc of my life" is an R14a amended trigger for cgm_graph_walk (GAP-6 fix). Variant of
  GT.017 ("life path") using synonym phrasing to verify R14a covers the trigger list.

**GT.046: cross_native stub (deferred marker, 1 entry)**

- GT.046: `"[DEFERRED — M5] Compare my chart with my partner's chart for relationship compatibility."` —
  query_class: cross_native, category: deferred, expected_tools: [],
  required_tools: [], forbidden_tools: [], required_asset_ids: [],
  notes: "No native-2 data exists. Deferred to M5 per GAP-7. This entry holds the cross_native
  slot to satisfy the all-8-classes coverage requirement; smoke_runner should skip entries
  with empty expected_tools."

**Schema changes in golden set header:**

```json
{
  "$schema_version": "1.2",
  "category_distribution": {
    "remedial": 6,
    "interpretive": 7,
    "predictive": 9,
    "holistic": 6,
    "planetary": 3,
    "edge_case": 5,
    "factual": 3,
    "discovery": 3,
    "cross_domain": 3,
    "deferred": 1
  }
}
```

**Acceptance criteria:**

1. All 8 query classes now have ≥ 2 golden entries with non-empty `expected_tools` (excluding
   the deferred cross_native stub).
2. `time_window` requirement is captured in at least 2 entries (GT.039, GT.040) via the
   `required_plan_fields` extension field.
3. `graph_seed_hints` requirement is captured in at least 2 entries (GT.041, GT.042) via
   the `required_plan_fields` extension field.
4. `"$schema_version"` reads `"1.2"` in the file header.
5. All 17 new entries parse without error when loaded by `planner_smoke_runner.ts`
   (entries with empty `expected_tools` are skipped by the runner's existing degenerate-entry
   guard).

**Worktree setup command:**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add ../Madhav-eval -b fix/golden-set-qp-s3
```

---

### QP-S4 — Full Eval + Governance

| Field | Value |
|-------|-------|
| Session ID | QP-S4 |
| Branch | `fix/eval-governance-qp-s4` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Madhav-finalize` |
| Executor model | `claude-opus-4-6` |
| Estimated duration | 30–60 min (includes up to 3 eval iteration rounds) |
| Closes gaps | Governance close for all gaps; eval verification |
| **Depends on** | QP-S1 merged to main AND QP-S3 merged to main |

**may_touch:**
- `platform/tests/eval/eval_results_pipeline_gap_s1.json` (CREATE — eval output)
- `platform/tests/eval/REGRESSION_NOTES_v2_1.md` (CREATE)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (append pipeline_gap_plan_s1 block)
- `00_ARCHITECTURE/SESSION_LOG.md` (append entry)
- `00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md` (set `status: COMPLETE`)

**must_not_touch:** `PLANNER_PROMPT_v2_0.md`, `planner_golden_set.json`, any source code file,
any worktree from QP-S1/S2/S3.

**Work breakdown:**

1. **Confirm prerequisites.** Verify `git log --oneline -5` shows both QP-S1 and QP-S3
   squash-merge commits on main. Verify `PLANNER_PROMPT_v2_0.md` frontmatter reads `version: 2.1`
   and `planner_golden_set.json` `$schema_version` reads `"1.2"` with 46 entries.

2. **Run full eval.**
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Madhav-finalize/platform && \
   PLANNER_MODEL_ID=claude-opus-4-6 \
   npx tsx --conditions=react-server \
     tests/eval/planner_smoke_runner.ts \
     2>eval_stderr.log \
   | tee tests/eval/eval_results_pipeline_gap_s1.json
   ```
   If NIM (`nvidia/llama-3.3-nemotron-super-49b-v1`) is available, run a parallel eval
   with it for comparison; store results as `eval_results_pipeline_gap_s1_nim.json`. NIM
   availability is not a blocker — claude-opus-4-6 is the authoritative eval model for this
   session.

3. **Verify convergence gates.** Parse `eval_results_pipeline_gap_s1.json` and confirm:
   ```
   avg_tool_recall           ≥ 0.963
   avg_tool_precision        ≥ 0.986
   avg_asset_bundle_recall   ≥ 0.971
   asset_bundle_floor_violations = 0
   All GT.030–GT.045 entries: pass = true  (rubric score ≥ 8/12)
   ```
   If any gate fails, proceed to step 4. If all gates pass, skip to step 5.

4. **Diagnostic iteration (up to 3 rounds).** For each failing entry:
   a. Identify which prompt rule is misapplied or absent.
   b. Propose a minimal targeted edit to `PLANNER_PROMPT_v2_0.md` (QP-S1 may have
      introduced subtle regressions). Any prompt edit in this step must be recorded in
      `REGRESSION_NOTES_v2_1.md` with: the entry ID, the predicted vs expected tool set,
      the diagnosed rule gap, and the patch applied.
   c. Re-run the eval. Repeat up to 3 rounds.
   d. If convergence is not achieved after 3 rounds, document the residual gaps in
      `REGRESSION_NOTES_v2_1.md` with a `status: RESIDUAL` marker and a proposed fix for
      the next session. Do NOT block the governance close on residuals that do not regress
      the existing 29-entry baseline.

5. **Write REGRESSION_NOTES_v2_1.md.** Format:
   ```markdown
   ---
   artifact: REGRESSION_NOTES_v2_1.md
   eval_run: eval_results_pipeline_gap_s1.json
   prompt_version: 2.1
   golden_set_version: 1.2
   total_entries: 46
   ---
   ## Summary
   ## New entries (GT.030–GT.045) — per-entry scores
   ## Baseline entries (GT.001–GT.029) — regression check
   ## Residuals (if any)
   ## Next session recommendations
   ```

6. **Update CURRENT_STATE_v1_0.md.** Append a `pipeline_gap_plan_s1:` block under the
   `active_plan_rows:` section:
   ```yaml
   pipeline_gap_plan_s1:
     status: COMPLETE
     merged_sessions: [QP-S1, QP-S2, QP-S3]
     eval_file: platform/tests/eval/eval_results_pipeline_gap_s1.json
     prompt_version: 2.1
     golden_set_version: "1.2"
     entry_count: 46
     convergence_gates_met: true   # or list which gates were residual
   ```

7. **Append SESSION_LOG.md entry.** Follow the SESSION_LOG_SCHEMA_v1_0.md format.
   Include: session_id (e.g. `PGP-S4-close`), branches merged, eval gate outcomes,
   artifacts created, next session pointer.

8. **Mark this plan COMPLETE.** Edit `PIPELINE_GAP_PLAN_v1_0.md` YAML frontmatter:
   `status: COMPLETE`, add `completed_on: <date>`.

**Acceptance criteria:**

1. `eval_results_pipeline_gap_s1.json` exists in `platform/tests/eval/` and all five
   convergence gates are met (or residuals are documented per step 4d).
2. `REGRESSION_NOTES_v2_1.md` exists with all five sections populated and per-entry
   scores for GT.030–GT.045.
3. `SESSION_LOG.md` has a new entry for this session following the schema.
4. `CURRENT_STATE_v1_0.md` has the `pipeline_gap_plan_s1:` block.
5. `PIPELINE_GAP_PLAN_v1_0.md` frontmatter reads `status: COMPLETE`.

**Worktree setup command (run AFTER QP-S1 and QP-S3 are merged to main):**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git pull origin main
git worktree add ../Madhav-finalize -b fix/eval-governance-qp-s4
```

---

## §5 Parallelization Guide

All three parallel worktrees (QP-S1, QP-S2, QP-S3) must be created from the same main
HEAD commit (post-PR-15 merge, commit 85dfca5 or later). Run these commands in sequence
before spawning the executor sessions:

```bash
# 0. Confirm starting point
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main
git log --oneline -3   # should show 85dfca5 or the PR-15 squash merge as HEAD

# 1. QP-S1 worktree (prompt gap closure)
git worktree add ../Madhav-gap -b fix/planner-gap-qp-s1

# 2. QP-S2 worktree (code cleanup)
git worktree add ../Madhav-cleanup -b fix/cleanup-qp-s2

# 3. QP-S3 worktree (golden set expansion)
git worktree add ../Madhav-eval -b fix/golden-set-qp-s3

# 4. Verify all three worktrees are live
git worktree list
# Expected output:
#   /Users/Dev/Vibe-Coding/Apps/Madhav          <hash> [main]
#   /Users/Dev/Vibe-Coding/Apps/Madhav-gap      <hash> [fix/planner-gap-qp-s1]
#   /Users/Dev/Vibe-Coding/Apps/Madhav-cleanup  <hash> [fix/cleanup-qp-s2]
#   /Users/Dev/Vibe-Coding/Apps/Madhav-eval     <hash> [fix/golden-set-qp-s3]
```

**File-overlap verification** (confirm zero conflict surface before spawning):
```bash
# These three greps should produce zero cross-overlap results
echo "QP-S1 touches:"
echo "  00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md"

echo "QP-S2 touches:"
echo "  platform/src/components/consume/StreamingAnswer.tsx"
echo "  platform/src/hooks/useChatSession.ts"
echo "  platform/src/app/api/chat/consume/route.ts"
echo "  .gitignore"

echo "QP-S3 touches:"
echo "  platform/tests/eval/planner_golden_set.json"
```

No file appears in more than one session's `may_touch` list. Merge conflicts between QP-S1,
QP-S2, and QP-S3 are structurally impossible.

---

## §6 Merge Order and Conflict Analysis

### Merge order

```
Parallel phase (any order within the group):
  fix/planner-gap-qp-s1  →  squash-merge to main
  fix/cleanup-qp-s2      →  squash-merge to main
  fix/golden-set-qp-s3   →  squash-merge to main

Sequential phase (must follow all three above):
  git pull origin main   (in Madhav-finalize after QP-S1 + QP-S3 are merged)
  fix/eval-governance-qp-s4  →  squash-merge to main
```

### Conflict analysis

| Pair | Conflict risk | Rationale |
|------|---------------|-----------|
| QP-S1 ∩ QP-S2 | None | Disjoint file sets. S1 touches only the prompt MD; S2 touches only TS/TSX source + .gitignore |
| QP-S1 ∩ QP-S3 | None | S1 touches the prompt; S3 touches only the golden set JSON |
| QP-S2 ∩ QP-S3 | None | S2 touches source + config; S3 touches only the golden set JSON |
| Any S1/S2/S3 ∩ QP-S4 | None by design | S4 only creates new files or appends to governance docs. It does NOT re-edit the prompt or golden set |

No merge conflicts are expected. If a conflict does arise (e.g. from a hotfix merged to main
between S1/S2/S3), resolve it in the affected branch with `git rebase main` before merging.

### QP-S4 trigger condition

QP-S4 must not start until both QP-S1 and QP-S3 are merged to main. QP-S2 can be merged
before or after QP-S4 starts — the code cleanup has no eval dependency. Recommended order:
merge all three parallel sessions first, then spawn QP-S4.

---

## §7 Convergence Targets

These five gates define overall success for this plan. All must be met (or have documented
residuals per QP-S4 step 4d) before QP-S4 is allowed to mark the plan COMPLETE.

| Gate | Target | Measurement |
|------|--------|-------------|
| avg_tool_recall | ≥ 0.963 | `eval_results_pipeline_gap_s1.json`.aggregate.avg_tool_recall — must not regress from pre-gap-closure baseline |
| avg_tool_precision | ≥ 0.986 | `eval_results_pipeline_gap_s1.json`.aggregate.avg_tool_precision — must not regress |
| avg_asset_bundle_recall | ≥ 0.971 | `eval_results_pipeline_gap_s1.json`.aggregate.avg_asset_bundle_recall |
| asset_bundle_floor_violations | = 0 | Every entry must have FORENSIC + CGM in predicted asset_bundle |
| new_entries_gate | ≥ 8/12 rubric per GT.030–GT.045 | All 16 scorable new entries must pass the smoke runner's required_hit gate and achieve recall ≥ 0.75 and precision ≥ 0.75 |

**Regression policy:** any eval run that degrades avg_tool_recall below 0.963 or
avg_tool_precision below 0.986 on the original 29 entries is a regression and must be
diagnosed and fixed before QP-S4 closes. Regressions on the original 29 entries take
precedence over new-entry failures.

**Eval command (authoritative):**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-finalize/platform && \
PLANNER_MODEL_ID=claude-opus-4-6 \
npx tsx --conditions=react-server \
  tests/eval/planner_smoke_runner.ts \
  2>eval_stderr.log \
| tee tests/eval/eval_results_pipeline_gap_s1.json
```

---

## §8 How to Start

Follow these steps in order to kick off the first parallel sessions.

**Step 1 — Confirm main is at the correct baseline.**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main && git pull origin main
git log --oneline -5
# Look for the PR-15 squash-merge (Pipeline-Transform-S1) in the top 5 entries.
# Confirm PLANNER_PROMPT_v2_0.md version is 2.0.1 (not yet 2.1).
head -6 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md
```

**Step 2 — Create the three parallel worktrees.**
```bash
git worktree add ../Madhav-gap     -b fix/planner-gap-qp-s1
git worktree add ../Madhav-cleanup -b fix/cleanup-qp-s2
git worktree add ../Madhav-eval    -b fix/golden-set-qp-s3
git worktree list   # verify all four paths are shown
```

**Step 3 — Spawn QP-S1 (highest priority — prompt gap closure).**

Open a new Claude Code session (claude-opus-4-6) with working directory
`/Users/Dev/Vibe-Coding/Apps/Madhav-gap`. Provide the executor brief:

> "You are executing session QP-S1 of PIPELINE_GAP_PLAN_v1_0.md. Your working directory is
> /Users/Dev/Vibe-Coding/Apps/Madhav-gap on branch fix/planner-gap-qp-s1. You may only touch
> 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md. Implement the 8 work items defined in §4/QP-S1.
> When done, run: git add 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md && git commit -m 'fix(planner): close GAP-1..6, bump prompt to v2.1' && git push -u origin fix/planner-gap-qp-s1"

**Step 4 — Spawn QP-S2 and QP-S3 simultaneously with QP-S1.**

QP-S2 working directory: `/Users/Dev/Vibe-Coding/Apps/Madhav-cleanup`, branch
`fix/cleanup-qp-s2`. Executor brief: implement §4/QP-S2 work items (5 steps), run tsc --noEmit,
commit and push.

QP-S3 working directory: `/Users/Dev/Vibe-Coding/Apps/Madhav-eval`, branch
`fix/golden-set-qp-s3`. Executor brief: implement §4/QP-S3 work items (add GT.030–GT.046),
bump schema_version to 1.2, commit and push.

**Step 5 — Merge QP-S1, QP-S2, QP-S3 to main (in any order).**
```bash
# For each session (replace S1 with S2/S3 as needed):
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git merge --squash fix/planner-gap-qp-s1
git commit -m "fix(planner): close GAP-1..6, bump prompt to v2.1 [QP-S1]"
git push origin main
# Repeat for S2 and S3.
```

**Step 6 — Create QP-S4 worktree and spawn the eval session.**
```bash
git pull origin main
git worktree add ../Madhav-finalize -b fix/eval-governance-qp-s4
```
Open a new Claude Code session (claude-opus-4-6) with working directory
`/Users/Dev/Vibe-Coding/Apps/Madhav-finalize`. Provide the executor brief referencing
§4/QP-S4 work items (8 steps). This session runs the eval, writes REGRESSION_NOTES, and
closes the governance artifacts.

**Step 7 — Final merge and cleanup.**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git merge --squash fix/eval-governance-qp-s4
git commit -m "chore(governance): eval close, PIPELINE_GAP_PLAN_v1_0 COMPLETE [QP-S4]"
git push origin main

# Remove worktrees
git worktree remove ../Madhav-gap
git worktree remove ../Madhav-cleanup
git worktree remove ../Madhav-eval
git worktree remove ../Madhav-finalize
git worktree prune
```

The plan is complete when `PIPELINE_GAP_PLAN_v1_0.md` reads `status: COMPLETE` on main.

---

*End of PIPELINE_GAP_PLAN_v1_0.md*
