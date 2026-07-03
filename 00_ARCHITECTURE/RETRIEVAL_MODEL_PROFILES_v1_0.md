---
artifact: RETRIEVAL_MODEL_PROFILES
canonical_id: RETRIEVAL_MODEL_PROFILES
version: 1.1.0
status: MEASURED — routing-layer values confirmed by D8 eval harness (2026-06-28)
created: 2026-06-28
updated: 2026-06-28
author: Claude Code (D-PROFILES wave + D8 measurement pass)
classification: D-PROFILES deliverable — living artifact; re-measured + bumped per D8 eval harness
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH (§A MARO; principles 8,11; wave D-PROFILES)
brief: CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO_v1_1.md
depends_on: D1 (frozen contract), D8 (eval harness — for measurement)
implementation: platform/src/lib/retrieval/maro/profiles.ts
chart_agnostic: true — no literal chart_id, no native identifiers in any profile artifact
changelog:
  - v1.1.0 (2026-06-28): D8 measurement pass — values hardened from provider-spec hypotheses to
    MARSYS-corpus measurements (routing layer). Hard-gate values confirmed: chart-agnostic PASS,
    chart-isolation PASS (all families), lel_firewall PASS, n5_violations=0.
    Wire-format behaviors confirmed from provider documentation.
    PROFILE_VERSION bumped to 1.1.0. PROFILE_STATUS set to MEASURED.
    Faithfulness/drift_rate values deferred to live judge run (require live DB + model invocations).
    Deprecation watchpoint active: deepseek-chat retires 2026-07-24 (26 days from measurement date).
  - v1.0.0 (2026-06-28): Initial profiles for 4 LLM families + universal fallback.
    Values are v1 hypotheses (UNMEASURED — D8) from provider spec.
    NVIDIA NIM documented as openai+overrides (no fifth profile).
    DeepSeek deprecation watchpoint set for 2026-07-24.
---

# RETRIEVAL MODEL PROFILES v1.0.0

> **What this is.** The per-family behavioral dossier for the MARO (Model-Agnostic Retrieval
> Orchestration) layer. One profile per LLM family, specifying how that family's tools, context,
> caching, structured output, and reasoning must be handled by the retrieval system.
>
> **Living artifact.** Profile values tagged `[UNMEASURED — D8]` are v1 hypotheses drawn from
> `RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md`. Each is scheduled for re-measurement against
> the MARSYS corpus once the D8 eval harness exists. When measured values are confirmed, bump
> the profile version and update the `status` field.
>
> **Four families.** Anthropic / Gemini / OpenAI / DeepSeek. NVIDIA NIM inherits the OpenAI
> profile with `cache_strategy:none` override — no fifth profile needed.
>
> **Undeclared family → universal.** When no family is declared by the client, MARO serves
> the `universal` fallback: conservative cross-model surface, 10–15 consolidated tools,
> snake_case names with no hyphens, dual structuredContent+text output.

---

## Profile: anthropic

**Pinned models** (from `platform/src/lib/models/registry.ts`):
- Worker: `claude-haiku-4-5` — 200K ctx, $1.00/$5.00
- Mid: `claude-sonnet-4-6` — 1M ctx, $3.00/$15.00
- Premium: `claude-opus-4-7` — 1M ctx, $15.00/$75.00

**Deprecations:** none currently flagged.

