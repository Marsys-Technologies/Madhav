// PARIPRASHNA-P3-PREFLIGHT Part A — adapter parameter-surface audit.
//
// Unlike adapter_gemini.test.ts (which mocks 'ai' + '@ai-sdk/google' and
// asserts on the options object passed INTO streamText), this file mocks
// NEITHER: it stubs global.fetch and lets the real @ai-sdk/google package
// build the actual outbound HTTP request body. That is the only place a
// parameter can be proven to have reached the wire rather than merely been
// passed to an SDK call that silently drops it — the exact class of defect
// DD-20 found once already (a markdown-fenced response proved
// responseSchema wasn't reaching generationConfig despite the adapter's own
// comment claiming it would).
//
// No live model call is made or needed: fetch is stubbed and never touches
// the network.

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('server-only', () => ({}))

import { adapterGemini } from '../../providers/adapter_gemini'
import type { QueryRequest } from '../../types'
import type { ModelMeta } from '@/lib/models/registry'

async function collectEvents(stream: ReadableStream) {
  const reader = stream.getReader()
  const events: unknown[] = []
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    events.push(value)
  }
  return events
}

function makeMeta(overrides: Partial<ModelMeta> = {}): ModelMeta {
  return {
    id: 'gemini-2.5-pro',
    label: 'Gemini 2.5 Pro',
    hint: '',
    provider: 'google',
    tier: 'premium',
    speedTier: 'deep',
    maxOutputTokens: 65536,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 1.25,
    costPer1MOutput: 10.0,
    reasoningMode: 'native',
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      request_transforms: { safety_filter: 'block_none', thinking_budget: 32768 },
    },
    ...overrides,
  } as ModelMeta
}

function makeReq(overrides: Partial<QueryRequest> = {}): QueryRequest {
  return {
    callType: 'synthesis',
    systemPrompt: 'sys',
    messages: [{ role: 'user', content: 'hi' }],
    ...overrides,
  } as QueryRequest
}

// A minimal, well-formed but EMPTY Gemini streamGenerateContent SSE body.
// We only care about the outbound request; the adapter is error-tolerant
// of an empty/malformed response (emits an 'error' event rather than
// throwing), so an empty stream is sufficient and never needs real content.
function emptySseResponse(): Response {
  return new Response('', {
    status: 200,
    headers: { 'content-type': 'text/event-stream' },
  })
}

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  process.env.GOOGLE_GENERATIVE_AI_API_KEY = 'test-key-not-real-never-sent-over-network'
  fetchMock = vi.fn().mockResolvedValue(emptySseResponse())
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  delete process.env.GOOGLE_GENERATIVE_AI_API_KEY
})

async function captureWireBody(req: QueryRequest, meta: ModelMeta): Promise<Record<string, unknown>> {
  await collectEvents(adapterGemini.stream(req, meta))
  expect(fetchMock).toHaveBeenCalled()
  const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
  expect(typeof init.body).toBe('string')
  return JSON.parse(init.body as string) as Record<string, unknown>
}

