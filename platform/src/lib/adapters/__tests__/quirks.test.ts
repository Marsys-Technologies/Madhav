import { describe, test, expect } from 'vitest'
import { MODELS } from '@/lib/models/registry'
import type { ProviderQuirks } from '@/lib/adapters/types'

const REQUIRED_FIELDS: (keyof ProviderQuirks)[] = [
  'reasoning_via',
  'streaming_required',
  'tool_use_format',
  'structured_output_format',
  'cache_strategy',
  'system_prompt_shape',
]

const VALID_REASONING_VIA = ['markers', 'native', 'none'] as const
const VALID_TOOL_USE_FORMAT = ['openai', 'anthropic', 'gemini', 'none'] as const
const VALID_STRUCTURED_OUTPUT = ['json_schema', 'json_object', 'gemini_response_schema', 'none'] as const
const VALID_CACHE_STRATEGY = ['automatic', 'explicit_headers', 'context_caching', 'none'] as const
const VALID_SYSTEM_PROMPT_SHAPE = ['inline', 'system_message', 'system_block_array'] as const

describe('ProviderQuirks — coverage', () => {
  test('every model in registry has a quirks field', () => {
    expect(MODELS.length).toBeGreaterThan(0)
    for (const m of MODELS) {
      expect(m.quirks, `model ${m.id} missing quirks`).toBeDefined()
      expect(typeof m.quirks).toBe('object')
    }
  })

  test('quirks count matches MODELS count', () => {
    const withQuirks = MODELS.filter(m => m.quirks !== undefined)
    expect(withQuirks.length).toBe(MODELS.length)
  })
})

describe('ProviderQuirks — field validity', () => {
  test('all required quirks fields are present on every model', () => {
    for (const m of MODELS) {
      for (const f of REQUIRED_FIELDS) {
        expect(m.quirks[f], `model ${m.id} missing quirks.${f}`).toBeDefined()
      }
    }
  })

  test('reasoning_via values are within valid set', () => {
    for (const m of MODELS) {
      expect(
        VALID_REASONING_VIA.includes(m.quirks.reasoning_via as typeof VALID_REASONING_VIA[number]),
        `model ${m.id}: invalid reasoning_via=${m.quirks.reasoning_via}`,
      ).toBe(true)
    }
  })

  test('tool_use_format values are within valid set', () => {
    for (const m of MODELS) {
      expect(
        VALID_TOOL_USE_FORMAT.includes(m.quirks.tool_use_format as typeof VALID_TOOL_USE_FORMAT[number]),
        `model ${m.id}: invalid tool_use_format=${m.quirks.tool_use_format}`,
      ).toBe(true)
    }
  })

  test('structured_output_format values are within valid set', () => {
    for (const m of MODELS) {
      expect(
        VALID_STRUCTURED_OUTPUT.includes(m.quirks.structured_output_format as typeof VALID_STRUCTURED_OUTPUT[number]),
        `model ${m.id}: invalid structured_output_format=${m.quirks.structured_output_format}`,
      ).toBe(true)
    }
  })

  test('cache_strategy values are within valid set', () => {
    for (const m of MODELS) {
      expect(
        VALID_CACHE_STRATEGY.includes(m.quirks.cache_strategy as typeof VALID_CACHE_STRATEGY[number]),
        `model ${m.id}: invalid cache_strategy=${m.quirks.cache_strategy}`,
      ).toBe(true)
    }
  })

  test('system_prompt_shape values are within valid set', () => {
    for (const m of MODELS) {
      expect(
        VALID_SYSTEM_PROMPT_SHAPE.includes(m.quirks.system_prompt_shape as typeof VALID_SYSTEM_PROMPT_SHAPE[number]),
        `model ${m.id}: invalid system_prompt_shape=${m.quirks.system_prompt_shape}`,
      ).toBe(true)
    }
  })

  test('streaming_required is a boolean on every model', () => {
    for (const m of MODELS) {
      expect(typeof m.quirks.streaming_required, `model ${m.id}`).toBe('boolean')
    }
  })
})

describe('ProviderQuirks — consistency with reasoningMode', () => {
  test('reasoning_via is consistent with reasoningMode on every model', () => {
    for (const m of MODELS) {
      expect(
        m.quirks.reasoning_via,
        `model ${m.id}: quirks.reasoning_via=${m.quirks.reasoning_via} !== reasoningMode=${m.reasoningMode}`,
      ).toBe(m.reasoningMode)
    }
  })
})

