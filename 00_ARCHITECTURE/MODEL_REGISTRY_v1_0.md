---
artifact: MODEL_REGISTRY_v1_0
title: "MARSYS-JIS Model Registry"
canonical_id: MODEL_REGISTRY
version: 1.0
status: CURRENT
created_date: 2026-05-04
session_id: GANGA-P1-R1-S1
authored_by: Claude Code (Opus 4.7) — GANGA-P1-R1-S1-STACK-AUDIT
project_code: GANGA
purpose: >
  Authoritative registry of LLM provider stacks, per-role model assignments, and
  toolChoice support matrix for the MARSYS-JIS pipeline. Companion to the runtime
  registry at platform/src/lib/models/registry.ts (this artifact is the human-readable
  ledger; the .ts file is the machine-readable single-source-of-truth).
sources:
  - platform/src/lib/models/registry.ts (read 2026-05-04)
  - platform/src/lib/models/resolver.ts (read 2026-05-04)
  - platform/src/lib/pipeline/manifest_planner.ts (read 2026-05-04)
  - PROJECT_GANGA_PLAN_v1_0.md §Workstream K + §Critical Findings
---

# MARSYS-JIS — Model Registry

*Gate G0 deliverable. The single human-readable ledger of provider stacks, per-role
model assignments, and toolChoice support across the LLM pipeline.*

---

## §1 — Active Provider Stacks

Five stacks are defined in `STACK_ROUTING` (registry.ts:817–973). Each stack
provides a primary + fallback model for every CallType. The user selects a
stack (not individual models); switching stacks re-routes every pipeline call
simultaneously.

| Stack ID | Provider | Default? | Cost Profile | Synthesis Context | Notes |
|---|---|---|---|---|---|
| `nim` | NVIDIA NIM | ✅ DEFAULT | Free tier ($0.00) | 1M | Queue-based; cold-start latency variable |
| `anthropic` | Anthropic | — | Premium ($1–$15/$5–$75) | 1M (Opus 4.7) | Native prompt-caching, tool-use first-class |
| `gemini` | Google | — | Cheap ($0.015–$2.50/$0.06–$15) | 2M (largest) | Safety filters require BLOCK_NONE (resolver.ts:99) |
| `gpt` | OpenAI | — | Mid ($0.05–$2/$0.20–$8) | 1M | Auto prompt-caching, 75% discount on cache reads |
| `deepseek` | DeepSeek (api.deepseek.com) | — | Cheap ($0.14–$1.74/$0.28–$3.48) | 1M | **🚨 BF.GAP.001 — planner broken** |

`DEFAULT_STACK_ID = 'nim'` (registry.ts:554). New users land here.

---

## §2 — Model Decision Matrix (K.1)

### §2.1 — Per-stack, per-role primary models (from STACK_ROUTING)

The CallType taxonomy (registry.ts:765–771) maps every pipeline call to one of
five roles: `synthesis`, `planner_deep`, `planner_fast`, `context_assembly`,
`worker`. The per-role primary model on each stack is:

| Role → / Stack ↓ | synthesis | planner_deep | planner_fast | context_assembly | worker |
|---|---|---|---|---|---|
| **anthropic** | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5 | claude-sonnet-4-6 | claude-haiku-4-5 |
| **gemini** | gemini-2.5-pro | gemini-2.5-flash | gemini-2.5-flash | gemini-2.5-flash | gemini-2.5-flash-lite |
| **gpt** | gpt-4.1 | gpt-4.1-mini | gpt-4.1-mini | gpt-4.1-mini | gpt-4.1-nano |
| **deepseek** | deepseek-v4-pro | deepseek-v4-pro | deepseek-v4-flash 🚨 | deepseek-v4-flash 🚨 | deepseek-v4-flash 🚨 |
| **nim** | nemotron-3-super-120b-a12b | llama-3.3-nemotron-super-49b-v1 | nemotron-3-super-120b-a12b | nemotron-3-super-120b-a12b | nemotron-3-super-120b-a12b |

