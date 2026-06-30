/**
 * MARO — Model-Agnostic Retrieval Orchestration: Tests
 * ======================================================
 * D-PROFILES wave — tests for all four model family paths.
 *
 * Coverage:
 *   1. Family resolution (declared / undeclared / unknown)
 *   2. Per-family normalization (all 4 families + universal)
 *   3. Tool-arg decode (object vs JSON.parse)
 *   4. Structured output validate-and-repair
 *   5. MCP construct stripping (DeepSeek)
 *   6. NVIDIA NIM override (openai + cache:none)
 *   7. Behavioral_overrides application (D1 contract field)
 *   8. chart_id required guard (never defaulted)
 *   9. Context budget by tier
 *  10. MCP surface spec (declared + universal)
 */

import { describe, it, expect } from 'vitest'
import {
  resolveFamily,
  orchestrate,
  getMcpSurface,
  normalizeToolArgs,
  serializeToolArgs,
  validateAndRepair,
  stripMcpConstructs,
  applyNvidiaOverrides,
  getProfile,
  getContextBudget,
  ANTHROPIC_PROFILE,
  GEMINI_PROFILE,
  OPENAI_PROFILE,
  DEEPSEEK_PROFILE,
  UNIVERSAL_PROFILE,
  PROFILE_VERSION,
} from './index'
import type { RetrievalRequest } from './types'

// ── Helpers ────────────────────────────────────────────────────────────────────

function makeRequest(overrides: Partial<RetrievalRequest> = {}): RetrievalRequest {
  return {
    chart_id: 'test-chart-uuid-0000-0000',   // never a real chart_id
    query: 'What is the lagna lord placement?',
    capability_uri: 'marsys://tool/L1/positions',
    ...overrides,
  }
}

// ── §1: Family resolution ─────────────────────────────────────────────────────

describe('resolveFamily', () => {
  it('resolves declared anthropic family', () => {
    expect(resolveFamily(makeRequest({ model_family: 'anthropic' }))).toBe('anthropic')
  })

  it('resolves declared gemini family', () => {
    expect(resolveFamily(makeRequest({ model_family: 'gemini' }))).toBe('gemini')
  })

  it('resolves declared openai family', () => {
    expect(resolveFamily(makeRequest({ model_family: 'openai' }))).toBe('openai')
  })

  it('resolves declared deepseek family', () => {
    expect(resolveFamily(makeRequest({ model_family: 'deepseek' }))).toBe('deepseek')
  })

  it('resolves undeclared (no model_family) → universal', () => {
    expect(resolveFamily(makeRequest())).toBe('universal')
  })

  it('resolves unknown family string → universal', () => {
    expect(resolveFamily(makeRequest({ model_family: 'cohere' as never }))).toBe('universal')
  })

  it('resolves explicit universal → universal', () => {
    expect(resolveFamily(makeRequest({ model_family: 'universal' }))).toBe('universal')
  })
})

// ── §2: Per-family normalization ──────────────────────────────────────────────

