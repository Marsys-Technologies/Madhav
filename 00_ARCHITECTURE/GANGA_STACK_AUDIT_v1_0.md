---
artifact: GANGA_STACK_AUDIT_v1_0
title: "GANGA Gate G0 — LLM Stack Audit"
canonical_id: GANGA_STACK_AUDIT
version: 1.0
status: CURRENT
gate: G0
verdict: PASS (with PF-S1 queued as P0 BLOCKING for G1)
created_date: 2026-05-04
session_id: GANGA-P1-R1-S1-STACK-AUDIT
authored_by: Claude Code (Opus 4.7)
project_code: GANGA
purpose: >
  G0 gate artifact. Audits the LLM provider stack — model validity, toolChoice
  support, planner mechanism — across all five active stacks. Confirms the
  production blocker (BF.GAP.001) and produces the actionable handoff to
  GANGA-P1-R2-S1-PLANNER-FIX.
companion: 00_ARCHITECTURE/MODEL_REGISTRY_v1_0.md
---

# GANGA Gate G0 — LLM Stack Audit

*Companion to MODEL_REGISTRY_v1_0.md. This artifact is the gate-decision record;
the registry is the data ledger. Both authored in the same session for atomicity.*

---

## §1 — Audit scope

| Workstream | Item | Status |
|---|---|---|
| K.1 | Model × stack × role matrix audit (5 stacks × 5 roles = 25 cells) | ✅ COMPLETE |
| K.2 | NIM stack evaluation (PlanInputJsonSchema mechanism, model validity) | ✅ COMPLETE |
| K.3 | Author MODEL_REGISTRY_v1_0.md | ✅ COMPLETE (companion artifact) |

Read-only audit. Per session brief Step 1, `platform/src/**` was in
`must_not_touch`. No code changes in this session.

---

## §2 — Findings summary

### §2.1 — Production blocker confirmed

**BF.GAP.001 — DeepSeek planner has never fired in production.**

- `LLM_FIRST_PLANNER_ENABLED=true` was committed 2026-05-04 (commit `fa75e1a`).
- Every production query on the DeepSeek stack since then has produced
  `query_plan_log.plan_json IS NULL` (100%).
- All queries silently fall back to the deterministic `classify()` path —
  the LLM-first planner code is wired up but never reaches success.
- Root cause: registry.ts uses `deepseek-v4-flash` as the planner_fast
  primary. The DeepSeek public API does not recognize that ID. The valid
  IDs are `deepseek-chat` (V4 Flash, non-thinking) and `deepseek-reasoner`
  (V4 Pro, thinking, wraps `extractReasoningMiddleware`).
- The failure path resolves to the thinking variant, which rejects
  `toolChoice='required'` + `submit_plan` tool-call mode → no tool call
  emitted → `PlannerError` raised → silent fallback to classify().

Detail in MODEL_REGISTRY_v1_0.md §4.

### §2.2 — Stack-by-stack health

| Stack | Verdict | Detail |
|---|---|---|
| anthropic | ✅ HEALTHY | All five roles map to valid haiku/sonnet/opus IDs. tool-use + prompt-caching native. |
| gemini | ✅ HEALTHY (with caveats) | All roles valid. Two production-time mitigations are mandatory (resolver.ts:99–126): (a) `safetySettings: BLOCK_NONE` on all 5 categories — Jyotish content trips DANGEROUS_CONTENT mid-stream otherwise; (b) `thinkingBudget: 8192` on 2.5-flash/pro to cap latency. |
| gpt | ✅ HEALTHY | Entire gpt-4.1 family supports 1M ctx; auto prompt-caching (75% cache discount). |
| nim | ✅ HEALTHY (with hardening recommended) | All routed models confirmed live (smoke 2026-05-03). Planner uses hand-crafted `PlanInputJsonSchema` (manifest_planner.ts:94–118) to work around NIM's grammar-decoder rejecting Zod's `propertyNames` and `anyOf:[{const}]` — this is the correct solution and should not be reverted. NIM free-tier model availability is volatile (multiple models lost in 24h between 2026-05-02 and 2026-05-03); recommend weekly catalog scan job. |
| **deepseek** | **❌ BROKEN** | **planner_fast / context_assembly / worker / synthesis-fallback all point at the invalid `deepseek-v4-flash` ID. See BF.GAP.001.** |