describe('ProviderQuirks — per-provider sanity', () => {
  test('all Anthropic models use system_block_array', () => {
    const anthropic = MODELS.filter(m => m.provider === 'anthropic')
    expect(anthropic.length).toBeGreaterThan(0)
    for (const m of anthropic) {
      expect(m.quirks.system_prompt_shape, `model ${m.id}`).toBe('system_block_array')
    }
  })

  test('all Anthropic models use explicit_headers cache strategy', () => {
    const anthropic = MODELS.filter(m => m.provider === 'anthropic')
    for (const m of anthropic) {
      expect(m.quirks.cache_strategy, `model ${m.id}`).toBe('explicit_headers')
    }
  })

  test('all Anthropic models use anthropic tool_use_format', () => {
    const anthropic = MODELS.filter(m => m.provider === 'anthropic')
    for (const m of anthropic) {
      expect(m.quirks.tool_use_format, `model ${m.id}`).toBe('anthropic')
    }
  })

  test('all Gemini models use gemini tool_use_format', () => {
    const gemini = MODELS.filter(m => m.provider === 'google')
    expect(gemini.length).toBeGreaterThan(0)
    for (const m of gemini) {
      expect(m.quirks.tool_use_format, `model ${m.id}`).toBe('gemini')
    }
  })

  test('all Gemini models have reasoning_via native', () => {
    const gemini = MODELS.filter(m => m.provider === 'google')
    for (const m of gemini) {
      expect(m.quirks.reasoning_via, `model ${m.id}`).toBe('native')
    }
  })

  test('all Gemini models have safety_filter in request_transforms', () => {
    const gemini = MODELS.filter(m => m.provider === 'google')
    for (const m of gemini) {
      expect(m.quirks.request_transforms, `model ${m.id} missing request_transforms`).toBeDefined()
      expect(
        (m.quirks.request_transforms as Record<string, unknown>)?.safety_filter,
        `model ${m.id}`,
      ).toBe('block_none')
    }
  })

  test('all NIM (nvidia) models have streaming_required=true', () => {
    const nim = MODELS.filter(m => m.provider === 'nvidia')
    expect(nim.length).toBeGreaterThan(0)
    for (const m of nim) {
      expect(m.quirks.streaming_required, `model ${m.id}`).toBe(true)
    }
  })

  test('all NIM models use system_message prompt shape', () => {
    const nim = MODELS.filter(m => m.provider === 'nvidia')
    for (const m of nim) {
      expect(m.quirks.system_prompt_shape, `model ${m.id}`).toBe('system_message')
    }
  })

  test('all OpenAI models use automatic cache strategy', () => {
    const openai = MODELS.filter(m => m.provider === 'openai')
    expect(openai.length).toBeGreaterThan(0)
    for (const m of openai) {
      expect(m.quirks.cache_strategy, `model ${m.id}`).toBe('automatic')
    }
  })

  test('all OpenAI models use json_schema structured output', () => {
    const openai = MODELS.filter(m => m.provider === 'openai')
    for (const m of openai) {
      expect(m.quirks.structured_output_format, `model ${m.id}`).toBe('json_schema')
    }
  })

  test('deepseek-v4-pro has thinking_mode toggle in request_transforms', () => {
    const v4pro = MODELS.find(m => m.id === 'deepseek-v4-pro')
    expect(v4pro).toBeDefined()
    expect(v4pro!.quirks.request_transforms).toBeDefined()
    expect((v4pro!.quirks.request_transforms as Record<string, unknown>).thinking_mode).toBe('toggle')
  })

  test('only deepseek-v4-pro and deepseek-ai/deepseek-v4-pro have thinking_mode in request_transforms', () => {
    const withThinkingMode = MODELS.filter(m =>
      (m.quirks.request_transforms as Record<string, unknown> | undefined)?.thinking_mode !== undefined,
    )
    const ids = withThinkingMode.map(m => m.id).sort()
    expect(ids).toEqual(['deepseek-ai/deepseek-v4-pro', 'deepseek-v4-pro'])
  })

  test('deepseek-reasoner has tool_use_format none (rejects tool_choice)', () => {
    const reasoner = MODELS.find(m => m.id === 'deepseek-reasoner')
    expect(reasoner).toBeDefined()
    expect(reasoner!.quirks.tool_use_format).toBe('none')
  })

  test('models with reasoning_via != none can be enumerated and are only Gemini', () => {
    const reasoning = MODELS.filter(m => m.quirks.reasoning_via !== 'none')
    expect(reasoning.length).toBeGreaterThan(0)
    for (const m of reasoning) {
      expect(m.provider, `unexpected reasoning provider for ${m.id}`).toBe('google')
    }
  })

  test('non-streaming models do not have streaming_required=true', () => {
    const anthropic = MODELS.filter(m => m.provider === 'anthropic')
    const openai = MODELS.filter(m => m.provider === 'openai')
    const deepseek = MODELS.filter(m => m.provider === 'deepseek')
    const google = MODELS.filter(m => m.provider === 'google')
    for (const m of [...anthropic, ...openai, ...deepseek, ...google]) {
      expect(m.quirks.streaming_required, `model ${m.id}`).toBe(false)
    }
  })

  test('all DeepSeek models use system_message prompt shape', () => {
    const deepseek = MODELS.filter(m => m.provider === 'deepseek')
    expect(deepseek.length).toBeGreaterThan(0)
    for (const m of deepseek) {
      expect(m.quirks.system_prompt_shape, `model ${m.id}`).toBe('system_message')
    }
  })

  test('all DeepSeek models have cache_strategy none', () => {
    const deepseek = MODELS.filter(m => m.provider === 'deepseek')
    for (const m of deepseek) {
      expect(m.quirks.cache_strategy, `model ${m.id}`).toBe('none')
    }
  })

  test('Anthropic models do not have NIM streaming requirement', () => {
    const anthropic = MODELS.filter(m => m.provider === 'anthropic')
    for (const m of anthropic) {
      expect(m.quirks.streaming_required, `model ${m.id}`).toBe(false)
    }
  })

  test('Gemini models use context_caching strategy', () => {
    const gemini = MODELS.filter(m => m.provider === 'google')
    for (const m of gemini) {
      expect(m.quirks.cache_strategy, `model ${m.id}`).toBe('context_caching')
    }
  })

  test('Gemini models use gemini_response_schema structured output', () => {
    const gemini = MODELS.filter(m => m.provider === 'google')
    for (const m of gemini) {
      expect(m.quirks.structured_output_format, `model ${m.id}`).toBe('gemini_response_schema')
    }
  })

  test('request_transforms when present is an object', () => {
    const withTransforms = MODELS.filter(m => m.quirks.request_transforms !== undefined)
    expect(withTransforms.length).toBeGreaterThan(0)
    for (const m of withTransforms) {
      expect(typeof m.quirks.request_transforms).toBe('object')
      expect(m.quirks.request_transforms).not.toBeNull()
    }
  })
})
