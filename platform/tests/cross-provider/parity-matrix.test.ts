/**
 * parity-matrix.test.ts — R11F-C-S1 Cross-provider tool-selection parity matrix.
 *
 * Verifies that ALL five providers, when given the same planner-authorised
 * tool catalogue (query_dasha_periods + msr_sql), correctly forward those
 * tools in their underlying SDK call.
 *
 * Strategy:
 *   - Anthropic / Google → vi.mock('ai') to intercept streamText()
 *   - OpenAI / DeepSeek / NVIDIA → vi.hoisted() + vi.mock('openai') to
 *     intercept client.chat.completions.create()
 *
 * All tests run without real API keys; only the mock call-arguments are
 * inspected.
 *
 * A divergence-report test documents any legitimate per-provider asymmetries
 * (always passes; purely documentary).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ------------------------------------------------------------------
// Canonical tool catalogue under test
// ------------------------------------------------------------------

const CANONICAL_TOOLS = [
  {
    name: 'query_dasha_periods',
    description: 'Query dasha periods for a given planet/dasha lord',
    inputSchema: {
      type: 'object' as const,
      properties: {
        dasha_lord: { type: 'string', description: 'Graha name (Saturn, Jupiter, etc.)' },
        limit: { type: 'number', description: 'Max periods to return' },
      },
      required: ['dasha_lord'],
    },
  },
  {
    name: 'msr_sql',
    description: 'Query MSR signals from the Master Signal Register',
    inputSchema: {
      type: 'object' as const,
      properties: {
        filter: { type: 'string', description: 'SQL WHERE clause fragment' },
        limit: { type: 'number', description: 'Max signals to return' },
      },
    },
  },
]

// ------------------------------------------------------------------
// Shared OpenAI-compat stream fixture (OpenAI / DeepSeek / NVIDIA)
// ------------------------------------------------------------------

async function* plainStopStream() {
  yield {
    choices: [{ delta: { content: 'Dasha analysis complete.' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: {}, finish_reason: 'stop' }],
    usage: { prompt_tokens: 50, completion_tokens: 10, prompt_tokens_details: { cached_tokens: 0 } },
  }
}

// ------------------------------------------------------------------
// Helper: collect all events from an AsyncIterable
// ------------------------------------------------------------------

async function collectEvents<T>(iterable: AsyncIterable<T>): Promise<T[]> {
  const result: T[] = []
  for await (const event of iterable) {
    result.push(event)
  }
  return result
}

// ===================================================================
// SECTION 1 — Anthropic adapter (uses Vercel AI SDK streamText)
// ===================================================================

// Mock 'ai' before importing the adapter
vi.mock('ai', () => ({
  streamText: vi.fn(),
  jsonSchema: vi.fn((schema: unknown) => schema),
}))

vi.mock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn((modelId: string) => ({ modelId })),
}))

vi.mock('@ai-sdk/google', () => ({
  google: vi.fn((modelId: string) => ({ modelId })),
}))

vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn(),
  RETRIEVAL_TOOLS: [],
}))

vi.mock('server-only', () => ({}))

// vi.hoisted: declare mockCreate before vi.mock('openai') for OpenAI/DeepSeek/NVIDIA
const { mockCreate } = vi.hoisted(() => ({ mockCreate: vi.fn() }))

vi.mock('openai', () => {
  function MockOpenAI() {
    return { chat: { completions: { create: mockCreate } } }
  }
  return { default: MockOpenAI }
})

import { streamText } from 'ai'
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter'
import { GoogleAdapter } from '../../src/lib/providers/google/adapter'
import { OpenAIAdapter } from '../../src/lib/providers/openai/adapter'
import { DeepSeekAdapter } from '../../src/lib/providers/deepseek/adapter'
import { NVIDIAAdapter } from '../../src/lib/providers/nvidia/adapter'
import type { ChatRequest } from '../../src/lib/providers/types'

// Shared base request (same for all providers; model field set per-provider)
function makeRequest(model: string): ChatRequest {
  return {
    model,
    messages: [{ role: 'user', content: 'When does my next Saturn mahadasha begin?' }],
    tools: CANONICAL_TOOLS,
  }
}

// Minimal Anthropic/Google fullStream that emits only a text-delta + finish
async function* vercelStopStream() {
  yield { type: 'text-delta', textDelta: 'Analysis done.' }
  yield { type: 'finish', finishReason: 'stop', usage: { inputTokens: 50, outputTokens: 10 } }
}

// ===================================================================
// ANTHROPIC — streamText tools ToolSet shape
// ===================================================================

describe('parity-matrix: Anthropic adapter forwards canonical tools to streamText', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(streamText).mockImplementation(() => ({
      fullStream: vercelStopStream(),
    } as unknown as ReturnType<typeof streamText>))
  })

  it('PM-A.1: streamText is called with both canonical tools', async () => {
    const adapter = new AnthropicAdapter()
    await collectEvents(adapter.chat(makeRequest('claude-sonnet-4-6')))

    expect(streamText).toHaveBeenCalledTimes(1)
    const params = vi.mocked(streamText).mock.calls[0][0]
    expect(params).toHaveProperty('tools')

    // Anthropic uses ToolSet (object keyed by name)
    const tools = params.tools as Record<string, { inputSchema?: unknown; parameters?: unknown }>
    expect(Object.keys(tools)).toContain('query_dasha_periods')
    expect(Object.keys(tools)).toContain('msr_sql')
  })

  it('PM-A.2: each tool has inputSchema with type:object (normalizeInputSchema applied)', async () => {
    const adapter = new AnthropicAdapter()
    await collectEvents(adapter.chat(makeRequest('claude-sonnet-4-6')))

    const params = vi.mocked(streamText).mock.calls[0][0]
    const tools = params.tools as Record<string, { inputSchema?: { type?: string } }>

    for (const [toolName, def] of Object.entries(tools)) {
      expect(def, `Tool ${toolName} must have inputSchema`).toHaveProperty('inputSchema')
      expect((def.inputSchema as { type?: string }).type, `Tool ${toolName} inputSchema.type must be 'object'`).toBe('object')
    }
  })

  it('PM-A.3: no tools forwarded when request.tools is empty', async () => {
    const adapter = new AnthropicAdapter()
    const emptyReq: ChatRequest = { ...makeRequest('claude-sonnet-4-6'), tools: [] }
    await collectEvents(adapter.chat(emptyReq))

    const params = vi.mocked(streamText).mock.calls[0][0]
    // Empty tools array → no tools param (or empty tools object)
    const tools = params.tools as Record<string, unknown> | undefined
    const toolCount = tools ? Object.keys(tools).length : 0
    expect(toolCount).toBe(0)
  })
})

// ===================================================================
// GOOGLE — streamText tools ToolSet shape
// ===================================================================

describe('parity-matrix: Google adapter forwards canonical tools to streamText', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(streamText).mockImplementation(() => ({
      fullStream: vercelStopStream(),
    } as unknown as ReturnType<typeof streamText>))
  })

  it('PM-G.1: streamText is called with both canonical tools', async () => {
    const adapter = new GoogleAdapter()
    await collectEvents(adapter.chat(makeRequest('gemini-2.5-pro')))

    expect(streamText).toHaveBeenCalledTimes(1)
    const params = vi.mocked(streamText).mock.calls[0][0]
    expect(params).toHaveProperty('tools')

    // Google uses ToolSet (object keyed by name)
    const tools = params.tools as Record<string, unknown>
    expect(Object.keys(tools)).toContain('query_dasha_periods')
    expect(Object.keys(tools)).toContain('msr_sql')
  })

  it('PM-G.2: both tools present in tools param', async () => {
    const adapter = new GoogleAdapter()
    await collectEvents(adapter.chat(makeRequest('gemini-2.5-pro')))

    const params = vi.mocked(streamText).mock.calls[0][0]
    const tools = params.tools as Record<string, unknown>
    expect(Object.keys(tools)).toHaveLength(2)
  })
})

// ===================================================================
// OPENAI — client.chat.completions.create() OpenAI function format
// ===================================================================

describe('parity-matrix: OpenAI adapter forwards canonical tools to OpenAI API', () => {
  beforeEach(() => {
    mockCreate.mockReset()
    mockCreate.mockImplementation(plainStopStream)
  })

  it('PM-O.1: create() is called with both canonical tools in function format', async () => {
    const adapter = new OpenAIAdapter()
    await collectEvents(adapter.chat(makeRequest('gpt-4.1')))

    expect(mockCreate).toHaveBeenCalledTimes(1)
    const params = mockCreate.mock.calls[0][0]
    expect(params.tools).toBeDefined()
    expect(params.tools).toHaveLength(2)

    const toolNames = params.tools.map((t: { function: { name: string } }) => t.function.name)
    expect(toolNames).toContain('query_dasha_periods')
    expect(toolNames).toContain('msr_sql')
  })

  it('PM-O.2: tools are in OpenAI function call format (type:function + parameters)', async () => {
    const adapter = new OpenAIAdapter()
    await collectEvents(adapter.chat(makeRequest('gpt-4.1')))

    const params = mockCreate.mock.calls[0][0]
    for (const tool of params.tools) {
      expect(tool.type).toBe('function')
      expect(tool.function).toBeDefined()
      expect(tool.function.name).toBeDefined()
      expect(tool.function.parameters).toBeDefined()
      expect(tool.function.parameters.type).toBe('object')
    }
  })

  it('PM-O.3: no tools forwarded when request.tools is empty', async () => {
    const adapter = new OpenAIAdapter()
    const emptyReq: ChatRequest = { ...makeRequest('gpt-4.1'), tools: [] }
    await collectEvents(adapter.chat(emptyReq))

    const params = mockCreate.mock.calls[0][0]
    expect(params.tools).toBeUndefined()
  })
})

// ===================================================================
// DEEPSEEK — client.chat.completions.create() OpenAI-compat format
// ===================================================================

describe('parity-matrix: DeepSeek adapter forwards canonical tools to DeepSeek API', () => {
  beforeEach(() => {
    mockCreate.mockReset()
    mockCreate.mockImplementation(plainStopStream)
  })

  it('PM-D.1: create() is called with both canonical tools in OpenAI-compat format', async () => {
    const adapter = new DeepSeekAdapter()
    await collectEvents(adapter.chat(makeRequest('deepseek-chat')))

    expect(mockCreate).toHaveBeenCalledTimes(1)
    const params = mockCreate.mock.calls[0][0]
    expect(params.tools).toBeDefined()
    expect(params.tools).toHaveLength(2)

    const toolNames = params.tools.map((t: { function: { name: string } }) => t.function.name)
    expect(toolNames).toContain('query_dasha_periods')
    expect(toolNames).toContain('msr_sql')
  })

  it('PM-D.2: tools are in OpenAI-compat function format (type:function + parameters)', async () => {
    const adapter = new DeepSeekAdapter()
    await collectEvents(adapter.chat(makeRequest('deepseek-chat')))

    const params = mockCreate.mock.calls[0][0]
    for (const tool of params.tools) {
      expect(tool.type).toBe('function')
      expect(tool.function).toBeDefined()
      expect(tool.function.name).toBeDefined()
      expect(tool.function.parameters).toBeDefined()
      expect(tool.function.parameters.type).toBe('object')
    }
  })

  it('PM-D.3: no tools forwarded when request.tools is empty', async () => {
    const adapter = new DeepSeekAdapter()
    const emptyReq: ChatRequest = { ...makeRequest('deepseek-chat'), tools: [] }
    await collectEvents(adapter.chat(emptyReq))

    const params = mockCreate.mock.calls[0][0]
    expect(params.tools).toBeUndefined()
  })
})

// ===================================================================
// NVIDIA NIM — client.chat.completions.create() OpenAI-compat format
// ===================================================================

describe('parity-matrix: NVIDIA adapter forwards canonical tools to NIM API', () => {
  beforeEach(() => {
    mockCreate.mockReset()
    mockCreate.mockImplementation(plainStopStream)
  })

  it('PM-N.1: create() is called with both canonical tools in OpenAI-compat format', async () => {
    const adapter = new NVIDIAAdapter()
    await collectEvents(adapter.chat(makeRequest('meta/llama-3.1-70b-instruct')))

    expect(mockCreate).toHaveBeenCalledTimes(1)
    const params = mockCreate.mock.calls[0][0]
    expect(params.tools).toBeDefined()
    expect(params.tools).toHaveLength(2)

    const toolNames = params.tools.map((t: { function: { name: string } }) => t.function.name)
    expect(toolNames).toContain('query_dasha_periods')
    expect(toolNames).toContain('msr_sql')
  })

  it('PM-N.2: tools are in OpenAI-compat function format (type:function + parameters)', async () => {
    const adapter = new NVIDIAAdapter()
    await collectEvents(adapter.chat(makeRequest('meta/llama-3.1-70b-instruct')))

    const params = mockCreate.mock.calls[0][0]
    for (const tool of params.tools) {
      expect(tool.type).toBe('function')
      expect(tool.function).toBeDefined()
      expect(tool.function.name).toBeDefined()
      expect(tool.function.parameters).toBeDefined()
      expect(tool.function.parameters.type).toBe('object')
    }
  })

  it('PM-N.3: no tools forwarded when request.tools is empty', async () => {
    const adapter = new NVIDIAAdapter()
    const emptyReq: ChatRequest = { ...makeRequest('meta/llama-3.1-70b-instruct'), tools: [] }
    await collectEvents(adapter.chat(emptyReq))

    const params = mockCreate.mock.calls[0][0]
    expect(params.tools).toBeUndefined()
  })
})

// ===================================================================
// DIVERGENCE REPORT — always-pass documentary test
// ===================================================================

describe('parity-matrix: Divergence report — documented per-provider asymmetries', () => {
  it('PM-DIV.1: documents the two tool serialization families (always passes)', () => {
    /**
     * Provider → SDK call → tool format
     * ─────────────────────────────────────────────────────────────────────────
     * anthropic  │ streamText (Vercel AI SDK)      │ ToolSet keyed by name;
     *            │                                 │ each entry has inputSchema
     *            │                                 │ (via jsonSchema()); type
     *            │                                 │ field is 'object' after
     *            │                                 │ normalizeInputSchema().
     *
     * google     │ streamText (Vercel AI SDK)      │ ToolSet keyed by name;
     *            │                                 │ same shape as Anthropic.
     *            │                                 │ No inputSchema→parameters
     *            │                                 │ normalization needed; SDK
     *            │                                 │ handles Gemini translation.
     *
     * openai     │ OpenAI SDK chat.completions     │ Array of {type:'function',
     *            │                                 │ function:{name, description,
     *            │                                 │ parameters: JSONSchema}}.
     *            │                                 │ parameters is raw JSON
     *            │                                 │ Schema (no jsonSchema()
     *            │                                 │ wrapper).
     *
     * deepseek   │ OpenAI SDK (compatible endpoint)│ Identical to OpenAI format.
     *            │                                 │ hasReasoningMiddleware=true
     *            │                                 │ for <think> block handling.
     *
     * nvidia     │ OpenAI SDK (NIM endpoint)       │ Identical to OpenAI format.
     *            │                                 │ Model-dependent: only
     *            │                                 │ llama-3.1-70b-instruct+
     *            │                                 │ support tool_calls (Case A).
     * ─────────────────────────────────────────────────────────────────────────
     *
     * Asymmetry #1: Anthropic + Google use ToolSet (object) while
     *               OpenAI / DeepSeek / NVIDIA use array of function objects.
     *
     * Asymmetry #2: Anthropic normalizes via normalizeInputSchema() at the
     *               tool_catalogue boundary; OpenAI/DeepSeek/NVIDIA pass the
     *               inputSchema directly as 'parameters'.
     *
     * Asymmetry #3: DeepSeek hasReasoningMiddleware=true (unique to DeepSeek R1)
     *               while all other providers have hasReasoningMiddleware=false.
     *
     * No provider should silently drop tools when request.tools is non-empty.
     * All five providers: empty tools → no tools param (OpenAI family) or
     *                     empty ToolSet (Vercel family).
     */
    expect(true).toBe(true) // Always passes — purely documentary
  })
})