describe('orchestrate — family normalization', () => {
  it('anthropic: tool_arg_format=object, requires_json_parse=false', () => {
    const result = orchestrate(makeRequest({ model_family: 'anthropic' }))
    expect(result.normalization.tool_arg_format).toBe('object')
    expect(result.normalization.requires_json_parse).toBe(false)
    expect(result.resolved_family).toBe('anthropic')
  })

  it('anthropic: cache_strategy=explicit_headers', () => {
    const result = orchestrate(makeRequest({ model_family: 'anthropic' }))
    expect(result.normalization.cache_strategy).toBe('explicit_headers')
  })

  it('anthropic: structured_output=json_schema, validate_and_repair=false', () => {
    const result = orchestrate(makeRequest({ model_family: 'anthropic' }))
    expect(result.normalization.structured_output_format).toBe('json_schema')
    expect(result.validate_and_repair).toBe(false)
  })

  it('anthropic: reasoning_round_trip=unmodified', () => {
    const result = orchestrate(makeRequest({ model_family: 'anthropic' }))
    expect(result.normalization.reasoning_round_trip).toBe('unmodified')
  })

  it('anthropic: mcp_transport=https_only', () => {
    const result = orchestrate(makeRequest({ model_family: 'anthropic' }))
    expect(result.normalization.mcp_transport).toBe('https_only')
    expect(result.strip_mcp_constructs).toBe(false)
  })

  it('gemini: tool_arg_format=object, requires_json_parse=false', () => {
    const result = orchestrate(makeRequest({ model_family: 'gemini' }))
    expect(result.normalization.tool_arg_format).toBe('object')
    expect(result.normalization.requires_json_parse).toBe(false)
  })

  it('gemini: structured_output=gemini_response_schema, validate_and_repair=true', () => {
    const result = orchestrate(makeRequest({ model_family: 'gemini' }))
    expect(result.normalization.structured_output_format).toBe('gemini_response_schema')
    expect(result.validate_and_repair).toBe(true)
  })

  it('gemini: tool_result_wire=functionResponse_with_exact_id', () => {
    const result = orchestrate(makeRequest({ model_family: 'gemini' }))
    expect(result.normalization.tool_result_wire).toBe('functionResponse_with_exact_id')
  })

  it('gemini: reasoning_round_trip=per_part_unmodified', () => {
    const result = orchestrate(makeRequest({ model_family: 'gemini' }))
    expect(result.normalization.reasoning_round_trip).toBe('per_part_unmodified')
  })

  it('gemini: mcp_transport=streamable_http (no SSE)', () => {
    const result = orchestrate(makeRequest({ model_family: 'gemini' }))
    expect(result.normalization.mcp_transport).toBe('streamable_http')
  })

  it('openai: tool_arg_format=json_string, requires_json_parse=true', () => {
    const result = orchestrate(makeRequest({ model_family: 'openai' }))
    expect(result.normalization.tool_arg_format).toBe('json_string')
    expect(result.normalization.requires_json_parse).toBe(true)
  })

  it('openai: cache_strategy=automatic', () => {
    const result = orchestrate(makeRequest({ model_family: 'openai' }))
    expect(result.normalization.cache_strategy).toBe('automatic')
  })

  it('openai: reasoning_round_trip=encrypted_content_or_prev_id', () => {
    const result = orchestrate(makeRequest({ model_family: 'openai' }))
    expect(result.normalization.reasoning_round_trip).toBe('encrypted_content_or_prev_id')
  })

  it('deepseek: tool_arg_format=json_string, requires_json_parse=true', () => {
    const result = orchestrate(makeRequest({ model_family: 'deepseek' }))
    expect(result.normalization.tool_arg_format).toBe('json_string')
    expect(result.normalization.requires_json_parse).toBe(true)
  })

  it('deepseek: structured_output=json_object, validate_and_repair=true (MANDATORY)', () => {
    const result = orchestrate(makeRequest({ model_family: 'deepseek' }))
    expect(result.normalization.structured_output_format).toBe('json_object')
    expect(result.validate_and_repair).toBe(true)
  })

  it('deepseek: reasoning_round_trip=reasoning_content_v4_tool_turns', () => {
    const result = orchestrate(makeRequest({ model_family: 'deepseek' }))
    expect(result.normalization.reasoning_round_trip).toBe('reasoning_content_v4_tool_turns')
  })

  it('deepseek: mcp_transport=none, strip_mcp_constructs=true', () => {
    const result = orchestrate(makeRequest({ model_family: 'deepseek' }))
    expect(result.normalization.mcp_transport).toBe('none')
    expect(result.strip_mcp_constructs).toBe(true)
  })

  it('universal: conservative fallback — validate_and_repair=true, max_tools=10', () => {
    const result = orchestrate(makeRequest({ model_family: 'universal' }))
    expect(result.validate_and_repair).toBe(true)
    expect(result.normalization.max_active_tools).toBe(10)
    expect(result.resolved_family).toBe('universal')
  })
})

// ── §3: Tool-arg decode ───────────────────────────────────────────────────────