🚨 = uses an invalid DeepSeek API ID; see BF.GAP.001 in §4.

### §2.2 — Decision matrix (model × validity × toolChoice × thinking risk)

| Stack | Role | model_id | validity_confirmed | toolChoice_support | thinking_mode_risk | ctx (input) | $/1M in | $/1M out | Notes |
|---|---|---|---|---|---|---|---|---|---|
| anthropic | planner_fast | claude-haiku-4-5 | ✅ yes | ✅ yes | ❌ no | 200K | 1.00 | 5.00 | tool-use + prompt-caching native |
| anthropic | worker | claude-haiku-4-5 | ✅ yes | ✅ yes | ❌ no | 200K | 1.00 | 5.00 | shared with planner_fast |
| anthropic | context_assembly | claude-sonnet-4-6 | ✅ yes | ✅ yes | ❌ no | 1M | 3.00 | 15.00 | required ≥1M ctx for full corpus |
| anthropic | synthesis (primary) | claude-opus-4-7 | ✅ yes | ✅ yes | ❌ no | 1M | 15.00 | 75.00 | flagship; deepest reasoning |
| anthropic | synthesis (fallback) | claude-sonnet-4-6 | ✅ yes | ✅ yes | ❌ no | 1M | 3.00 | 15.00 | balanced |
| gemini | planner_fast | gemini-2.5-flash-lite | ✅ yes (smoke 2026-05-03) | ✅ yes | ❌ no | (≤200K typical) | 0.015 | 0.06 | replaced gemini-2.0-flash-lite (HTTP 404 2026-05-03) |
| gemini | worker | gemini-2.5-flash-lite | ✅ yes | ✅ yes | ❌ no | (≤200K typical) | 0.015 | 0.06 | cheapest 1M-family model |
| gemini | planner_deep | gemini-2.5-flash | ✅ yes | ✅ yes | ⚠️ yes | 1M | 0.075 | 0.30 | thinking enabled by default; mitigated via `thinkingBudget: 8192` (resolver.ts:118) |
| gemini | context_assembly | gemini-2.5-flash | ✅ yes | ✅ yes | ⚠️ yes | 1M | 0.075 | 0.30 | thinkingBudget cap applies |
| gemini | synthesis (primary) | gemini-2.5-pro | ✅ yes | ✅ yes | ⚠️ yes | 2M (largest) | 1.25–2.50 | 10.00 | safety filters MUST be BLOCK_NONE for Jyotish content (resolver.ts:111–117) |
| gemini | synthesis (fallback) | gemini-2.5-flash | ✅ yes | ✅ yes | ⚠️ yes | 1M | 0.075 | 0.30 | thinkingBudget cap |
| gpt | planner_fast | gpt-4.1-mini | ✅ yes | ✅ yes | ❌ no | 1M | 0.40 | 1.60 | auto prompt-caching, no headers |
| gpt | planner_deep | gpt-4.1-mini | ✅ yes | ✅ yes | ❌ no | 1M | 0.40 | 1.60 | shared with planner_fast |
| gpt | context_assembly | gpt-4.1-mini | ✅ yes | ✅ yes | ❌ no | 1M | 0.40 | 1.60 | |
| gpt | worker | gpt-4.1-nano | ✅ yes | ✅ yes | ❌ no | 1M | 0.05 | 0.20 | cheapest 1M-ctx model in registry |
| gpt | synthesis (primary) | gpt-4.1 | ✅ yes | ✅ yes | ❌ no | 1M | 2.00 | 8.00 | best instruction following in family |
| gpt | synthesis (fallback) | gpt-4.1-mini | ✅ yes | ✅ yes | ❌ no | 1M | 0.40 | 1.60 | |
| **deepseek** | **planner_fast** | **deepseek-v4-flash** | **❌ INVALID API ID** | **❌ no (after fallback)** | **🔥 yes** | (n/a) | (0.14 nominal) | (0.28 nominal) | **🚨 BF.GAP.001 — root cause** |
| **deepseek** | **worker** | **deepseek-v4-flash** | **❌ INVALID API ID** | **❌ no** | **🔥 yes** | — | — | — | shares root cause |
| **deepseek** | **context_assembly** | **deepseek-v4-flash** | **❌ INVALID API ID** | **❌ no** | **🔥 yes** | — | — | — | shares root cause |
| deepseek | planner_deep | deepseek-v4-pro | ⚠️ name aliases deepseek-reasoner | ⚠️ thinking model | 🔥 yes | 1M | 1.74 | 3.48 | thinking=false needed for JSON; SDK does not currently set this for planner calls |
| deepseek | synthesis (primary) | deepseek-v4-pro | ⚠️ name aliases deepseek-reasoner | n/a (no toolChoice in synthesis) | 🔥 yes | 1M | 1.74 | 3.48 | thinking=true for synthesis is fine; ~3.5 min latency observed (G.4) |
| deepseek | synthesis (fallback) | deepseek-v4-flash | ❌ INVALID API ID | n/a | 🔥 yes | — | — | — | falls back to v4-pro on planner failure path |
| nim | planner_fast | nvidia/nemotron-3-super-120b-a12b | ✅ yes (smoke 2026-05-03 ✅ 356ms) | ⚠️ partial — uses PlanInputJsonSchema workaround + toolChoice='required' | ❌ no | 1M (Mamba practical) | 0.00 | 0.00 | RULER-1M 91.64 |
| nim | planner_deep | nvidia/llama-3.3-nemotron-super-49b-v1 | ✅ yes (smoke 2026-05-03 ✅ 6.8s cold) | ⚠️ partial (same workaround) | ❌ no | ~128K (Llama 3.3 base) | 0.00 | 0.00 | deep CoT planner |
| nim | context_assembly | nvidia/nemotron-3-super-120b-a12b | ✅ yes | n/a | ❌ no | 1M | 0.00 | 0.00 | Mamba linear-time @1M |
| nim | worker | nvidia/nemotron-3-super-120b-a12b | ✅ yes | n/a | ❌ no | 1M | 0.00 | 0.00 | replaced llama-3.1-8b (timed out 2026-05-03) |
| nim | synthesis (primary) | nvidia/nemotron-3-super-120b-a12b | ✅ yes | n/a | ❌ no | 1M | 0.00 | 0.00 | only confirmed 1M-ctx NIM model serving |
| nim | synthesis (fallback) | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | ✅ yes (smoke 2026-05-03 ✅ 374ms) | n/a | ❌ no | 1M | 0.00 | 0.00 | confirmed by nim_1m_context_scan.mjs |