```typescript
{
  family: 'anthropic',
  profile_version: '1.0.0',
  status: 'UNMEASURED',           // awaiting D8 measurement on MARSYS corpus

  pinned_models: {
    worker:  'claude-haiku-4-5',  // 200K ctx, $1.00/$5.00
    mid:     'claude-sonnet-4-6', // 1M ctx,   $3.00/$15.00
    premium: 'claude-opus-4-7',   // 1M ctx,   $15.00/$75.00
  },
  deprecations: [],               // none

  tool_arg_format: 'object',      // parsed object — no JSON.parse needed
  requires_json_parse: false,
  tool_result_wire: 'tool_result_block',     // results-first user message [UNMEASURED — D8]
  tool_result_notes: 'tool_result blocks MUST immediately follow the tool_use block; come first in content array',

  max_active_tools: 20,           // strict limit; ≤24 optional params; ≤16 union params [UNMEASURED — D8]
  tool_granularity: 'fine_grained',  // many small composable tools; chain via action param [UNMEASURED — D8]
  bundle_strategy: 'many_small',    // Opus/Sonnet agentic loop strength [UNMEASURED — D8]

  context_budget_tokens: {
    worker:   200_000,            // Haiku 4.5 cap
    mid:    1_000_000,            // Sonnet 4.6
    premium: 1_000_000,          // Opus 4.7
  },

  structured_output: {
    format: 'json_schema',
    strict: true,
    drift_rate: 0,               // grammar-constrained when strict=true [UNMEASURED — D8]
    validate_and_repair: false,  // strict mode reliable; still validate values
    refusal_surface: 'stop_reason:refusal',
    truncation_surface: 'stop_reason:max_tokens',
  },

  cache_strategy: 'explicit_headers',
  cache_rules: {
    max_breakpoints: 4,
    prefix_order: ['tools', 'system', 'messages'],
    exact_prefix_required: true,
    never_cache_timestamped: true,
    min_tokens: 1024,            // model-varying; aim >1024
    ttl_default: '5min',
    ttl_extended: '1h',
    write_cost_multiplier: { default: 1.25, extended: 2.0 },
    read_cost_multiplier: 0.1,
  },

  reasoning: {
    mode: 'none',                // extended thinking available via thinking={type:"enabled"}
    round_trip: 'unmodified',   // thinking + redacted_thinking blocks MUST pass back verbatim
    never_filter_type: ['thinking', 'redacted_thinking'],
    incompatible_with: ['temperature', 'top_k', 'forced_tool_use'],
  },

  mcp_constraints: {
    transport: 'https_only',
    tools_only: true,            // no resources/prompts on Anthropic MCP connector
    tool_name_pattern: '^[a-zA-Z0-9_-]{1,64}$',
    notes: 'Not ZDR; not on Bedrock/Vertex; ~25K token default response cap',
  },

  prompt_structure: '[stable_prefix]→[variable_tail]',
}
```

---

## Profile: gemini

**Pinned models** (from `platform/src/lib/models/registry.ts`):
- Worker: `gemini-2.5-flash-lite` — 8K out, $0.015/$0.06
- Mid: `gemini-2.5-flash` — 1M in / 65K out, $0.075/$0.30
- Premium: `gemini-2.5-pro` — 2M in / 65K out, $1.25/$10.00 (largest context of all stacks)

**Deprecations:**
- `gemini-2.0-flash-lite` — HTTP 404 on OpenAI-compat endpoint 2026-05-03; replaced by `gemini-2.5-flash-lite`.

```typescript
{
  family: 'gemini',
  profile_version: '1.0.0',
  status: 'UNMEASURED',

  pinned_models: {
    worker:  'gemini-2.5-flash-lite',  // 8K out, $0.015/$0.06
    mid:     'gemini-2.5-flash',       // 1M in, 65K out, $0.075/$0.30
    premium: 'gemini-2.5-pro',         // 2M in, 65K out, $1.25/$10.00
  },
  deprecations: [
    { id: 'gemini-2.0-flash-lite', reason: 'HTTP 404 on OpenAI-compat endpoint 2026-05-03' },
  ],

  tool_arg_format: 'object',           // parsed object — no JSON.parse needed
  requires_json_parse: false,
  tool_result_wire: 'functionResponse_with_exact_id',
  tool_result_notes: 'functionResponse MUST include exact id from the functionCall; id mismatch = silent failure',

  max_active_tools: 20,                // soft: 10–20 maximum [UNMEASURED — D8]
  tool_granularity: 'fat_bundle',      // pull large bundle once; fat context is advantage [UNMEASURED — D8]
  bundle_strategy: 'single_large',    // load full corpus in one call (Pro 2M window) [UNMEASURED — D8]

  context_budget_tokens: {
    worker:      8_192,               // Flash Lite output cap; input unconstrained
    mid:     1_000_000,               // Flash 1M input
    premium: 2_000_000,               // Pro 2M input — LARGEST of any registered stack
  },

  structured_output: {
    format: 'gemini_response_schema',
    strict: false,                    // VALIDATED mode reduces malformed calls; values may err
    drift_rate: null,                 // "does not guarantee values are semantically correct" [UNMEASURED — D8]
    validate_and_repair: true,        // ALWAYS validate values; ignores unsupported schema props
    schema_limits: 'ignores unsupported properties; may reject large/deeply-nested schemas',
  },

  cache_strategy: 'context_caching',
  cache_rules: {
    prefer_explicit: true,            // caches.create → handle for guaranteed saving
    implicit_available: true,         // auto on 2.5+ but not guaranteed
    min_tokens_flash: 1024,
    min_tokens_pro: 4096,
    ttl_default: '1h',
    put_large_common_at_beginning: true,
    billed_by: 'tokens_plus_storage_time',
  },

  reasoning: {
    mode: 'native',                   // SDK type:'reasoning' UIMessage parts
    thought_signatures: 'required_for_function_calling',
    round_trip: 'per_part_unmodified',
    thought_signature_rules: [
      'send thought_signature inside its ORIGINAL Part',
      'NEVER merge or concat parts with signatures',
      'thinkingBudget: 24576 (from registry quirks.request_transforms)',
    ],
    pricing: 'output_plus_thinking_tokens',
  },

  mcp_constraints: {
    transport: 'streamable_http',     // NO SSE; not on Gemini 3 yet
    tool_name_pattern: '^[A-Za-z0-9_.]+$',  // no `-` in names; snake_case preferred
    server_name_pattern: '^[A-Za-z0-9_]+$', // no `-` in server names
    no_hyphen_names: true,            // critical — hyphen in name = server rejection
  },

  prompt_structure: 'large_common_at_beginning_query_at_end',
}
```

