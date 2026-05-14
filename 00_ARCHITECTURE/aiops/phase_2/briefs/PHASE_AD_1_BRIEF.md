---
status: OPEN
session_id: AIOPS_AD_1
phase: AD.1
phase_name: "ProviderQuirks registry extension"
next_session: AIOPS_AD_2
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_AD_1
## AIOps Phase 2, Step 1 — Add ProviderQuirks metadata to every model

---

## §0 — Executor orientation

AD.1 extends `ModelMeta` with the `quirks: ProviderQuirks` field, then
populates every entry in the `MODELS` array. The `quirks` shape is data, not
code — adding a new model in Phase 2 onward means editing one entry, not
five files. This phase is high-volume mechanical work with rigorous testing.

Master plan §3 has the full `ProviderQuirks` taxonomy. Master plan §6 has
per-provider example shapes.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md §3, §6
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/lib/models/registry.ts (existing MODELS array — every entry)
5. platform/src/lib/adapters/types.ts (from AD.0)
6. Provider docs (skim, not exhaustive):
   - Anthropic prompt-caching headers
   - Gemini safety + thinking config
   - DeepSeek thinking mode toggle
   - OpenAI structured outputs (json_schema)
   - NIM OpenAI-compat catalog quirks
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/models/registry.ts           # extend ModelMeta + populate all entries
platform/src/lib/adapters/types.ts            # add ProviderQuirks type if not already there
platform/src/lib/adapters/__tests__/quirks.test.ts  # NEW exhaustive tests
CLAUDECODE_BRIEF.md
```

### must_not_touch
- Everything outside `may_touch`.
- Specifically: do NOT delete `reasoningMode` from ModelMeta yet — it stays as a redundant duplicate of `quirks.reasoning_via` until AD.4 migrates consumers.

---

## §3 — Work plan

### 3.1 — Move ProviderQuirks type into adapters/types.ts (if needed)

Per master plan §3, `ProviderQuirks` lives in `lib/adapters/types.ts`.
Ensure it's exported and import it from `registry.ts`.

### 3.2 — Extend ModelMeta

In `platform/src/lib/models/registry.ts`:

```ts
import type { ProviderQuirks } from '@/lib/adapters/types'

export interface ModelMeta {
  // ... existing fields ...
  quirks: ProviderQuirks    // NEW — required field
}
```

The field is REQUIRED (not optional). Every entry must specify it or
compile fails.

### 3.3 — Populate quirks on every MODELS entry

The `MODELS` array contains every registered model. For each, add a `quirks`
field. Use the per-provider templates below.

**Anthropic models (haiku-4-5, sonnet-4-6, opus-4-7):**

```ts
quirks: {
  reasoning_via: 'none',
  streaming_required: false,
  tool_use_format: 'anthropic',
  structured_output_format: 'json_schema',
  cache_strategy: 'explicit_headers',
  system_prompt_shape: 'system_block_array',
}
```

**Gemini models (2.5-flash-lite, 2.5-flash, 2.5-pro):**

```ts
quirks: {
  reasoning_via: 'native',  // 2.5 models emit type:'reasoning' UIMessage parts
  streaming_required: false,
  tool_use_format: 'gemini',
  structured_output_format: 'gemini_response_schema',
  cache_strategy: 'context_caching',
  system_prompt_shape: 'system_message',
  request_transforms: { safety_filter: 'block_none', thinking_budget: 32768 },
}
```

**DeepSeek models:**

For `deepseek-v4-pro`:
```ts
quirks: {
  reasoning_via: 'markers',  // <think>...</think> blocks
  streaming_required: false,
  tool_use_format: 'openai',
  structured_output_format: 'json_object',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
  request_transforms: { thinking_mode: 'toggle' },
}
```

For `deepseek-chat` and `deepseek-v4-flash` (non-thinking):
```ts
quirks: {
  reasoning_via: 'none',
  streaming_required: false,
  tool_use_format: 'openai',
  structured_output_format: 'json_object',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
}
```

For `deepseek-reasoner` (deprecated alias — V4 Pro thinking):
```ts
quirks: {
  reasoning_via: 'markers',
  streaming_required: false,
  tool_use_format: 'none',  // rejects tool_choice — confirmed in nvidia.ts
  structured_output_format: 'none',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
}
```

**OpenAI models (gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini):**

```ts
quirks: {
  reasoning_via: 'none',  // future o-series will be 'native'
  streaming_required: false,
  tool_use_format: 'openai',
  structured_output_format: 'json_schema',
  cache_strategy: 'automatic',  // OpenAI handles caching automatically
  system_prompt_shape: 'system_message',
}
```

**NVIDIA NIM models:**

For Nemotron variants (`nvidia/nemotron-3-super-120b-a12b`, `nvidia/llama-3.3-nemotron-super-49b-v1`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`):
```ts
quirks: {
  reasoning_via: 'none',  // Nemotron does not surface reasoning today
  streaming_required: true,  // NIM managed catalog requires stream:true
  tool_use_format: 'openai',  // most variants — verify per-model in tests
  structured_output_format: 'json_object',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
}
```