Legend:
- `validity_confirmed` = whether the registered ID is recognized by the underlying provider's API
- `toolChoice_support` = whether the model accepts `toolChoice='required'` (manifest_planner.ts:272) without rejection
- `thinking_mode_risk` = whether the resolved model routes to a thinking/reasoning variant that may reject toolChoice or emit reasoning tokens that break tool-call parsing
- `ctx` values from `MODEL_INDEX[id].maxInputTokens` in registry.ts; `—` indicates unverified

---

## §3 — toolChoice Support Matrix

`manifest_planner.ts` invokes `generateText({ ..., tools: { submit_plan }, toolChoice: 'required' })`
(line 272) for every stack. The behavior under that call differs by provider:

| Stack | Mechanism | Status |
|---|---|---|
| anthropic | Native tool-use; toolChoice='required' supported across haiku/sonnet/opus | ✅ Working |
| gemini | tool-use supported on flash-lite, flash, pro; toolChoice='required' honored. **Caveat:** thinkingConfig must be capped to keep latency reasonable (resolver.ts:118) | ✅ Working with thinkingBudget cap |
| gpt | tool-use across the entire gpt-4.1 family (1M ctx) | ✅ Working |
| nim | NVIDIA's OpenAI-compatible endpoint accepts toolChoice='required' BUT the grammar-constrained decoder rejects Zod's auto-generated schema (`propertyNames`, `anyOf:[{const:N}]`). Worked around via hand-crafted `PlanInputJsonSchema` (manifest_planner.ts:94–118) | ✅ Working via PlanInputJsonSchema |
| **deepseek** | **planner_fast primary `deepseek-v4-flash` is not a valid DeepSeek API ID. Call fails. Fallback path lands on `deepseek-reasoner` (a thinking/CoT model wrapped with `extractReasoningMiddleware` in resolver.ts:37–42), which rejects `toolChoice='required'` and/or emits `<think>` blocks instead of a structured tool call. Result: `generateText` returns no submit_plan tool call → `PlannerError` → silent fallback to `classify()` → `plan_json = NULL`** | **❌ BROKEN — see BF.GAP.001** |