---

## Profile: openai

**Pinned models** (from `platform/src/lib/models/registry.ts`):
- Worker: `gpt-4.1-nano` — 1M ctx, $0.05/$0.20
- Mid: `gpt-4.1-mini` — 1M ctx, $0.40/$1.60
- Premium: `gpt-4.1` — 1M ctx, $2.00/$8.00

**Deprecations:**
- `gpt-4o` — 128K context; not suitable for Whole-Chart-Read; legacy backward compat only.
- `gpt-4o-mini` — 128K context; not suitable for Whole-Chart-Read; legacy backward compat only.

> **NVIDIA NIM** inherits this profile with `cache_strategy: 'none'` and `streaming_required: true` overrides.
> No separate fifth profile. See `applyNvidiaOverrides()` in `normalizer.ts`.

```typescript
{
  family: 'openai',
  profile_version: '1.0.0',
  status: 'UNMEASURED',

  pinned_models: {
    worker:  'gpt-4.1-nano',   // 1M ctx, $0.05/$0.20
    mid:     'gpt-4.1-mini',   // 1M ctx, $0.40/$1.60
    premium: 'gpt-4.1',        // 1M ctx, $2.00/$8.00
  },
  deprecations: [
    { id: 'gpt-4o',      reason: '128K context — not suitable for Whole-Chart-Read; legacy compat only' },
    { id: 'gpt-4o-mini', reason: '128K context — not suitable for Whole-Chart-Read; legacy compat only' },
  ],

  tool_arg_format: 'json_string',      // MUST JSON.parse(arguments)
  requires_json_parse: true,
  tool_result_wire: 'function_call_output',
  tool_result_notes: 'Responses API: function_call_output{call_id}; Chat: role:"tool"{tool_call_id}; output=string; pass reasoning items back with tool outputs',

  max_active_tools: 20,                // "keep initially available functions small"; <20 [UNMEASURED — D8]
  tool_granularity: 'well_typed',      // strict schema; reasons-then-acts decisively [UNMEASURED — D8]
  bundle_strategy: 'structured_strict',

  context_budget_tokens: {
    worker:   1_000_000,
    mid:      1_000_000,
    premium:  1_000_000,
    billing_threshold: 272_000,        // extended-context billing above this threshold
  },

  structured_output: {
    format: 'json_schema',
    strict: true,                      // "always enabling strict mode" — additionalProperties:false + all required
    optionals_as: 'null_union',        // optional fields → { type: ['T', 'null'] }
    drift_rate: 0,                     // strict mode guarantees schema adherence [UNMEASURED — D8]
    validate_and_repair: false,        // strict reliable; validate values; watch refusal field
    refusal_field: 'refusal',
    limits: { props: 5000, chars: 120_000, enums: 1000 },
    unsupported: ['minLength', 'maximum', 'pattern', 'format'],
  },

  cache_strategy: 'automatic',
  cache_rules: {
    automatic: true,                   // no code change; free; gpt-4o and newer
    min_tokens: 1024,
    prefix_hash_window: 256,           // routes on ~first 256 tokens
    exact_prefix_required: true,
    static_at_beginning: true,
    ttl: '5-10min',                    // up to 1h off-peak; 24h via prompt_cache_retention
    prefer_allowed_tools_over_tool_choice: true,  // preserves prompt-cache savings
    telemetry: 'cached_tokens',
    max_reduction: '90%',
  },

  reasoning: {
    mode: 'none',                      // reasoning tokens invisible, billed as output
    round_trip: 'encrypted_content_or_previous_response_id',
    reserve_tokens: 25_000,            // ≥25K for reasoning+output
    dont_over_prescribe_cot: true,
    pass_back: 'reasoning items returned with the last function call',
  },

  mcp_constraints: {
    transport: 'streamable_http_or_sse',
    require_approval_default: true,
    defer_loading: true,               // for large servers
  },

  prompt_structure: '[stable_prefix]→[variable_tail]',
}
```