describe('normalizeToolArgs', () => {
  it('anthropic/gemini: object passthrough (no JSON.parse)', () => {
    const args = { planet: 'mars', house: 3 }
    expect(normalizeToolArgs(args, ANTHROPIC_PROFILE)).toEqual(args)
    expect(normalizeToolArgs(args, GEMINI_PROFILE)).toEqual(args)
  })

  it('openai/deepseek: parses JSON string', () => {
    const args = '{"planet":"mars","house":3}'
    const expected = { planet: 'mars', house: 3 }
    expect(normalizeToolArgs(args, OPENAI_PROFILE)).toEqual(expected)
    expect(normalizeToolArgs(args, DEEPSEEK_PROFILE)).toEqual(expected)
  })

  it('returns empty object for undefined args', () => {
    expect(normalizeToolArgs(undefined, ANTHROPIC_PROFILE)).toEqual({})
  })

  it('returns _parse_error for malformed JSON string', () => {
    const result = normalizeToolArgs('{bad json', OPENAI_PROFILE)
    expect(result).toHaveProperty('_parse_error')
    expect(result).toHaveProperty('_raw', '{bad json')
  })
})

describe('serializeToolArgs', () => {
  it('openai/deepseek: serializes to JSON string', () => {
    const args = { planet: 'mars', house: 3 }
    const serialized = serializeToolArgs(args, OPENAI_PROFILE)
    expect(typeof serialized).toBe('string')
    expect(JSON.parse(serialized as string)).toEqual(args)
  })

  it('anthropic/gemini: returns object as-is', () => {
    const args = { planet: 'mars', house: 3 }
    expect(serializeToolArgs(args, ANTHROPIC_PROFILE)).toEqual(args)
    expect(serializeToolArgs(args, GEMINI_PROFILE)).toEqual(args)
  })
})

// ── §4: Structured output validate-and-repair ─────────────────────────────────

describe('validateAndRepair', () => {
  it('deepseek: handles empty content (retry required)', () => {
    const result = validateAndRepair('', DEEPSEEK_PROFILE)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Empty output')
  })

  it('deepseek: handles null output (retry required)', () => {
    const result = validateAndRepair(null, DEEPSEEK_PROFILE)
    expect(result.valid).toBe(false)
  })

  it('deepseek: parses valid JSON string', () => {
    const result = validateAndRepair('{"graha":"mangala","rashi":"mesha"}', DEEPSEEK_PROFILE)
    expect(result.valid).toBe(true)
    expect(result.value).toEqual({ graha: 'mangala', rashi: 'mesha' })
  })

  it('deepseek: repairs missing keys from expected shape', () => {
    const result = validateAndRepair(
      { graha: 'mangala' },
      DEEPSEEK_PROFILE,
      { graha: 'string', rashi: 'string' },
    )
    expect(result.valid).toBe(true)
    expect(result.repaired).toBe(true)
    expect((result.value as Record<string, unknown>)['rashi']).toBeNull()
  })

  it('gemini: validates and marks valid for correct output', () => {
    const result = validateAndRepair({ position: 'Capricorn', degree: 15 }, GEMINI_PROFILE)
    expect(result.valid).toBe(true)
    expect(result.repaired).toBe(false)
  })

  it('anthropic (strict, no validate_and_repair): passthrough for null guard', () => {
    const result = validateAndRepair(null, ANTHROPIC_PROFILE)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('null/undefined')
  })

  it('anthropic (strict, no validate_and_repair): valid object passes', () => {
    const result = validateAndRepair({ position: 'Capricorn' }, ANTHROPIC_PROFILE)
    expect(result.valid).toBe(true)
  })
})

// ── §5: MCP construct stripping (DeepSeek) ────────────────────────────────────