Ground truth: `manifest_planner.ts` does NOT branch by provider. The same code
path runs for all five stacks. The DeepSeek failure is in the model-resolution
layer, not the planner code. **Do not modify manifest_planner.ts** (per
PROJECT_GANGA_PLAN §Critical Findings); the fix is in registry.ts.

---

## §4 — Known Invalid Model IDs

### BF.GAP.001 — `deepseek-v4-flash`

**Symptom.** Every DeepSeek-stack query in production has produced
`plan_json = NULL` since `LLM_FIRST_PLANNER_ENABLED=true` was committed
(2026-05-04, fa75e1a). The LLM-first planner has never successfully fired.
All queries silently fall back to the deterministic `classify()` path.

**Root cause.**

1. registry.ts declares `id: 'deepseek-v4-flash'` (line 212) and assigns it as:
   - `FAMILY_WORKER['deepseek']` (line 636)
   - `STACK_ROUTING.deepseek.planner_fast.primary` (line 961)
   - `STACK_ROUTING.deepseek.context_assembly.primary` (line 965)
   - `STACK_ROUTING.deepseek.worker.primary` (line 969)
   - `STACK_ROUTING.deepseek.synthesis.fallback` (line 954)

2. `resolver.ts` calls `deepseek('deepseek-v4-flash')` (resolver.ts:43) — an
   identifier that DeepSeek's public API (`api.deepseek.com`) does not
   recognize. The valid IDs are `deepseek-chat` (V4 Flash, non-thinking)
   and `deepseek-reasoner` (V4 Pro, thinking). The runtime mapping comment
   in registry.ts (lines 226–227) confirms this: *"deepseek-chat now routes
   to deepseek-v4-flash on DeepSeek's API"* — i.e. `deepseek-chat` IS the
   API surface; `deepseek-v4-flash` is the marketing/internal label only.

3. When the call to `deepseek('deepseek-v4-flash')` reaches DeepSeek's
   endpoint, it errors / falls through to `deepseek-reasoner` (the thinking
   variant), which:
   - is wrapped with `extractReasoningMiddleware` in resolver.ts:37–42, and
   - rejects `toolChoice='required'` in conjunction with a thinking response.

4. The AI SDK returns no tool call. `manifest_planner.ts:317–322` raises
   `PlannerError`. `consume/route.ts` catches it and silently falls back
   to `classify()`. Telemetry shows `plan_json = NULL` on every query.

**Detection.** `query_plan_log.plan_json IS NULL` for 100% of DeepSeek-stack
queries since 2026-05-04. (See `PROJECT_GANGA_PLAN_v1_0.md §3` row 3.)

**Fix.** Out of scope for GANGA-P1-R1-S1. Authored brief
`CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md` (preserved in git history at
commit `aeb7929`) prescribes 6 targeted edits to registry.ts: replace
`deepseek-v4-flash` with `deepseek-chat` in FAMILY_WORKER + four
STACK_ROUTING entries; un-deprecate the `deepseek-chat` registry entry;
add a warn-on-use guard for `deepseek-v4-flash`. Execution: GANGA-P1-R2-S1.