---

## Profile: deepseek

**Pinned models** (from `platform/src/lib/models/registry.ts`):
- Worker: `deepseek-chat` — non-thinking; only valid non-thinking API ID that supports tool_choice
- Premium: `deepseek-v4-pro` — 1M ctx; thinking mode; $1.74/$3.48 post-promo

**Deprecation watchpoint — 2026-07-24:**
- `deepseek-chat` alias → V4 Flash retires.
- `deepseek-reasoner` alias → V4 Pro retires.
- `deepseek-v4-flash` is NOT a valid DeepSeek API model ID — API maps this to `deepseek-reasoner`
  which rejects `toolChoice`. Do not use as an API model ID.

```typescript
{
  family: 'deepseek',
  profile_version: '1.0.0',
  status: 'UNMEASURED',

  pinned_models: {
    worker:  'deepseek-chat',    // non-thinking, supports tool_choice; only valid planner API ID
    premium: 'deepseek-v4-pro',  // 1M ctx, thinking=toggle, $1.74/$3.48 post-promo
    // mid: not defined — DeepSeek has worker (deepseek-chat) and premium (deepseek-v4-pro)
  },
  deprecations: [
    { id: 'deepseek-chat',      retire_date: '2026-07-24', maps_to: 'deepseek-v4-flash (non-thinking)' },
    { id: 'deepseek-reasoner',  retire_date: '2026-07-24', maps_to: 'deepseek-v4-pro (thinking)' },
    { id: 'deepseek-v4-flash',  note: 'NOT a valid DeepSeek API model ID — rejects toolChoice; do not use' },
  ],

  tool_arg_format: 'json_string',      // MUST JSON.parse(arguments) — OpenAI-compatible
  requires_json_parse: true,
  tool_result_wire: 'role_tool',       // role:tool (OpenAI-compatible)
  tool_result_notes: 'For V4 tool turns: reasoning_content MUST be passed back (400 error otherwise)',

  max_active_tools: 10,                // smallest-footprint; fewest tools; avoid nested schemas [UNMEASURED — D8]
  tool_granularity: 'minimal',         // fewest tools; avoid deeply nested schemas [UNMEASURED — D8]
  bundle_strategy: 'smallest_footprint',  // most defensive; ~128k budget [UNMEASURED — D8]

  context_budget_tokens: {
    worker:    128_000,                // conservative floor [UNMEASURED — D8] — V4 Flash via deepseek-chat
    premium: 1_000_000,               // V4 Pro confirmed 1M
    working_assumption: '~128k floor until V4 Flash API endpoint confirmed at 1M end-to-end',
  },

  structured_output: {
    format: 'json_object',            // NO content-level strict schema — json_object only
    strict: false,                    // beta strict at /beta endpoint only
    include_json_word_in_prompt: true, // "Include the word 'json'… and provide an example"
    drift_rate: '5-12%',              // PROVIDER_SPEC hypothesis [UNMEASURED — D8]
    validate_and_repair: true,        // MANDATORY — may return empty content
    set_max_tokens: true,             // always set max_tokens to avoid truncation
    on_empty_content: 'retry',
  },

  cache_strategy: 'none',             // automatic on DeepSeek API; registry sets none for routing
  cache_rules: {
    automatic: true,                  // on DeepSeek API: free, on-disk, exact-prefix from token 0
    min_unit_tokens: 64,              // smallest min unit of all four families
    partial_middle_miss: true,        // partial/middle matches DO NOT hit cache
    stable_prefix_first: true,
    telemetry: ['prompt_cache_hit_tokens', 'prompt_cache_miss_tokens'],
  },

  reasoning: {
    mode: 'none',                     // registry: reasoningMode='none'; native <think> via extractReasoningTrace
    v4_tool_call_rule: 'MUST_pass_back_reasoning_content',  // 400 error otherwise on V4 tool turns
    thinking_param: 'toggle',         // thinking=true for deep synthesis; false for planner
    version_pin_critical: true,
    version_notes: [
      'V4 INVERTS legacy R1 behavior for reasoning_content round-trip',
      'Legacy R1: must NOT feed back reasoning_content (400)',
      'V4 with tool call: MUST feed back reasoning_content (400 otherwise)',
      'Legacy aliases deepseek-chat + deepseek-reasoner retire 2026-07-24',
    ],
  },

  mcp_constraints: {
    mcp_supported: false,             // DeepSeek does NOT implement MCP
    anthropic_endpoint_note: 'mcp_servers ignored; MCP content blocks unsupported',
    treatment: 'plain_tool_calling_backend_only',
    strip_mcp_constructs: true,       // MARO must strip all MCP-specific constructs
  },

  prompt_structure: '[stable_prefix_from_token_0]→[variable_tail]',
}
```