For DeepSeek-on-NIM (`deepseek-ai/deepseek-v4-pro` — currently unavailable but registered):
```ts
quirks: {
  reasoning_via: 'markers',  // same <think> behavior as direct DeepSeek
  streaming_required: true,
  tool_use_format: 'openai',
  structured_output_format: 'json_object',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
  request_transforms: { thinking_mode: 'toggle' },
}
```

For Kimi K2 (`moonshotai/kimi-k2-instruct`):
```ts
quirks: {
  reasoning_via: 'none',
  streaming_required: true,
  tool_use_format: 'openai',
  structured_output_format: 'json_object',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
}
```

For Mistral Large 3 on NIM (`mistralai/mistral-large-3-675b-instruct-2512`):
```ts
quirks: {
  reasoning_via: 'none',
  streaming_required: true,
  tool_use_format: 'none',  // tool-use capability unverified per registry comment
  structured_output_format: 'none',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
}
```

For deprecated/EOL NIM models (`qwen/qwen3-235b-a22b`, `meta/llama-3.1-8b-instruct`, `nvidia/llama-3.1-nemotron-ultra-253b-v1`): populate with sensible defaults; they're not actively routed.

### 3.4 — Cross-check tool_use_format with reality

For models where `tool_use_format: 'openai'`, verify the model actually
supports tool_choice by checking NIM's `COMPAT_ERROR_PATTERNS` in
`platform/src/lib/models/nvidia.ts`. If a model has been known to reject
tool_choice (e.g., `deepseek-reasoner`), set `tool_use_format: 'none'`.

### 3.5 — Tests

`platform/src/lib/adapters/__tests__/quirks.test.ts`:

```ts
import { describe, test, expect } from 'vitest'
import { MODELS } from '@/lib/models/registry'
import type { ProviderQuirks } from '@/lib/adapters/types'

describe('ProviderQuirks coverage', () => {
  test('every model in registry has a quirks field', () => {
    for (const m of MODELS) {
      expect(m.quirks).toBeDefined()
    }
  })

  test('reasoning_via is consistent with reasoningMode', () => {
    for (const m of MODELS) {
      expect(m.quirks.reasoning_via).toBe(m.reasoningMode)
    }
  })

  test('all required quirks fields are populated', () => {
    const required: (keyof ProviderQuirks)[] = [
      'reasoning_via', 'streaming_required',
      'tool_use_format', 'structured_output_format',
      'cache_strategy', 'system_prompt_shape',
    ]
    for (const m of MODELS) {
      for (const f of required) {
        expect(m.quirks[f]).toBeDefined()
      }
    }
  })

  // Per-provider sanity:
  test('all Gemini models use gemini tool_use_format', () => { ... })
  test('all Anthropic models use system_block_array', () => { ... })
  test('all NIM models have streaming_required=true', () => { ... })
  test('only V4 Pro DeepSeek has thinking_mode in request_transforms', () => { ... })
  test('Gemini 2.5 models have safety_filter set to block_none', () => { ... })
  test('OpenAI cache_strategy is "automatic" universally', () => { ... })
  test('every model with reasoning_via != "none" can be enumerated', () => { ... })
})
```

≥30 test cases total. Parametrize where possible.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD1.1 | ModelMeta has `quirks: ProviderQuirks` field | grep + type |
| AC.AD1.2 | Every MODELS entry has quirks populated | parametrized test on `MODELS.length` matches |
| AC.AD1.3 | reasoning_via consistent with reasoningMode | parametrized test |
| AC.AD1.4 | All 6 required quirks subfields set on every entry | parametrized test |
| AC.AD1.5 | Per-provider sanity tests pass | ≥6 test cases |
| AC.AD1.6 | Total new tests | ≥30 |
| AC.AD1.7 | typecheck + lint + full test suite green | exit 0 each |
| AC.AD1.8 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Final commit:
```
feat(aiops-AD.1): ProviderQuirks metadata on every model

- ModelMeta extended with quirks: ProviderQuirks (required field)
- All N MODELS entries populated with per-provider quirks
- reasoning_via verified consistent with existing reasoningMode field
- 30+ tests covering coverage, consistency, per-provider sanity
- reasoningMode field preserved (redundant duplicate) until AD.4 migrates consumers

AC summary: 8/8 PASS
```

Rotate brief → AD.2.

---

## §7 — BAIL OUT triggers

- A model's tool_use_format is genuinely ambiguous (e.g., new NIM model with no prior compat data); bail and let native confirm.
- Type extension causes a typecheck cascade — investigate, but if more than 5 unrelated files break, bail.

---

*End of PHASE_AD_1_BRIEF.md*