describe('adapterGemini — real wire body (fetch-boundary, no ai/@ai-sdk/google mocks)', () => {
  test('responseSchema reaches generationConfig.responseSchema on the real request (DD-20 wiring re-check — was RED, now fixed)', async () => {
    // ROOT CAUSE this test caught (confirmed by reading the pinned SDK source, not
    // assumed): adapter_gemini.ts USED TO set a top-level `responseFormat: { type:
    // 'json', schema }` field on the object passed to streamText(). In the pinned
    // `ai@6.0.197`, streamText()'s own destructured parameter list (dist/index.mjs
    // ~L6488-6527) has NO `responseFormat` field at all — structured output in this
    // SDK version is driven exclusively by `output`/`experimental_output`. The
    // unrecognized `responseFormat` key fell into the `...settings` rest spread,
    // which `prepareCallSettings()` narrows to a fixed allowlist (maxOutputTokens,
    // temperature, topP, topK, presencePenalty, frequencyPenalty, stopSequences,
    // seed — dist/index.mjs ~L7063-7070) that does not include it. The actual
    // `responseFormat` handed to the provider's doStream() comes from
    // `output?.responseFormat` (dist/index.mjs ~L7331) — since `output` was never
    // set, this resolved to `undefined`. Schema-constrained generation was NOT
    // happening; every call was silently relying on DD-20's repair-retry path.
    //
    // Fixed by switching the adapter to `Output.object({ schema: jsonSchema(...) })`
    // passed as `output`, the SDK's real structured-output mechanism.
    const schema = {
      type: 'object',
      properties: { verdict: { type: 'string' } },
      required: ['verdict'],
    }
    const body = await captureWireBody(
      makeReq({ responseSchema: schema as unknown as QueryRequest['responseSchema'] }),
      makeMeta(),
    )
    const generationConfig = body.generationConfig as Record<string, unknown> | undefined
    expect(generationConfig?.responseMimeType).toBe('application/json')
    expect(generationConfig?.responseSchema).toBeDefined()
    expect(JSON.stringify(generationConfig?.responseSchema)).toContain('verdict')
  })

  test('thinking_level from registry quirks reaches generationConfig.thinkingConfig.thinkingLevel (was RED — adapter never read it — now fixed)', async () => {
    // Mirrors the real gemini-3.1-pro-preview / gemini-3.7-flash catalog entries
    // (registry.ts ~L305/~L331): request_transforms carries thinking_level, NOT
    // thinking_budget. The adapter's prepareRequest USED TO only read
    // `request_transforms.thinking_budget` — thinking_level was never read, so a
    // 3.x model would silently fall back to the hardcoded 24576-token thinkingBudget
    // default instead of the intended thinking_level. Fixed: prepareRequest now
    // branches on which field the model's quirks declare.
    const meta = makeMeta({
      id: 'gemini-3.1-pro-preview',
      quirks: {
        reasoning_via: 'native',
        streaming_required: false,
        tool_use_format: 'gemini',
        structured_output_format: 'gemini_response_schema',
        cache_strategy: 'context_caching',
        system_prompt_shape: 'system_message',
        request_transforms: { safety_filter: 'block_none', thinking_level: 'high' },
      },
    })
    const body = await captureWireBody(makeReq(), meta)
    const thinkingConfig = (body.generationConfig as Record<string, unknown> | undefined)
      ?.thinkingConfig as Record<string, unknown> | undefined

    expect(thinkingConfig?.thinkingLevel).toBe('high')
  })

  test('thinking_level model with reasoning=disable sends thinkingLevel=low, not thinkingBudget=0 or minimal', async () => {
    // Gemini 3.x has no documented "disabled" thinking_level (docs enumerate only
    // minimal/low/medium/high), and the two fields are not interchangeable on the
    // wire. 'low', NOT 'minimal': confirmed live against the real API
    // (dd20_e2e_verify.ts re-run, PARIPRASHNA-P3-PREFLIGHT Part B) that
    // gemini-3.1-pro-preview rejects thinkingLevel='minimal' with HTTP 400
    // ("Thinking level MINIMAL is not supported for this model").
    const meta = makeMeta({
      id: 'gemini-3.1-pro-preview',
      quirks: {
        reasoning_via: 'native',
        streaming_required: false,
        tool_use_format: 'gemini',
        structured_output_format: 'gemini_response_schema',
        cache_strategy: 'context_caching',
        system_prompt_shape: 'system_message',
        request_transforms: { safety_filter: 'block_none', thinking_level: 'high' },
      },
    })
    const body = await captureWireBody(makeReq({ reasoning: 'disable' }), meta)
    const thinkingConfig = (body.generationConfig as Record<string, unknown> | undefined)
      ?.thinkingConfig as Record<string, unknown> | undefined
    expect(thinkingConfig?.thinkingLevel).toBe('low')
    expect(thinkingConfig?.thinkingBudget).toBeUndefined()
  })

  test('thinking_budget model (gemini-2.5-pro) is unaffected — regression guard', async () => {
    const body = await captureWireBody(makeReq(), makeMeta())
    const thinkingConfig = (body.generationConfig as Record<string, unknown> | undefined)
      ?.thinkingConfig as Record<string, unknown> | undefined
    expect(thinkingConfig?.thinkingBudget).toBe(32768)
    expect(thinkingConfig?.thinkingLevel).toBeUndefined()
  })

  test('SDK itself DOES support thinkingConfig.thinkingLevel — this is an adapter gap, not an SDK limitation', async () => {
    // Proves the fix is a same-shape adapter change, not a scoping problem: passing
    // thinkingLevel directly via providerOptions.google.thinkingConfig (bypassing the
    // adapter's own quirks-reading code) IS accepted and forwarded verbatim by the
    // pinned @ai-sdk/google@3.0.80 (google-generative-ai-options.ts's own zod schema
    // includes thinkingLevel alongside thinkingBudget/includeThoughts).
    fetchMock.mockResolvedValue(emptySseResponse())
    const { streamText } = await import('ai')
    const { google } = await import('@ai-sdk/google')
    await collectEvents(
      new ReadableStream({
        async start(controller) {
          const result = streamText({
            model: google('gemini-3.1-pro-preview'),
            system: 'sys',
            messages: [{ role: 'user', content: 'hi' }],
            providerOptions: { google: { thinkingConfig: { thinkingLevel: 'high' } } },
          } as Parameters<typeof streamText>[0])
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          for await (const _part of result.fullStream) {
            // draining is enough to force the request; content is irrelevant
          }
          controller.close()
        },
      }),
    )
    const [, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit]
    const body = JSON.parse(init.body as string) as Record<string, unknown>
    const thinkingConfig = (body.generationConfig as Record<string, unknown> | undefined)
      ?.thinkingConfig as Record<string, unknown> | undefined
    expect(thinkingConfig?.thinkingLevel).toBe('high')
  })

  test('temperature, maxOutputTokens, safetySettings all reach the real request body', async () => {
    const body = await captureWireBody(
      makeReq({ temperature: 0.4, maxOutputTokens: 1234 }),
      makeMeta(),
    )
    const generationConfig = body.generationConfig as Record<string, unknown> | undefined
    expect(generationConfig?.temperature).toBe(0.4)
    expect(generationConfig?.maxOutputTokens).toBe(1234)
    const safetySettings = body.safetySettings as Array<{ threshold: string }> | undefined
    expect(safetySettings?.length).toBe(5)
    expect(safetySettings?.every(s => s.threshold === 'BLOCK_NONE')).toBe(true)
  })
})