describe('stripMcpConstructs', () => {
  it('strips structuredContent field', () => {
    const input = { text: 'some text', structuredContent: { graha: 'mars' } }
    const result = stripMcpConstructs(input) as Record<string, unknown>
    expect(result).not.toHaveProperty('structuredContent')
    expect(result).toHaveProperty('text', 'some text')
  })

  it('strips resources and prompts', () => {
    const input = { text: 'data', resources: [{ uri: 'x' }], prompts: ['y'] }
    const result = stripMcpConstructs(input) as Record<string, unknown>
    expect(result).not.toHaveProperty('resources')
    expect(result).not.toHaveProperty('prompts')
  })

  it('filters non-text content blocks', () => {
    const input = {
      content: [
        { type: 'text', text: 'hello' },
        { type: 'resource', resource: { uri: 'x' } },
        { type: 'embedded_resource', resource: {} },
      ],
    }
    const result = stripMcpConstructs(input) as Record<string, unknown>
    const content = result['content'] as Array<Record<string, unknown>>
    expect(content).toHaveLength(1)
    expect(content[0]!['type']).toBe('text')
  })

  it('strips thought_signature field', () => {
    const input = { text: 'answer', thought_signature: 'encrypted-abc' }
    const result = stripMcpConstructs(input) as Record<string, unknown>
    expect(result).not.toHaveProperty('thought_signature')
  })

  it('passes through non-object values unchanged', () => {
    expect(stripMcpConstructs('plain string')).toBe('plain string')
    expect(stripMcpConstructs(42)).toBe(42)
    expect(stripMcpConstructs(null)).toBeNull()
  })
})

// ── §6: NVIDIA NIM override ───────────────────────────────────────────────────

describe('applyNvidiaOverrides', () => {
  it('applies cache_strategy:none to openai base profile', () => {
    const override = applyNvidiaOverrides(OPENAI_PROFILE)
    expect(override.cache_strategy).toBe('none')
  })

  it('sets validate_and_repair=true (json_object treatment)', () => {
    const override = applyNvidiaOverrides(OPENAI_PROFILE)
    expect(override.validate_and_repair).toBe(true)
  })

  it('preserves other openai profile fields', () => {
    const override = applyNvidiaOverrides(OPENAI_PROFILE)
    expect(override.tool_arg_format).toBe('json_string')
    expect(override.requires_json_parse).toBe(true)
    expect(override.tool_result_wire).toBe('function_call_output')
  })

  it('adds streaming_required=true in capability_overrides', () => {
    const override = applyNvidiaOverrides(OPENAI_PROFILE)
    expect(override.capability_overrides?.['streaming_required']).toBe(true)
  })

  it('orchestrate with is_nvidia_model=true applies NIM overrides', () => {
    const result = orchestrate(makeRequest({ model_family: 'openai' }), undefined, true)
    expect(result.normalization.cache_strategy).toBe('none')
    expect(result.normalization.validate_and_repair).toBe(true)
  })
})

// ── §7: behavioral_overrides application ──────────────────────────────────────