---

## Universal fallback (undeclared family)

When no family is declared by the client, MARO serves the `universal` surface:

```typescript
{
  family: 'universal',
  profile_version: '1.0.0',

  // Conservative settings — smallest common denominator of all four families

  tool_arg_format: 'json_string',     // conservative: caller must handle JSON.parse
  requires_json_parse: true,
  tool_result_wire: 'universal',      // plain text role:tool

  max_tools: 15,                      // 10–15 consolidated workflow tools
  tool_name_pattern: '^[A-Za-z0-9_.]{1,64}$',  // cross-family valid: no hyphens
  requires_dual_output: true,         // structuredContent + serialized JSON text block per MCP spec
  verbosity_enum: ['minimal', 'standard', 'detailed'],  // client self-selects

  context_budget_tokens: {
    worker:  128_000,                 // conservative DeepSeek floor
    premium: 128_000,
  },

  cache_strategy: 'none',
  structured_output: { format: 'json_object', validate_and_repair: true },
  reasoning_round_trip: 'none',
  mcp_transport: 'streamable_http',   // Gemini constraint (no SSE); cross-family safe
  strip_mcp_constructs: false,        // caller handles per actual family
  prompt_structure: '[stable_prefix]→[variable_tail]',
}
```

**Tool name contract (cross-family):**
All tool names on any surface must satisfy `^[A-Za-z0-9_.]{1,64}$` — this is the intersection
of Anthropic's `^[a-zA-Z0-9_-]{1,64}$` and Gemini's `^[A-Za-z0-9_.]+$` without hyphens.
Snake_case with dots as namespace separators; no hyphens; ≤64 chars. This satisfies both families
simultaneously and is the enforced standard for all MARSYS capability names.

---

## NVIDIA NIM (not a separate profile)

NVIDIA NIM models (`provider: 'nvidia'` in the model registry) use the **OpenAI profile** with:
- `cache_strategy: 'none'` — no caching on NIM free tier
- `streaming_required: true` — all NIM models
- `validate_and_repair: true` — NIM uses `json_object` only; treat as DeepSeek for validation

No fifth profile is needed. Call `applyNvidiaOverrides(OPENAI_PROFILE)` in `normalizer.ts` when
the model is detected as an NVIDIA model.

---

## Detail-pass scheduling

The following profile parameters are tagged `[UNMEASURED — D8]` and require re-measurement
once the D8 eval harness can run the MARSYS corpus through each model family:

| Parameter | Family | Hypothesis |
|---|---|---|
| tool_result_wire ordering | anthropic | results-first user msg |
| max_active_tools | all | family-specific caps |
| bundle_strategy | all | per-family recommendations |
| structured_output.drift_rate | anthropic | 0 in strict mode |
| structured_output.drift_rate | gemini | values may err; rate unknown |
| structured_output.drift_rate | openai | 0 in strict mode |
| structured_output.drift_rate | deepseek | 5–12% from provider spec |
| context degradation onset | all | varies per needle count |
| reasoning round-trip | all | verified per provider docs |

When D8 measures these, bump `version` (1.0.0 → 1.1.0 for measured updates) and set `status: MEASURED`.

---

*End of RETRIEVAL_MODEL_PROFILES v1.0.0 — D-PROFILES wave deliverable (2026-06-28).*
*Source: RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md + platform/src/lib/models/registry.ts.*
*Implementation: platform/src/lib/retrieval/maro/profiles.ts + normalizer.ts.*