**Audit note (2026-05-04).** The brief was deleted from `/Apps/Madhav/Ganga/`
during ROOT_FILE_POLICY cleanup at session-open (commit `a0ef8d3`). Recoverable
from git history (`git show aeb7929:Ganga/CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md`).
Re-stage to `00_ARCHITECTURE/` at GANGA-P1-R2-S1 open if still wanted as the
working brief.

### Adjacent invalid / dead model IDs (informational)

These were already de-routed in registry.ts but are retained for audit trail:

| ID | Status | Discovered |
|---|---|---|
| `nvidia/llama-3.1-nemotron-ultra-253b-v1` | ❌ HTTP 404 (not on NIM free tier) | 2026-05-02 |
| `qwen/qwen3-235b-a22b` | ⚠️ HTTP 410 EOL | 2026-05-02 |
| `meta/llama-3.1-8b-instruct` | ⏱ TIMEOUT (degraded 2026-05-03) | 2026-05-03 |
| `gemini-2.0-flash-lite` | ❌ HTTP 404 (dropped from OpenAI-compat endpoint) | 2026-05-03 |
| `deepseek-ai/deepseek-v4-pro` (NIM) | ⏱ TIMEOUT on NIM free tier | 2026-05-02, 2026-05-03 |
| `deepseek-ai/deepseek-v4-flash` (NIM) | ⏱ TIMEOUT (was ✅ 2026-05-02; pulled by 2026-05-03) | 2026-05-03 |
| `qwen/qwen3-30b-a3b` (NIM) | ❌ HTTP 404 | 2026-05-02 |
| `nvidia/nemotron-4-340b-instruct` (NIM) | ❌ HTTP 404 | 2026-05-02 |
| `deepseek-ai/deepseek-r1` (NIM) | ⚠️ HTTP 410 EOL | 2026-05-02 |

---

## §5 — Planner Model Constraints

These are the binding constraints any planner-role model must satisfy. Derived
from the manifest_planner.ts implementation and observed production behavior.

| ID | Constraint | Source / Rationale |
|---|---|---|
| **B.1** | Must accept `toolChoice='required'` with a single `submit_plan` tool | manifest_planner.ts:272. The planner forces tool-call mode to avoid generateObject's structured-output path (NIM rejects it with HTTP 500). |
| **B.2** | Must accept hand-crafted JSON Schema (PlanInputJsonSchema) — NOT Zod-translated | manifest_planner.ts:94–118. Zod emits `propertyNames` and `anyOf:[{const:N}]`, both rejected by NIM's grammar decoder. |
| **B.3** | Must produce structured output without thinking/reasoning tokens that break tool-call extraction | A model that emits `<think>` blocks before the tool call (e.g. deepseek-reasoner via R1_REASONING_MIDDLEWARE in resolver.ts:15) cannot reliably satisfy B.1. |
| **B.4** | Must respond within 90s (the nimFetch abort horizon) — see manifest_planner.ts:264 comment | NIM free-tier queue waits can be long; `maxRetries: 0` on the AI SDK call to prevent retry-storm masking the real cause. |
| **B.5** | Must support `temperature: 0` (deterministic structured output) | manifest_planner.ts:257. Non-zero temperature on a structured-output planner harms determinism without benefit. |

A model that fails any of B.1–B.5 cannot serve as a planner regardless of its
suitability for synthesis. `deepseek-v4-flash` (after the alias-resolution
failure → reasoner mapping) fails B.1 + B.3 simultaneously.

---

## §6 — Recommended Changes

### §6.1 — Immediate (GANGA-P1-R2-S1 — PF-S1, P0 BLOCKING)

Replace `deepseek-v4-flash` with `deepseek-chat` in five places in registry.ts.
Detailed instructions in `CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md` (commit
`aeb7929` of main). Six edits total:

| # | File:line | Change |
|---|---|---|
| 1 | registry.ts:636 | `FAMILY_WORKER['deepseek']: 'deepseek-v4-flash'` → `'deepseek-chat'` |
| 2 | registry.ts:961 | `STACK_ROUTING.deepseek.planner_fast.primary: 'deepseek-v4-flash'` → `'deepseek-chat'` |
| 3 | registry.ts:965 | `STACK_ROUTING.deepseek.context_assembly.primary: 'deepseek-v4-flash'` → `'deepseek-chat'` |
| 4 | registry.ts:969 | `STACK_ROUTING.deepseek.worker.primary: 'deepseek-v4-flash'` → `'deepseek-chat'` |
| 5 | registry.ts:954 | `STACK_ROUTING.deepseek.synthesis.fallback: 'deepseek-v4-flash'` → `'deepseek-chat'` |
| 6 | registry.ts:230–242 | Un-deprecate the `deepseek-chat` registry entry: remove "(deprecated)" label, restore role='both' with full hint text reflecting it is the canonical V4 Flash API ID |

Optional 7th edit: add a warn-log when any code path resolves `deepseek-v4-flash`
so future regressions surface in observability.

### §6.2 — Out-of-scope for GANGA-P1-R2-S1

- Do NOT touch `manifest_planner.ts`. `toolChoice='required'` + PlanInputJsonSchema is
  correct for NIM compatibility and is not the bug. (Confirmed by reading the
  source 2026-05-04.)
- Do NOT change the deepseek-v4-pro entry; the synthesis-side path uses it
  with `thinking=true` and works correctly (modulo ~3.5 min latency, tracked
  separately as G.4).

### §6.3 — Future hardening (G2)

| Item | Description | Workstream |
|---|---|---|
| Model-ID validity gate | Pre-deployment smoke test that calls every primary in STACK_ROUTING with a `ping` and asserts HTTP 200 within budget. CI job. | E.5 / H.1 |
| Stack health dashboard | TracePanel surface for live model-resolution failures | I.4 / G.1 |
| Planner-fail observability | Increment a counter `planner_fail_total{stack,reason}` when `PlannerError` is caught in route.ts | G.2 |
| Lever 3 NIM model swap | Awaiting native authorization (open decision §5 of phase tracker) | F.3 |
| DeepSeek synthesis latency | Investigate ~3.5 min synthesis on DeepSeek stack; thinking=true cost | G.4 |

---

## §7 — Open Items

| ID | Item | Status | Owner |
|---|---|---|---|
| OI.1 | Lever 3 NIM model swap (replace nemotron-3-super-120b-a12b primary with mistral-large-3-675b once context confirmed ≥1M) | DEFERRED — pending native authorization (AC.W2.3) | F.3 |
| OI.2 | NIM free-tier model availability is volatile — schedule weekly catalog scan and update STACK_ROUTING accordingly | OPEN | platform/scripts/nim_catalog_check.mjs |
| OI.3 | DeepSeek synthesis latency (~3.5 min) — investigate thinking=true cost on V4 Pro for synthesis | OPEN | G.4 |
| OI.4 | Re-stage `CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md` to `00_ARCHITECTURE/` from git history (commit aeb7929) at next-session open if still desired as working brief | OPEN | GANGA-P1-R2-S1 |
| OI.5 | Mistral Large 3 675B context window verification — run `nim_1m_context_scan.mjs`; if ≥1M, promote to NIM synthesis primary | OPEN | F.2 |
| OI.6 | NVIDIA NIM API key + SLA verification (whether a paid tier would unlock DeepSeek V4 on NIM and rejuvenate the stack) | OPEN | F.1 |

---

## Changelog

- **v1.0 (2026-05-04)** — Initial publication. Authored at GANGA-P1-R1-S1
  (G0 Stack Audit gate). Captures the active 5-stack routing, K.1 decision
  matrix, K.2 NIM evaluation, B.1–B.5 planner constraints, and the
  BF.GAP.001 root-cause finding queued for fix in GANGA-P1-R2-S1.

*This is the human-readable ledger. The runtime single source of truth is
`platform/src/lib/models/registry.ts`. When the .ts file changes,
this artifact must be updated in the same session and a new minor or major
version bump recorded above. Drift between the two is a B.8 violation.*