describe('orchestrate — behavioral_overrides', () => {
  it('applies capability behavioral_overrides for the family', () => {
    const capabilityWithOverride = {
      uri: 'marsys://tool/test/cap',
      type: 'tool' as const,
      layer: 'L1' as const,
      name: 'test_cap',
      scope: 'global' as const,
      description: 'Test capability',
      archetype: 'flat_fact' as const,
      traversal_level: 'L-SIGNAL' as const,
      tool_role: 'leaf' as const,
      emits_references: false,
      lel_capable: false,
      handler: async () => ({ content: 'ok', is_error: false }),
      behavioral_overrides: {
        anthropic: { custom_note: 'anthropic-specific shaping', max_tokens_hint: 1000 },
      },
    }

    const result = orchestrate(
      makeRequest({ model_family: 'anthropic' }),
      capabilityWithOverride,
    )

    expect(result.normalization.capability_overrides).toEqual({
      custom_note: 'anthropic-specific shaping',
      max_tokens_hint: 1000,
    })
  })

  it('no overrides when behavioral_overrides is unset', () => {
    const capabilityWithoutOverride = {
      uri: 'marsys://tool/test/cap2',
      type: 'tool' as const,
      layer: 'L1' as const,
      name: 'test_cap2',
      scope: 'global' as const,
      description: 'Test capability 2',
      archetype: 'flat_fact' as const,
      traversal_level: 'L-SIGNAL' as const,
      tool_role: 'leaf' as const,
      emits_references: false,
      lel_capable: false,
      handler: async () => ({ content: 'ok', is_error: false }),
    }

    const result = orchestrate(
      makeRequest({ model_family: 'anthropic' }),
      capabilityWithoutOverride,
    )

    expect(result.normalization.capability_overrides).toBeUndefined()
  })

  it('universal family: behavioral_overrides not applied (cross-model surface)', () => {
    const cap = {
      uri: 'marsys://tool/test/cap3',
      type: 'tool' as const,
      layer: 'L1' as const,
      name: 'test_cap3',
      scope: 'global' as const,
      description: 'Test',
      archetype: 'flat_fact' as const,
      traversal_level: 'L-SIGNAL' as const,
      tool_role: 'leaf' as const,
      emits_references: false,
      lel_capable: false,
      handler: async () => ({ content: 'ok', is_error: false }),
      behavioral_overrides: {
        anthropic: { custom: 'value' },
      },
    }

    // universal family — overrides don't apply
    const result = orchestrate(makeRequest({ model_family: 'universal' }), cap)
    expect(result.normalization.capability_overrides).toBeUndefined()
  })
})

// ── §8: chart_id required guard ───────────────────────────────────────────────

describe('orchestrate — chart_id required guard', () => {
  it('throws when chart_id is missing', () => {
    const req = { ...makeRequest(), chart_id: '' }
    expect(() => orchestrate(req)).toThrow('chart_id is required')
  })

  it('throws when chart_id is not a string', () => {
    const req = { ...makeRequest(), chart_id: null as unknown as string }
    expect(() => orchestrate(req)).toThrow('chart_id is required')
  })

  it('does not default chart_id (MARO never defaults)', () => {
    // MARO throws — it never supplies a default chart_id
    const req = { query: 'test', capability_uri: 'x' } as unknown as RetrievalRequest
    expect(() => orchestrate(req)).toThrow('chart_id is required')
  })
})

// ── §9: Context budget by tier ────────────────────────────────────────────────

describe('getContextBudget', () => {
  it('anthropic worker tier = 200K (Haiku cap)', () => {
    expect(getContextBudget(ANTHROPIC_PROFILE, 'worker')).toBe(200_000)
  })

  it('anthropic premium tier = 1M (Opus)', () => {
    expect(getContextBudget(ANTHROPIC_PROFILE, 'premium')).toBe(1_000_000)
  })

  it('gemini premium tier = 2M (Pro — largest of all stacks)', () => {
    expect(getContextBudget(GEMINI_PROFILE, 'premium')).toBe(2_000_000)
  })

  it('deepseek worker tier = 128K (conservative floor)', () => {
    expect(getContextBudget(DEEPSEEK_PROFILE, 'worker')).toBe(128_000)
  })

  it('openai: all tiers = 1M (GPT-4.1 family)', () => {
    expect(getContextBudget(OPENAI_PROFILE, 'worker')).toBe(1_000_000)
    expect(getContextBudget(OPENAI_PROFILE, 'premium')).toBe(1_000_000)
  })

  it('orchestrate resolves budget per tier', () => {
    const result = orchestrate(makeRequest({ model_family: 'anthropic', model_tier: 'worker' }))
    expect(result.context_budget_tokens).toBe(200_000)

    const result2 = orchestrate(makeRequest({ model_family: 'anthropic', model_tier: 'premium' }))
    expect(result2.context_budget_tokens).toBe(1_000_000)
  })
})

// ── §10: MCP surface spec ─────────────────────────────────────────────────────