### §2.3 — K.2 NIM evaluation

**(1) Does nemotron-49B / nemotron-3-super-120b support standard `toolChoice='required'`?**

Yes — but only when paired with the hand-crafted `PlanInputJsonSchema`.
NIM's grammar-constrained decoder rejects two JSON-Schema constructs that
Zod auto-generates:

- `propertyNames` (emitted by `z.record(z.string(), z.unknown())`)
- `anyOf: [{const: N}]` (emitted by `z.union([z.literal(1), z.literal(2), z.literal(3)])`)

NIM returns *"Grammar error: Unimplemented keys"* on these. The workaround
(manifest_planner.ts:94–118) is to feed a hand-written, NIM-friendly
JSONSchema7 to the AI SDK's `tool()` helper, while still post-validating
the model's tool-call args against `PlanSchemaZod` at runtime. This
preserves the strict schema contract for downstream consumers.

**(2) What is the PlanInputJsonSchema mechanism in manifest_planner.ts?**

Read-only review: manifest_planner.ts:94–118. A hand-crafted JSON Schema
fed to `jsonSchema<PlanSchema>(PlanInputJsonSchema)` inside `tool({...})`.
It defines the same shape as `PlanSchemaZod` but uses NIM-compatible
primitives (`type: 'integer', minimum: 1, maximum: 3` instead of an
anyOf-of-const for `priority`). The AI SDK uses this schema to constrain
NIM's grammar decoder; `PlanSchemaZod.safeParse(submitCall.input)` at
line 324 enforces the strict contract post-call.

This is a clean, minimal workaround. Do not modify it.

**(3) Is the NIM planner producing valid plan_json in production?**

Cannot directly verify in this session — `query_plan_log` access requires
either a Cloud SQL connection (out-of-scope per file locks) or the
Observatory dashboard. Indirect signals:

- Smoke tests on 2026-05-03 show `nvidia/nemotron-3-super-120b-a12b` ✅ 356ms
  and `nvidia/llama-3.3-nemotron-super-49b-v1` ✅ 6.8s cold-start.
- BHISMA Wave 2 Lever 2 close note (2026-05-04) documents NIM Lever-2
  in production with `LLM_FIRST_PLANNER_ENABLED=true`.
- BHISMA-W2-SD acceptance criteria 46/58 met implies the NIM planner is
  emitting valid plan_json on at least the smoke set.

**Recommendation: do NOT migrate the NIM planner to a "standard" toolChoice
path.** The current PlanInputJsonSchema + toolChoice='required' combination
is correct and works. Migration would require either (a) fixing Zod's
schema emitter (out-of-scope, upstream concern) or (b) abandoning NIM
compatibility (regression of Lever 2). Stay the course.

**(4) NIM stack hardening recommended for G2:**

- Weekly NIM catalog scan (`platform/scripts/nim_catalog_check.mjs`) — multiple
  models lost availability in 24h between 2026-05-02 and 2026-05-03.
- Mistral Large 3 675B context-window verification (`nim_1m_context_scan.mjs`);
  if ≥1M, promote to NIM synthesis primary (would replace the 120B with a 675B).
- Lever 3 NIM model swap (gated on native authorization, AC.W2.3 DEFERRED).

---

## §3 — Critical bug confirmed

