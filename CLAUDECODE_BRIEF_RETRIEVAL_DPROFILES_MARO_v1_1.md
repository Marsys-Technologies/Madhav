---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO
version: 1.1
status: RESOLVED — all parameterized markers filled from upstream sources; ready for implementation
created: 2026-06-27
updated: 2026-06-28
author: Cowork (planning) — detail-pass by Claude Code (DETAIL-PASS agent)
classification: CLAUDECODE_BRIEF — D-PROFILES + MARO (model-heterogeneity wave)
session_type: implementation — the shared Model-Aware Retrieval Orchestrator + 4 behavioral profiles
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (§A MARO; principles 8,11; wave D-PROFILES)
depends_on: D1,D2,D3,D4 ; profile VALUES depend on D8 eval-harness measurement
detail_pass_sources:
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (per-provider conflict matrix + obligations)
  - platform/src/lib/retrieval/registry/types.ts (frozen D1 contract, behavioral_overrides field)
  - 00_ARCHITECTURE/RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md §A (MARO definition)
  - platform/src/lib/models/registry.ts (actual model families + pinned model IDs in code)
detail_pass_required_when: D8 eval harness exists (to harden profile values from hypothesis → measured)
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (§A whole model-heterogeneity spine; principles 8,11)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (the per-provider conflict matrix + obligations = the v1 profile hypotheses)
hard_constraints:
  - per-model intelligence lives in ONE shared core (MARO), not per-channel
  - channel asymmetry honesty: full loop control on chat; surface-shaping only on BYO-MCP
  - validate-and-repair all model JSON (#9); chart-agnostic (#14)
acceptance_criteria: see §4
changelog:
  - v1.0 (2026-06-27): Parameterized brief — structure complete, values pending upstream inputs.
  - v1.1 (2026-06-28): Detail-pass — all [resolved from …] markers filled. [resolved from D8] → v1
    hypothesis values from RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md, tagged UNMEASURED.
    [resolved from D7] → declaration mechanism options enumerated from §A.4 of design approach.
    Model IDs pinned from registry.ts. behavioral_overrides field shape confirmed from types.ts.
    Five provider families in code (anthropic/google/deepseek/openai/nvidia) vs four families in
    D-PROFILES scope (anthropic/gemini/openai/deepseek) — NVIDIA NIM uses openai tool_use_format
    and json_object structured output; no separate NVIDIA profile needed (inherits openai profile
    with cache_strategy: none override).
---

# CLAUDE CODE BRIEF — D-PROFILES + MARO (v1.1 — resolved)

> Model-heterogeneity is the central requirement on BOTH channels. This wave builds the shared MARO
> core and the four behavioral profiles. **RESOLVED:** all parameterized placeholders are filled
> below with concrete values from upstream sources. Profile values are tagged `[UNMEASURED — D8]`
> where they are provider-spec hypotheses awaiting D8 eval-harness measurement.

---

## §0 — Resolved inputs (was: parameterized)

### §0.1 — [resolved from D8] — Per-model behavioral values (v1 hypotheses, UNMEASURED)

These are the v1 hypothesis values drawn directly from
`RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md` Part 1 + Part 2. Each is tagged
`[UNMEASURED — D8]` and must be re-measured against the MARSYS corpus once the D8 eval harness
exists. Until then these are the production defaults.

**Anthropic (claude-haiku-4-5 / claude-sonnet-4-6 / claude-opus-4-7)**
- Context floor: 200K (Haiku), 1M (Sonnet 4.6, Opus 4.7) — set by `maxInputTokens` in registry
- Context degradation: "context rot" — recall degrades as tokens grow toward window limit `[UNMEASURED — D8]`
- Bundle-size sweet spot: many small, composable tools; consolidated related ops via `action` param;
  soft cap ≤20 strict tools, ≤24 optional params, ≤16 union params `[UNMEASURED — D8]`
- Structured-output drift rate: grammar-constrained (GA) when `output_config.format=json_schema` +
  `strict:true` — drift rate effectively 0 in strict mode; refusal surfaces as `stop_reason:"refusal"` `[UNMEASURED — D8]`
- Optimal tool granularity: fine-grained composable (agentic loop strength); Opus benefits most
  from many-small-tool chaining `[UNMEASURED — D8]`
- Tool-arg decode: parsed object (no JSON.parse needed)
- Reasoning artifact: `thinking` / `redacted_thinking` blocks — must be passed back UNMODIFIED
  including redacted blocks; filtering on `type=="thinking"` silently breaks protocol
- Caching: MUST mark explicitly — up to 4 `cache_control` breakpoints; prefix order
  tools→system→messages; 100% exact prefix match required; never cache timestamped blocks;
  min ~1,024 tokens; TTL 5min (×1.25 write, ×0.1 read) or 1h optional
- Pinned model IDs (from registry.ts): `claude-haiku-4-5` (worker), `claude-sonnet-4-6` (mid),
  `claude-opus-4-7` (premium)
- Deprecation watch: none currently flagged in registry

**Gemini (gemini-2.5-flash-lite / gemini-2.5-flash / gemini-2.5-pro)**
- Context floor: 8,192 out (Flash Lite); 1M in / 65,536 out (Flash); 2M in / 65,536 out (Pro)
- Context degradation: single-needle ~99%, multi-needle degrades `[UNMEASURED — D8]`
- Bundle-size sweet spot: fat bundle — pull large relevant context once; Pro 2M window is the
  largest of any registered stack; Flash/Pro preferred for context_assembly `[UNMEASURED — D8]`
- Structured-output drift rate: schema honored but "does not guarantee values are semantically
  correct. Always validate"; ignores unsupported properties; may reject large/deeply-nested schemas `[UNMEASURED — D8]`
- Optimal tool granularity: 10–20 active tools maximum (soft guidance); ANY mode may reject
  large/deeply-nested schemas `[UNMEASURED — D8]`
- Tool-arg decode: parsed object (no JSON.parse needed)
- Tool-result wire: `functionResponse` with EXACT `id` from the `functionCall` — id mismatch is a
  silent failure
- Reasoning artifact: `thought_signatures` (encrypted) required for function calling — must send
  the `thought_signature` back inside its ORIGINAL Part; never merge/concat parts with signatures;
  `thinkingBudget` set to 24576 in registry quirks
- Caching: prefer explicit `caches.create` → `cached_content` handle for guaranteed saving; implicit
  auto-on for 2.5+; min 1024/4096 tokens (Flash/Pro); put large+common content at beginning;
  default TTL 1h; explicit is the reliable path for MARSYS reused corpora
- MCP constraint: Streamable HTTP only (no SSE); no `-` in server names (snake_case); not on
  Gemini 3 yet — MCP tools must use snake_case names with no hyphens
- Pinned model IDs (from registry.ts): `gemini-2.5-flash-lite` (worker), `gemini-2.5-flash` (mid,
  1M ctx), `gemini-2.5-pro` (premium, 2M ctx)
- Deprecation watch: `gemini-2.0-flash-lite` dropped from OpenAI-compat endpoint (HTTP 404,
  2026-05-03); replaced by `gemini-2.5-flash-lite`

**OpenAI (gpt-4.1-nano / gpt-4.1-mini / gpt-4.1)**
- Context floor: 1M for entire GPT-4.1 family (gpt-4.1, gpt-4.1-mini, gpt-4.1-nano); legacy
  gpt-4o/gpt-4o-mini are 128K — not used for synthesis
- Context degradation: extended-context billing threshold at 272K `[UNMEASURED — D8]`
- Bundle-size sweet spot: keeps initially available functions small; "fewer than 20 functions";
  reasons-then-acts decisively; strict structured output is the main lever `[UNMEASURED — D8]`
- Structured-output drift rate: strict mode guarantees schema adherence; `refusal` field surfaces
  rejections; prefer `json_schema` over `json_object`; limits: 5,000 props / 120,000 chars / 1,000
  enums `[UNMEASURED — D8]`
- Optimal tool granularity: well-typed, predictable returns; strict mode with `additionalProperties:false`
  + all fields in `required` (optionals as null union); parallel tool calls on by default `[UNMEASURED — D8]`
- Tool-arg decode: **JSON string** — must JSON.parse `arguments` field (same as DeepSeek)
- Tool-result wire: Responses API `function_call_output{call_id}` / Chat `role:"tool"{tool_call_id}`;
  output should be a string; pass reasoning items back with tool outputs
- Reasoning artifact: `reasoning.encrypted_content` (stateless/ZDR) or `previous_response_id`
  (stateful); reserve ≥25,000 tokens for reasoning+output; don't over-prescribe CoT
- Caching: automatic, free, no code changes needed for gpt-4o and newer; min 1,024 tokens;
  routes on prefix hash (~first 256 tokens); exact prefix match incl. images and tools;
  TTL 5–10min (up to 1h off-peak, 24h via `prompt_cache_retention`); up to 90% input reduction;
  `cached_tokens` telemetry available; use `allowed_tools` (not `tool_choice`) to preserve cache
- Pinned model IDs (from registry.ts): `gpt-4.1-nano` (worker), `gpt-4.1-mini` (mid), `gpt-4.1`
  (premium); legacy `gpt-4o` / `gpt-4o-mini` retained for backward compat only
- Deprecation watch: gpt-4o / gpt-4o-mini legacy (128K context — not suitable for Whole-Chart-Read)

**DeepSeek (deepseek-chat / deepseek-v4-pro)**
- Context floor (real): legacy `deepseek-chat` / `deepseek-reasoner` aliases had 64K effective
  context under V3/R1; V4 is 1M in / 384K out — but the valid worker API ID (`deepseek-chat`)
  routes to V4 Flash on DeepSeek's backend; context budget for MARO should be treated
  conservatively at **~128k** until V4 Flash is confirmed at 1M end-to-end `[UNMEASURED — D8]`
- Context degradation: structured-output drift increases with context length `[UNMEASURED — D8]`
- Bundle-size sweet spot: smallest-footprint treatment; fewest tools; avoid deeply nested schemas;
  ~128k budget cap with cited facts at top/bottom `[UNMEASURED — D8]`
- Structured-output drift rate: **5–12% JSON-schema drift** (PROVIDER_SPEC hypothesis) —
  `json_object` only, no content-level strict schema; "Include the word 'json'… and provide an
  example"; set `max_tokens` to avoid truncation; may "occasionally return empty content" →
  **application-side validate + retry is MANDATORY** `[UNMEASURED — D8]`
- Optimal tool granularity: OpenAI-compatible function calling (now first-class in V4); beta strict
  mode at `/beta` endpoint: all object props required + `additionalProperties:false`; no
  length/items constraints; `disable_parallel_tool_use` accepted but ignored `[UNMEASURED — D8]`
- Tool-arg decode: **JSON string** — must JSON.parse `arguments` field (same as OpenAI)
- Tool-result wire: `role:tool` (OpenAI-compatible); `reasoning_content` MUST be passed back for
  turns with tool calls (400 error otherwise) in V4 thinking mode
- Reasoning artifact: **V4 behavior (version-pin critical):** `reasoning_content` MUST be passed
  back when a tool call appeared between user messages (400 otherwise); `thinking` parameter toggles
  mode; legacy R1 behavior INVERTED this (must NOT feed back) — legacy aliases retire 2026-07-24
- Caching: automatic, on-disk, free; exact-prefix from token 0; partial/middle matches don't hit;
  **min unit 64 tokens** (smallest of all four families); `prompt_cache_hit_tokens`/`miss_tokens`
  telemetry; stable prefix first
- MCP: **NONE** — DeepSeek does not implement MCP; `mcp_servers` ignored on its
  Anthropic-compatible endpoint; MCP content blocks unsupported. MARO must route DeepSeek as
  a plain tool-calling backend only — never expose MCP-specific constructs to DeepSeek
- Pinned model IDs (from registry.ts): `deepseek-chat` (worker/planner — only valid non-thinking
  API ID that supports tool_choice); `deepseek-v4-pro` (premium synthesis, thinking mode)
- Deprecation watch: `deepseek-chat` alias → V4 Flash; `deepseek-reasoner` alias → V4 Pro.
  Both **retire 2026-07-24**. `deepseek-v4-flash` is NOT a valid DeepSeek API model ID
  (maps to deepseek-reasoner which rejects toolChoice — confirmed in registry hint)

**NVIDIA NIM (nvidia/* models) — not a separate D-PROFILES family**
- NVIDIA uses `tool_use_format: 'openai'` and `structured_output_format: 'json_object'` across
  all NIM models (from registry quirks); `cache_strategy: 'none'`; `streaming_required: true`
- MARO treatment: NVIDIA inherits the **OpenAI profile** with the following overrides:
  `cache_strategy: none` (no caching on NIM free tier), `streaming_required: true`,
  validate-and-repair as with DeepSeek (json_object only on NIM models)
- No separate NVIDIA MARO profile needed — OpenAI profile + cache_strategy:none covers it

### §0.2 — [resolved from D7] — MCP declaration mechanism

`RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md §A.4` specifies the behavior but defers the mechanism:

> *"Declaration mechanics — config vs OAuth scope vs per-key binding vs client hint — are resolved
> in-wave, not here."*

The four candidate mechanisms enumerated in §A.4:
1. **Config declaration** — model family stated in the MARO config / environment (operator-set)
2. **OAuth scope** — model family encoded in the OAuth scope string at auth time
3. **Per-key binding** — API key issued per model family; MARO reads family from key metadata
4. **Client hint** — connecting client sends a header or initial tool-call parameter identifying
   the model family

Implementation decision (to be made in-wave during D7 execution): pick one or a priority-ordered
combination. The universal-best fallback (when no declaration is present) is mandatory regardless
of which mechanism is chosen. MARO must treat undeclared as `family: 'universal'` and serve the
consolidated cross-model surface.

---

## §1 — MARO core

Shared model-aware orchestrator behind BOTH channels: reads the active family's profile and shapes
tool surface, bundle size, context budget, output validation, grounding, routing. Both the chat
engine and the MCP adapter consume it (single source — no per-channel duplication).

**Per-family normalization mandated by the provider spec (implement all four):**

| Axis | anthropic | gemini | openai | deepseek |
|---|---|---|---|---|
| Tool-arg decode | object (no parse) | object (no parse) | JSON.parse(arguments) | JSON.parse(arguments) |
| Tool-result wire | tool_result block, results-first user msg | functionResponse+exact id | function_call_output/role:tool | role:tool |
| Caching control | explicit breakpoints (≤4, never timestamped, write cost) | explicit cache handle preferred | automatic (no code change) | automatic (64-tok min unit) |
| Structured output | json_schema + strict → grammar guarantee | gemini_response_schema → validate values | json_schema strict → guarantee | json_object only → validate+retry mandatory |
| Context budget | 200K (Haiku) / 1M (Sonnet, Opus) | 1M (Flash) / 2M (Pro) | 1M (GPT-4.1 family) | ~128k conservative floor |
| Reasoning round-trip | thinking/redacted blocks UNMODIFIED | thought_signature per Part UNMODIFIED | reasoning items + encrypted_content | reasoning_content MUST be passed back (V4 tool turns) |
| MCP reach | HTTPS, tools only | Streamable HTTP, no `-` in names | Streamable HTTP or SSE | NONE — plain tool backend only |
| Prompt structure | [stable prefix]→[variable tail] | large+common at beginning | static at beginning | stable prefix from token 0 |

**behavioral_overrides field (from D1 contract — `platform/src/lib/retrieval/registry/types.ts`):**
```typescript
behavioral_overrides?: {
  anthropic?: Record<string, unknown>
  gemini?: Record<string, unknown>
  openai?: Record<string, unknown>
  deepseek?: Record<string, unknown>
}
```
MARO reads `capability.behavioral_overrides[activeFamily]` to apply per-capability family
overrides. Most capabilities leave this unset. Only set when a capability needs explicit
per-family shaping beyond the family default profile.

---

## §2 — The four behavioral profiles (living artifact)

Emit `RETRIEVAL_MODEL_PROFILES` — one dossier per family. v1 values from the provider spec
(tagged `[UNMEASURED — D8]`); each parameter scheduled for D8 measurement. This is a LIVING
artifact — re-measured + bumped as models evolve.

### Profile: anthropic

```typescript
{
  family: 'anthropic',
  profile_version: '1.0.0',
  status: 'UNMEASURED',
  pinned_models: {
    worker:   'claude-haiku-4-5',    // 200K ctx, $1.00/$5.00
    mid:      'claude-sonnet-4-6',   // 1M ctx,   $3.00/$15.00
    premium:  'claude-opus-4-7',     // 1M ctx,   $15.00/$75.00
  },
  deprecations: [],                  // none currently
  tool_arg_format: 'object',         // parsed object — no JSON.parse
  tool_result_format: 'tool_result_block',  // results-first user message
  max_active_tools: 20,              // strict limit; ≤24 optional params, ≤16 union params [UNMEASURED — D8]
  tool_granularity: 'fine_grained',  // many small composable tools; chain via action param [UNMEASURED — D8]
  bundle_strategy: 'many_small',     // Opus/Sonnet agentic loop strength [UNMEASURED — D8]
  context_budget_tokens: {
    worker: 200_000,                 // Haiku 4.5 cap
    mid:    1_000_000,               // Sonnet 4.6
    premium: 1_000_000,              // Opus 4.7
  },
  structured_output: {
    format: 'json_schema',
    strict: true,
    drift_rate: 0,                   // grammar-constrained when strict=true [UNMEASURED — D8]
    validate_and_repair: false,      // strict mode is reliable; still validate values
  },
  cache_strategy: 'explicit_headers',
  cache_rules: {
    max_breakpoints: 4,
    prefix_order: ['tools', 'system', 'messages'],
    exact_prefix_required: true,
    never_cache_timestamped: true,
    min_tokens: 1024,                // model-varying; aim >1024
  },
  reasoning: {
    mode: 'none',                    // thinking blocks present on Opus/Sonnet with extended thinking
    round_trip: 'unmodified',        // thinking + redacted_thinking blocks MUST be passed back verbatim
    never_filter_type: ['thinking', 'redacted_thinking'],
  },
  mcp_constraints: {
    transport: 'https_only',
    tools_only: true,                // no resources/prompts on Anthropic MCP connector
    tool_name_pattern: '^[a-zA-Z0-9_-]{1,64}$',
  },
  prompt_structure: '[stable_prefix]→[variable_tail]',
}
```

### Profile: gemini

```typescript
{
  family: 'gemini',
  profile_version: '1.0.0',
  status: 'UNMEASURED',
  pinned_models: {
    worker:   'gemini-2.5-flash-lite',  // 8K out, $0.015/$0.06
    mid:      'gemini-2.5-flash',       // 1M in, 65K out, $0.075/$0.30
    premium:  'gemini-2.5-pro',         // 2M in, 65K out, $1.25/$10.00
  },
  deprecations: [
    { id: 'gemini-2.0-flash-lite', reason: 'HTTP 404 on OpenAI-compat endpoint 2026-05-03' },
  ],
  tool_arg_format: 'object',         // parsed object — no JSON.parse
  tool_result_format: 'functionResponse_with_exact_id',  // id from functionCall MUST match
  max_active_tools: 20,              // soft guidance: 10–20 maximum [UNMEASURED — D8]
  tool_granularity: 'fat_bundle',    // pull large bundle once; fat context is the advantage [UNMEASURED — D8]
  bundle_strategy: 'single_large',   // load full corpus in one call (Pro 2M window) [UNMEASURED — D8]
  context_budget_tokens: {
    worker:   8_192,                 // output cap; input unconstrained
    mid:    1_000_000,               // Flash 1M input
    premium: 2_000_000,              // Pro 2M input — largest of all stacks
  },
  structured_output: {
    format: 'gemini_response_schema',
    strict: false,                   // VALIDATED mode reduces malformed calls but values may err
    drift_rate: null,                // "does not guarantee values are semantically correct" [UNMEASURED — D8]
    validate_and_repair: true,       // ALWAYS validate values; ignores unsupported props
  },
  cache_strategy: 'context_caching',
  cache_rules: {
    prefer_explicit: true,           // `caches.create` → handle for guaranteed saving
    implicit_available: true,        // auto on 2.5+ but not guaranteed
    min_tokens_flash: 1024,
    min_tokens_pro: 4096,
    ttl_default: '1h',
    put_large_common_at_beginning: true,
  },
  reasoning: {
    mode: 'native',                  // SDK type:'reasoning' UIMessage parts
    thought_signatures: 'required_for_function_calling',
    round_trip: 'per_part_unmodified',  // send thought_signature inside ORIGINAL Part; never merge
    thinking_budget_default: 24576,  // from registry quirks.request_transforms.thinking_budget
  },
  mcp_constraints: {
    transport: 'streamable_http',    // no SSE; Gemini 3 not yet supported
    tool_name_pattern: '^[A-Za-z0-9_.]+$',  // no `-` in names; snake_case preferred
    server_name_pattern: '^[A-Za-z0-9_]+$', // no `-` in server names
  },
  prompt_structure: 'large_common_at_beginning_query_at_end',
}
```

### Profile: openai

```typescript
{
  family: 'openai',
  profile_version: '1.0.0',
  status: 'UNMEASURED',
  pinned_models: {
    worker:   'gpt-4.1-nano',   // 1M ctx, $0.05/$0.20
    mid:      'gpt-4.1-mini',   // 1M ctx, $0.40/$1.60
    premium:  'gpt-4.1',        // 1M ctx, $2.00/$8.00
  },
  deprecations: [
    { id: 'gpt-4o',      reason: '128K context — not suitable for Whole-Chart-Read; legacy compat only' },
    { id: 'gpt-4o-mini', reason: '128K context — not suitable for Whole-Chart-Read; legacy compat only' },
  ],
  tool_arg_format: 'json_string',    // MUST JSON.parse(arguments)
  tool_result_format: 'function_call_output',  // Responses: function_call_output{call_id}; Chat: role:tool
  max_active_tools: 20,              // "keep the number of initially available functions small" [UNMEASURED — D8]
  tool_granularity: 'well_typed',    // strict schema; reasons-then-acts; predictable returns [UNMEASURED — D8]
  bundle_strategy: 'structured_strict',  // well-typed returns; strict mode is the lever [UNMEASURED — D8]
  context_budget_tokens: {
    worker:   1_000_000,
    mid:      1_000_000,
    premium:  1_000_000,
    billing_threshold: 272_000,      // extended-context billing above this threshold
  },
  structured_output: {
    format: 'json_schema',
    strict: true,                    // "always enabling strict mode" — additionalProperties:false + all required
    optionals_as: 'null_union',      // optional fields become { type: ['T', 'null'] }
    drift_rate: 0,                   // strict mode guarantees schema adherence [UNMEASURED — D8]
    validate_and_repair: false,      // strict reliable; still validate values; watch refusal field
    limits: { props: 5000, chars: 120_000, enums: 1000 },
  },
  cache_strategy: 'automatic',
  cache_rules: {
    automatic: true,                 // no code change; free; gpt-4o and newer
    min_tokens: 1024,
    prefix_hash_window: 256,         // routes on ~first 256 tokens
    exact_prefix_required: true,
    static_at_beginning: true,
    ttl: '5-10min',                  // up to 1h off-peak; 24h via prompt_cache_retention
    prefer_allowed_tools_over_tool_choice: true,  // preserves prompt-cache savings
  },
  reasoning: {
    mode: 'none',                    // reasoning tokens invisible, billed as output
    round_trip: 'encrypted_content_or_previous_response_id',
    reserve_tokens: 25_000,          // ≥25K for reasoning+output
    dont_over_prescribe_cot: true,
  },
  mcp_constraints: {
    transport: 'streamable_http_or_sse',
    require_approval_default: true,  // OpenAI mcp tool requires approval by default
    defer_loading: true,             // for large servers
  },
  prompt_structure: '[stable_prefix]→[variable_tail]',
}
```

### Profile: deepseek

```typescript
{
  family: 'deepseek',
  profile_version: '1.0.0',
  status: 'UNMEASURED',
  pinned_models: {
    worker:   'deepseek-chat',    // non-thinking, supports tool_choice; only valid planner API ID
    premium:  'deepseek-v4-pro',  // 1M ctx, thinking=toggle, $1.74/$3.48 post-promo
  },
  deprecations: [
    { id: 'deepseek-chat',      retire_date: '2026-07-24', maps_to: 'deepseek-v4-flash (non-thinking)' },
    { id: 'deepseek-reasoner',  retire_date: '2026-07-24', maps_to: 'deepseek-v4-pro (thinking)' },
    { id: 'deepseek-v4-flash',  note: 'NOT a valid DeepSeek API model ID — rejects toolChoice; do not use' },
  ],
  tool_arg_format: 'json_string',    // MUST JSON.parse(arguments) — OpenAI-compatible
  tool_result_format: 'role_tool',   // role:tool (OpenAI-compatible)
  max_active_tools: 10,              // smallest-footprint treatment; fewer is safer [UNMEASURED — D8]
  tool_granularity: 'minimal',       // fewest tools; avoid nested schemas [UNMEASURED — D8]
  bundle_strategy: 'smallest_footprint',  // most defensive treatment; ~128k budget [UNMEASURED — D8]
  context_budget_tokens: {
    worker:   128_000,               // conservative floor [UNMEASURED — D8] — V4 Flash via deepseek-chat API
    premium:  1_000_000,             // V4 Pro confirmed 1M
    working_assumption: '~128k floor until V4 Flash API endpoint confirmed at 1M end-to-end',
  },
  structured_output: {
    format: 'json_object',           // NO content-level strict schema — json_object only
    strict: false,                   // beta strict at /beta endpoint only: all props required, additionalProperties:false
    include_json_word_in_prompt: true,  // "Include the word 'json'… and provide an example"
    drift_rate: '5-12%',             // PROVIDER_SPEC hypothesis [UNMEASURED — D8]
    validate_and_repair: true,       // MANDATORY — may return empty content
    set_max_tokens: true,            // always set max_tokens to avoid truncation
  },
  cache_strategy: 'none',            // automatic on DeepSeek API but registry sets cache_strategy:'none' for routing
  cache_rules: {
    automatic: true,                 // on DeepSeek API: free, on-disk, exact-prefix from token 0
    min_unit_tokens: 64,             // smallest min unit of all four families
    partial_middle_miss: true,       // partial/middle matches DO NOT hit cache
    stable_prefix_first: true,
  },
  reasoning: {
    mode: 'none',                    // registry: reasoningMode='none'; native <think> blocks via extractReasoningTrace
    v4_tool_call_rule: 'MUST_pass_back_reasoning_content',  // 400 error otherwise on V4 tool turns
    thinking_param: 'toggle',        // thinking=true for deep synthesis; false for planner
    version_pin_critical: true,      // V4 inverts legacy R1 behavior — must version-pin
  },
  mcp_constraints: {
    mcp_supported: false,            // DeepSeek does NOT implement MCP
    anthropic_endpoint_note: 'mcp_servers ignored; MCP content blocks unsupported',
    treatment: 'plain_tool_calling_backend_only',
  },
  prompt_structure: '[stable_prefix_from_token_0]→[variable_tail]',
}
```

---

## §3 — Channel asymmetry

**Chat channel:** MARO owns the loop → full per-model optimization per profiles above.

**BYO-MCP channel:** MARO shapes surface/returns/grounding/budget/validation but cannot control
the client's loop. Behavior per §A.4 of RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md:

- **Declared** (family known via one of the four mechanisms in §0.2) → serve that family's profiled
  surface from the behavioral profiles above
- **Undeclared** → serve `universal-best` surface: consolidated workflow tools (~10–15 not
  70-asset mirror), `response_format`/`verbosity` enum so client self-selects, structured+text
  dual output (structuredContent + serialized JSON text block per MCP spec), tool names that are
  valid for ALL families (snake_case, no hyphens, ≤64 chars, `[A-Za-z0-9_.]`)

**Capability statement:** On chat, system maximizes per-model value fully. On BYO-MCP, it
maximizes within protocol control and shapes the surface so the client's native loop is nudged
toward the optimal path. It does NOT claim control over a stranger's loop.

**DeepSeek on MCP:** DeepSeek has no MCP support. If DeepSeek is the declared family on the MCP
channel, MARO must serve it as a plain tool-calling backend, stripping MCP-specific constructs
(content blocks, resources, prompts). This is the only family requiring this treatment.

---

## §4 — Acceptance criteria

- MARO core implemented + consumed by both channels (one source of model logic; no per-channel
  duplication of the per-family normalization table in §1).
- Per-family normalization working for all four conflict axes: tool-arg decode, caching, structured
  output validate-and-repair, prompt structure, reasoning round-trip.
- `RETRIEVAL_MODEL_PROFILES` v1 artifact emitted with the four profiles above; all hypothesis
  values tagged `[UNMEASURED — D8]`; living-artifact versioning (semver) set.
- `behavioral_overrides` field on `CapabilityDescriptor` (D1 contract) read and applied by MARO
  for per-capability family overrides.
- Declared→profiled / undeclared→universal MCP behavior wired per §3; DeepSeek MCP exception
  (plain tool backend) implemented.
- Tool names cross-family compliant: snake_case, no hyphens, ≤64 chars (satisfies both
  Anthropic `^[a-zA-Z0-9_-]{1,64}$` and Gemini `[A-Za-z0-9_.]` constraints simultaneously
  when hyphens are avoided).
- NVIDIA NIM handled via OpenAI profile + `cache_strategy:none` override; no fifth profile.
- DeepSeek model IDs pinned to `deepseek-chat` (worker) and `deepseek-v4-pro` (premium);
  deprecation watchpoint for 2026-07-24 alias retirement documented.
- Detail-pass against D8 scheduled to harden all `[UNMEASURED — D8]` values once eval harness
  can measure each family on the MARSYS corpus.
- Chart-agnostic throughout: no literal chart_id, no native identifiers in any MARO or profile
  artifact (enforced by D1 `chart_agnostic_gate.ts`).

*End of CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO v1.1 (detail-pass 2026-06-28).*