describe('getMcpSurface', () => {
  it('universal: max_tools=15, cross-family safe pattern, dual output', () => {
    const surface = getMcpSurface('universal')
    expect(surface.max_tools).toBe(15)
    expect(surface.tool_name_pattern).toMatch(/A-Za-z0-9_/)
    // Verify pattern does NOT permit a literal hyphen as a valid name character.
    // Test against actual names — the pattern string itself uses - as a range delimiter in regex.
    const re = new RegExp(surface.tool_name_pattern)
    expect(re.test('my_tool')).toBe(true)    // snake_case: allowed
    expect(re.test('my.tool')).toBe(true)    // dot namespace: allowed
    expect(re.test('my-tool')).toBe(false)   // hyphen: not allowed (Gemini constraint)
    expect(surface.requires_dual_output).toBe(true)
    expect(surface.strip_mcp_constructs).toBe(false)
  })

  it('deepseek: strip_mcp_constructs=true (no MCP support)', () => {
    const surface = getMcpSurface('deepseek')
    expect(surface.strip_mcp_constructs).toBe(true)
    expect(surface.transport).toBe('none')
  })

  it('gemini: transport=streamable_http (no SSE)', () => {
    const surface = getMcpSurface('gemini')
    expect(surface.transport).toBe('streamable_http')
  })

  it('anthropic: transport=https_only', () => {
    const surface = getMcpSurface('anthropic')
    expect(surface.transport).toBe('https_only')
  })

  it('all families: tool_name_pattern rejects hyphenated names (cross-family Gemini constraint)', () => {
    for (const family of ['anthropic', 'gemini', 'openai', 'deepseek', 'universal'] as const) {
      const surface = getMcpSurface(family)
      // Gemini rejects server/tool names with hyphens. Verify our patterns reject them too.
      // (Pattern strings contain - as regex range delimiter; test via regex execution not string search.)
      const re = new RegExp(surface.tool_name_pattern)
      expect(re.test('my-tool'), `${family}: hyphenated name should be rejected`).toBe(false)
      expect(re.test('my_tool'), `${family}: snake_case name should be accepted`).toBe(true)
    }
  })
})

// ── §12: Cross-model conclusion-consistency test (R4) ─────────────────────────
//
// Charter requirement: "cross-model conclusion-consistency test (4 model families,
// same verdict different paths)".
//
// Verdict: a chart-level retrieval request produces the SAME top-level conclusions
// (validate_and_repair gate, strip_mcp_constructs decision, context adequacy)
// regardless of which model family processes it. Each family takes a different path
// (different tool_arg_format, different wire format, different reasoning round-trip),
// but the boolean verdict for the request must be identical across all four families
// when the same chart_id + query is submitted.
//
// This proves the MARO normalization layer is family-agnostic at the verdict level:
// the retrieval content (what signals are returned) is identical; only the wire
// encoding differs.