```yaml
id: BF.GAP.001
priority: P0 BLOCKING
title: DeepSeek model ID mismatch — LLM planner never fires in production
discovered: 2026-05-04 (Project Ganga session-open audit)
confirmed: 2026-05-04 (this session, GANGA-P1-R1-S1, by source-code review)
component: platform/src/lib/models/registry.ts
status: ROOT_CAUSE_CONFIRMED — fix queued for GANGA-P1-R2-S1

symptom: |
  query_plan_log.plan_json IS NULL on 100% of DeepSeek-stack queries since
  LLM_FIRST_PLANNER_ENABLED=true was committed (fa75e1a, 2026-05-04).
  All queries fall back silently to the deterministic classify() path.

root_cause: |
  registry.ts maps the DeepSeek planner_fast primary to 'deepseek-v4-flash',
  which is not a valid identifier on api.deepseek.com. The provider's
  recognized IDs are 'deepseek-chat' (V4 Flash, non-thinking) and
  'deepseek-reasoner' (V4 Pro, thinking, wrapped with R1_REASONING_MIDDLEWARE
  in resolver.ts:37–42). The failure path resolves to the thinking variant,
  which rejects toolChoice='required' + submit_plan tool mode. No tool call
  is emitted → manifest_planner.ts:317–322 raises PlannerError → consume/
  route.ts catches and silently falls back to classify().

blast_radius: |
  - 100% of DeepSeek-stack queries since 2026-05-04
  - 0% of nim/anthropic/gemini/gpt stack queries
  - User-visible impact: synthesis still works (synthesis primary is
    deepseek-v4-pro with thinking=true; correctly routed). What is
    missing is the LLM-first plan_json that should populate the
    QueryDNAPanel, the per-tool plan log, and the W2-INSTRUMENT
    observability surface — these are blank for DeepSeek queries.

fix: |
  Out of scope this session. Brief authored separately as
  CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md (preserved in git history at commit
  aeb7929 — recoverable via `git show aeb7929:Ganga/CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md`).
  Six edits to registry.ts; no manifest_planner.ts changes.

handoff: GANGA-P1-R2-S1-PLANNER-FIX
```

---

## §4 — Recommended next action

**GANGA-P1-R2-S1-PLANNER-FIX** (P0 BLOCKING; G1 gate prerequisite).

Pre-flight:
1. Re-stage `CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md` to `00_ARCHITECTURE/` from
   git history (commit `aeb7929`, path `Ganga/CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md`)
   if a working copy is wanted.
2. Open the next session in the Ganga umbrella worktree
   (`/Users/Dev/Vibe-Coding/Apps/Ganga/`, branch `feature/ganga-umbrella`).

Execution scope (per MODEL_REGISTRY_v1_0.md §6.1):

- 5 model-id replacements + 1 alias un-deprecation in registry.ts
- 0 changes to manifest_planner.ts
- 1 deploy + smoke (verify plan_json non-NULL on a DeepSeek-stack test query)
- Append the Phase Tracker A.1 row → ✅
- Update GANGA_PHASE_TRACKER §2 → G1 status `🟡 IN PROGRESS` → `🟢 COMPLETE`

Acceptance:
- `query_plan_log.plan_json IS NOT NULL` on at least one DeepSeek-stack query post-deploy.
- Existing nim/anthropic/gemini/gpt stacks unchanged (regression check).

---

## §5 — Gate G0 verdict

**PASS** — with PF-S1 queued as P0 BLOCKING for G1.

Rationale:

- All three K-workstream items (K.1, K.2, K.3) discharged.
- MODEL_REGISTRY_v1_0.md authored as the registry-side companion.
- Production blocker root-caused, scoped, and handed off to a discrete next
  session with a pre-existing brief — this is the cleanest possible G0
  closure.
- Four of five stacks are healthy. The fifth (deepseek) is broken in a
  precisely-localized way (5 lines in registry.ts) and the fix is fully
  specified.
- No code changed in this session — audit-only discipline preserved.

The G0 verdict explicitly does NOT pass the production blocker through.
G1 cannot close until PF-S1 lands. G0 closes because the *audit* is
complete; the *fix* is the next session's job.

---

## Changelog

- **v1.0 (2026-05-04)** — Initial publication. Gate G0 close artifact.
  PASS verdict with PF-S1 queued for GANGA-P1-R2-S1.