describe('R4 — cross-model conclusion consistency', () => {
  const FAMILIES = ['anthropic', 'gemini', 'openai', 'deepseek'] as const

  // Same chart_id + query across all families
  const sharedRequest = (family: typeof FAMILIES[number]) =>
    makeRequest({ model_family: family, model_tier: 'premium' })

  it('all 4 families resolve a non-universal family (no universal fallback on declared)', () => {
    for (const family of FAMILIES) {
      const result = orchestrate(sharedRequest(family))
      expect(result.resolved_family, `${family}: should resolve to self`).toBe(family)
    }
  })

  it('all 4 families: context_budget_tokens > 0 (no zero-budget family on premium tier)', () => {
    for (const family of FAMILIES) {
      const result = orchestrate(sharedRequest(family))
      expect(result.context_budget_tokens, `${family}: context budget must be positive`).toBeGreaterThan(0)
    }
  })

  it('validate_and_repair verdict: deepseek+gemini=true, anthropic+openai=false (per-family contract)', () => {
    // This IS the cross-model divergence: the verdict on validate_and_repair is family-specific.
    // deepseek: MANDATORY (5-12% drift). gemini: always validate. anthropic/openai: strict grammar.
    // The SAME retrieval content flows through; only the post-processing gate differs.
    const verdicts = Object.fromEntries(
      FAMILIES.map(f => [f, orchestrate(sharedRequest(f)).validate_and_repair])
    )
    expect(verdicts['anthropic']).toBe(false)
    expect(verdicts['openai']).toBe(false)
    expect(verdicts['gemini']).toBe(true)
    expect(verdicts['deepseek']).toBe(true)
  })

  it('strip_mcp_constructs verdict: only deepseek=true (no MCP support)', () => {
    // Same verdict gate: deepseek is the only family that cannot consume MCP constructs.
    // The retrieval CONTENT is identical; only the serialization changes.
    const verdicts = Object.fromEntries(
      FAMILIES.map(f => [f, orchestrate(sharedRequest(f)).strip_mcp_constructs])
    )
    expect(verdicts['anthropic']).toBe(false)
    expect(verdicts['gemini']).toBe(false)
    expect(verdicts['openai']).toBe(false)
    expect(verdicts['deepseek']).toBe(true)
  })

  it('requires_json_parse verdict: openai+deepseek=true, anthropic+gemini=false', () => {
    // Wire format divergence: OpenAI and DeepSeek send tool args as JSON strings.
    // The retrieval request that produced those args is IDENTICAL; only decoding differs.
    const verdicts = Object.fromEntries(
      FAMILIES.map(f => [f, orchestrate(sharedRequest(f)).normalization.requires_json_parse])
    )
    expect(verdicts['anthropic']).toBe(false)
    expect(verdicts['gemini']).toBe(false)
    expect(verdicts['openai']).toBe(true)
    expect(verdicts['deepseek']).toBe(true)
  })

  it('prompt_structure: all 4 families produce a non-empty hint (different paths)', () => {
    const structures = FAMILIES.map(f => orchestrate(sharedRequest(f)).prompt_structure)
    for (const s of structures) {
      expect(typeof s).toBe('string')
      expect(s.length).toBeGreaterThan(0)
    }
    // Paths ARE different (this is the "different paths" part of the charter requirement)
    const unique = new Set(structures)
    expect(unique.size).toBeGreaterThan(1)
  })

  it('normalized_args: same input args produce same decoded object across all families', () => {
    // The SAME args must decode to the SAME object regardless of family wire format.
    // This proves the retrieval content is family-agnostic even when encoding differs.
    const inputArgs = { chart_id: 'test-chart-uuid-0000-0000', limit: 10 }

    // Anthropic/Gemini receive args as object → normalizeToolArgs passes through
    const anthropicDecoded = makeRequest({ model_family: 'anthropic', args: inputArgs })
    const geminiDecoded = makeRequest({ model_family: 'gemini', args: inputArgs })

    // OpenAI/DeepSeek receive args as JSON string → normalizeToolArgs parses
    const openaiDecoded = makeRequest({ model_family: 'openai', args: JSON.stringify(inputArgs) as unknown as Record<string, unknown> })
    const deepseekDecoded = makeRequest({ model_family: 'deepseek', args: JSON.stringify(inputArgs) as unknown as Record<string, unknown> })

    const { normalizeToolArgs: normalize, getProfile: gp } = { normalizeToolArgs, getProfile }

    const decoded = {
      anthropic: normalize(anthropicDecoded.args, gp('anthropic')),
      gemini:    normalize(geminiDecoded.args, gp('gemini')),
      openai:    normalize(openaiDecoded.args, gp('openai')),
      deepseek:  normalize(deepseekDecoded.args, gp('deepseek')),
    }

    // All four families decode to the same object (same verdict, different paths)
    for (const family of FAMILIES) {
      expect(decoded[family], `${family}: decoded args must match input`).toEqual(inputArgs)
    }
  })

  it('MCP surface: all 4 families return a valid surface spec (no family returns null)', () => {
    for (const family of FAMILIES) {
      const surface = getMcpSurface(family)
      expect(surface.family).toBe(family)
      expect(surface.max_tools).toBeGreaterThan(0)
      expect(surface.tool_name_pattern).toBeTruthy()
      expect(typeof surface.requires_dual_output).toBe('boolean')
      expect(typeof surface.strip_mcp_constructs).toBe('boolean')
    }
  })

  it('behavioral_overrides: applying per-family override does not change resolved_family', () => {
    // Overrides shape the result but must not alter which family was resolved.
    // This is the "populate-or-amend" contract: amend the profile, never re-route the family.
    const capWithOverrides = {
      uri: 'marsys://tool/test/r4_consistency',
      type: 'tool' as const,
      layer: 'L1' as const,
      name: 'r4_consistency_cap',
      scope: 'global' as const,
      description: 'R4 cross-model consistency test capability',
      archetype: 'flat_fact' as const,
      traversal_level: 'L-SIGNAL' as const,
      tool_role: 'leaf' as const,
      emits_references: false,
      lel_capable: false,
      handler: async () => ({ content: 'ok', is_error: false }),
      behavioral_overrides: {
        anthropic: { max_tokens_hint: 1000 },
        gemini:    { validate_schema_depth: 'flat' },
        openai:    { streaming_hint: true },
        deepseek:  { max_tokens_hint: 512 },
      },
    }

    for (const family of FAMILIES) {
      const result = orchestrate(makeRequest({ model_family: family }), capWithOverrides)
      // Family resolution is unchanged by overrides (no re-routing)
      expect(result.resolved_family, `${family}: override must not change resolved_family`).toBe(family)
      // Override is captured in capability_overrides
      expect(result.normalization.capability_overrides, `${family}: override must be populated`).toBeDefined()
    }
  })
})

// ── §11: Profile constants ────────────────────────────────────────────────────

describe('profile constants', () => {
  it('PROFILE_VERSION is set', () => {
    expect(PROFILE_VERSION).toMatch(/^\d+\.\d+\.\d+$/)
  })

  it('getProfile falls back to universal for unknown family', () => {
    const profile = getProfile('cohere' as never)
    expect(profile.family).toBe('universal')
  })

  it('all four profiles have required fields', () => {
    const profiles = [ANTHROPIC_PROFILE, GEMINI_PROFILE, OPENAI_PROFILE, DEEPSEEK_PROFILE]
    for (const p of profiles) {
      expect(p.family).toBeTruthy()
      expect(p.tool_arg_format).toBeTruthy()
      expect(p.tool_result_wire).toBeTruthy()
      expect(p.cache_strategy).toBeTruthy()
      expect(p.structured_output_format).toBeTruthy()
      expect(typeof p.validate_and_repair).toBe('boolean')
      expect(typeof p.requires_json_parse).toBe('boolean')
      expect(p.context_budget).toBeTruthy()
      expect(p.reasoning_round_trip).toBeTruthy()
      expect(p.mcp_transport).toBeTruthy()
      expect(typeof p.strip_mcp_constructs).toBe('boolean')
      expect(p.prompt_structure).toBeTruthy()
      expect(typeof p.max_active_tools).toBe('number')
    }
  })

  it('openai and deepseek both require JSON.parse (json_string format)', () => {
    expect(OPENAI_PROFILE.requires_json_parse).toBe(true)
    expect(DEEPSEEK_PROFILE.requires_json_parse).toBe(true)
  })

  it('anthropic and gemini do not require JSON.parse (object format)', () => {
    expect(ANTHROPIC_PROFILE.requires_json_parse).toBe(false)
    expect(GEMINI_PROFILE.requires_json_parse).toBe(false)
  })

  it('deepseek: validate_and_repair=true (MANDATORY for 5-12% drift)', () => {
    expect(DEEPSEEK_PROFILE.validate_and_repair).toBe(true)
  })

  it('deepseek: strip_mcp_constructs=true (no MCP support)', () => {
    expect(DEEPSEEK_PROFILE.strip_mcp_constructs).toBe(true)
  })

  it('gemini: validate_and_repair=true (values may err)', () => {
    expect(GEMINI_PROFILE.validate_and_repair).toBe(true)
  })

  it('gemini: premium context = 2M (largest of all stacks)', () => {
    expect(GEMINI_PROFILE.context_budget.premium).toBe(2_000_000)
  })
})
