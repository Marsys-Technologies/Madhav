// OpenAI provider observed adapter — wraps an OpenAI-shaped client (Chat
// Completions + Responses APIs) and emits one llm_usage_events row per call
// via the S1.2 observability shim. Token, request-id, and error mapping per
// OBSERVATORY_PLAN_v1_0.md §4.2 (OpenAI provider matrix).
//
// Contract (per USTAD_S1_5 brief):
//   - Token extraction normalizes both Chat Completions and Responses API
//     usage shapes into the shim's TokenUsage (5 fields).
//   - Streaming calls ALWAYS receive `stream_options.include_usage: true` —
//     the adapter injects this regardless of caller intent.
//   - provider_request_id is sourced from the OpenAI response's `_request_id`
//     (Node SDK convention) or response headers' x-request-id.
//   - Error mapping: 400/401/403/404 → error_code from response body
//     `.error.code`; 429 → `rate_limited`; 5xx → `server_error`; timeout →
//     status='timeout' (the only path that produces non-error non-success).

import {
  computeCost,
  persistObservation,
  ZERO_USAGE,
  type CallStatus,
  type ObservatoryDb,
  type ObservedLLMRequest,
  type ObservedLLMResponse,
  type PersistedObservation,
  type PipelineStage,
  type TokenUsage,
} from '@/lib/llm/observability'

type AnyRecord = Record<string, unknown>

export interface OpenAIChatCompletionsCreate {
  (params: AnyRecord): Promise<unknown>
}

export interface OpenAIResponsesCreate {
  (params: AnyRecord): Promise<unknown>
}

export interface OpenAIShapedClient {
  chat: { completions: { create: OpenAIChatCompletionsCreate } }
  responses: { create: OpenAIResponsesCreate }
}

export interface ObservationContext {
  conversation_id: string
  conversation_name: string | null
  prompt_id: string
  parent_prompt_id?: string
  user_id: string
  pipeline_stage: PipelineStage
}

interface OpenAIErrorShape {
  status?: number
  code?: string
  name?: string
  message?: string
  error?: { code?: string; message?: string; type?: string }
  headers?: { get?: (k: string) => string | null } | Record<string, string>
  response?: { headers?: { get?: (k: string) => string | null } }
}

function getHeader(
  headers: unknown,
  key: string,
): string | undefined {
  if (!headers) return undefined
  const lk = key.toLowerCase()
  if (typeof (headers as { get?: unknown }).get === 'function') {
    const got = (headers as { get: (k: string) => string | null }).get(key)
    return got ?? undefined
  }
  if (typeof headers === 'object') {
    for (const [k, v] of Object.entries(headers as Record<string, unknown>)) {
      if (k.toLowerCase() === lk && typeof v === 'string') return v
    }
  }
  return undefined
}

export function extractRequestId(response: unknown): string | undefined {
  if (!response || typeof response !== 'object') return undefined
  const r = response as AnyRecord
  if (typeof r._request_id === 'string') return r._request_id
  const headerHit =
    getHeader(r.headers, 'x-request-id') ??
    getHeader((r.response as AnyRecord | undefined)?.headers, 'x-request-id')
  return headerHit
}

function readNumber(obj: unknown, key: string): number {
  if (obj && typeof obj === 'object') {
    const v = (obj as AnyRecord)[key]
    if (typeof v === 'number' && Number.isFinite(v)) return v
  }
  return 0
}

function readSubField(obj: unknown, parent: string, child: string): number {
  if (obj && typeof obj === 'object') {
    const sub = (obj as AnyRecord)[parent]
    if (sub && typeof sub === 'object') {
      const v = (sub as AnyRecord)[child]
      if (typeof v === 'number' && Number.isFinite(v)) return v
    }
  }
  return 0
}

// Normalizes both Chat Completions and Responses API usage shapes.
// Chat: {prompt_tokens, completion_tokens, prompt_tokens_details.cached_tokens,
//        completion_tokens_details.reasoning_tokens}
// Responses: {input_tokens, output_tokens, input_tokens_details.cached_tokens,
//             output_tokens_details.reasoning_tokens}
export function extractUsage(usage: unknown): TokenUsage {
  if (!usage || typeof usage !== 'object') return { ...ZERO_USAGE }

  const promptTokens = readNumber(usage, 'prompt_tokens')
  const completionTokens = readNumber(usage, 'completion_tokens')
  const inputTokens = readNumber(usage, 'input_tokens')
  const outputTokens = readNumber(usage, 'output_tokens')

  const cachedFromChat = readSubField(usage, 'prompt_tokens_details', 'cached_tokens')
  const cachedFromResponses = readSubField(usage, 'input_tokens_details', 'cached_tokens')

  const reasoningFromChat = readSubField(
    usage,
    'completion_tokens_details',
    'reasoning_tokens',
  )
  const reasoningFromResponses = readSubField(
    usage,
    'output_tokens_details',
    'reasoning_tokens',
  )

  return {
    input_tokens: promptTokens > 0 ? promptTokens : inputTokens,
    output_tokens: completionTokens > 0 ? completionTokens : outputTokens,
    cache_read_tokens:
      cachedFromChat > 0 ? cachedFromChat : cachedFromResponses,
    cache_write_tokens: 0, // OpenAI does not currently expose cache-write
    reasoning_tokens:
      reasoningFromChat > 0 ? reasoningFromChat : reasoningFromResponses,
  }
}

function isTimeout(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false
  const e = err as OpenAIErrorShape
  if (e.name === 'APIConnectionTimeoutError') return true
  if (e.name === 'AbortError') return true
  if (typeof e.code === 'string') {
    if (e.code === 'ETIMEDOUT' || e.code === 'ECONNABORTED') return true
  }
  if (typeof e.message === 'string' && /timed?\s*out/i.test(e.message)) return true
  return false
}

export function mapErrorCode(err: unknown): {
  status: CallStatus
  error_code: string
} {
  if (isTimeout(err)) return { status: 'timeout', error_code: 'timeout' }

  if (err && typeof err === 'object') {
    const e = err as OpenAIErrorShape
    const httpStatus = e.status

    if (httpStatus === 429) return { status: 'error', error_code: 'rate_limited' }
    if (typeof httpStatus === 'number' && httpStatus >= 500 && httpStatus <= 599) {
      return { status: 'error', error_code: 'server_error' }
    }
    if (
      httpStatus === 400 ||
      httpStatus === 401 ||
      httpStatus === 403 ||
      httpStatus === 404
    ) {
      const bodyCode = e.error?.code
      if (typeof bodyCode === 'string' && bodyCode.length > 0) {
        return { status: 'error', error_code: bodyCode }
      }
    }
    if (typeof e.code === 'string' && e.code.length > 0) {
      return { status: 'error', error_code: e.code }
    }
    if (typeof e.name === 'string' && e.name.length > 0) {
      return { status: 'error', error_code: e.name }
    }
  }
  return { status: 'error', error_code: 'unknown_error' }
}

function buildRequest(
  ctx: ObservationContext,
  model: string,
  params: AnyRecord,
  promptText: string | null,
  systemPrompt: string | null,
): ObservedLLMRequest {
  return {
    provider: 'openai',
    model,
    prompt_text: promptText,
    system_prompt: systemPrompt,
    parameters: params,
    conversation_id: ctx.conversation_id,
    conversation_name: ctx.conversation_name,
    prompt_id: ctx.prompt_id,
    parent_prompt_id: ctx.parent_prompt_id,
    user_id: ctx.user_id,
    pipeline_stage: ctx.pipeline_stage,
  }
}

interface ChatMessage {
  role?: string
  content?: unknown
}

function summarizePrompt(messages: unknown): {
  promptText: string | null
  systemPrompt: string | null
} {
  if (!Array.isArray(messages)) {
    return { promptText: null, systemPrompt: null }
  }
  const msgs = messages as ChatMessage[]
  let systemPrompt: string | null = null
  let lastUser: string | null = null
  for (const m of msgs) {
    if (typeof m?.content !== 'string') continue
    if (m.role === 'system' && systemPrompt === null) systemPrompt = m.content
    if (m.role === 'user') lastUser = m.content
  }
  return { promptText: lastUser, systemPrompt }
}

function summarizeResponsesInput(input: unknown): {
  promptText: string | null
  systemPrompt: string | null
} {
  if (typeof input === 'string') {
    return { promptText: input, systemPrompt: null }
  }
  if (Array.isArray(input)) return summarizePrompt(input)
  return { promptText: null, systemPrompt: null }
}

function extractChatResponseText(response: unknown): string | null {
  if (!response || typeof response !== 'object') return null
  const choices = (response as AnyRecord).choices
  if (!Array.isArray(choices) || choices.length === 0) return null
  const first = choices[0] as AnyRecord
  const message = first?.message as AnyRecord | undefined
  if (typeof message?.content === 'string') return message.content
  return null
}

function extractResponsesText(response: unknown): string | null {
  if (!response || typeof response !== 'object') return null
  const r = response as AnyRecord
  if (typeof r.output_text === 'string') return r.output_text
  return null
}

async function safeComputeCost(
  request: ObservedLLMRequest,
  observed: ObservedLLMResponse,
  db: ObservatoryDb,
) {
  try {
    return await computeCost(
      request.provider,
      request.model,
      observed.usage,
      observed.started_at,
      db,
    )
  } catch (err) {

    console.error('[openai_observed] computeCost failed:', err)
    return null
  }
}

async function safePersist(
  request: ObservedLLMRequest,
  observed: ObservedLLMResponse,
  db: ObservatoryDb,
): Promise<PersistedObservation | null> {
  try {
    const cost = await safeComputeCost(request, observed, db)
    return await persistObservation(request, observed, cost, db)
  } catch (err) {

    console.error('[openai_observed] persistObservation failed:', err)
    return null
  }
}

// Wraps a non-streaming provider call. observe()-shaped, but with explicit
// timeout discrimination (the shim's observe() always labels thrown errors as
// status='error'; OpenAI requires status='timeout' for connection timeouts).
async function wrapNonStreamCall<T>(
  request: ObservedLLMRequest,
  call: () => Promise<T>,
  responseText: (r: T) => string | null,
  db: ObservatoryDb,
): Promise<T> {
  const startedAt = new Date()
  try {
    const response = await call()
    const finishedAt = new Date()
    const r = response as AnyRecord
    const usage = extractUsage(r?.usage)
    const observed: ObservedLLMResponse = {
      response_text: responseText(response),
      usage,
      provider_request_id: extractRequestId(response),
      status: 'success',
      started_at: startedAt,
      finished_at: finishedAt,
    }
    await safePersist(request, observed, db)
    return response
  } catch (err) {
    const finishedAt = new Date()
    const { status, error_code } = mapErrorCode(err)
    const observed: ObservedLLMResponse = {
      response_text: null,
      usage: { ...ZERO_USAGE },
      provider_request_id: extractRequestId(err),
      status,
      error_code,
      started_at: startedAt,
      finished_at: finishedAt,
    }
    await safePersist(request, observed, db)
    throw err
  }
}

interface AsyncIterableLike<T> {
  [Symbol.asyncIterator](): AsyncIterator<T>
}

function isAsyncIterable<T>(x: unknown): x is AsyncIterableLike<T> {
  return (
    !!x &&
    (typeof x === 'object' || typeof x === 'function') &&
    typeof (x as { [Symbol.asyncIterator]?: unknown })[Symbol.asyncIterator] ===
      'function'
  )
}

// Wraps an async-iterable provider stream. Accumulates usage from the final
// chunk (Chat Completions: chunk.usage when include_usage=true; Responses
// API: event.type === 'response.completed' carries event.response.usage).
async function* wrapStream<TChunk>(
  request: ObservedLLMRequest,
  iterable: AsyncIterableLike<TChunk>,
  db: ObservatoryDb,
): AsyncGenerator<TChunk> {
  const startedAt = new Date()
  let accumulatedUsage: TokenUsage = { ...ZERO_USAGE }
  let providerRequestId: string | undefined
  let streamErr: unknown = null

  // Some OpenAI Stream wrappers expose _request_id on the iterable itself.
  providerRequestId = extractRequestId(iterable)

  try {
    for await (const chunk of iterable) {
      const c = chunk as AnyRecord
      // Chat Completions: usage on final chunk when include_usage=true
      if (c?.usage && typeof c.usage === 'object') {
        accumulatedUsage = extractUsage(c.usage)
      }
      // Responses API: events of type 'response.completed' wrap a response
      if (c?.type === 'response.completed') {
        const ev = c as AnyRecord
        const evResponse = ev.response as AnyRecord | undefined
        if (evResponse?.usage) {
          accumulatedUsage = extractUsage(evResponse.usage)
        }
        const rid = extractRequestId(evResponse)
        if (rid) providerRequestId = rid
      }
      if (!providerRequestId) {
        const rid = extractRequestId(c)
        if (rid) providerRequestId = rid
      }
      yield chunk
    }
  } catch (err) {
    streamErr = err
  } finally {
    const finishedAt = new Date()
    if (streamErr) {
      const { status, error_code } = mapErrorCode(streamErr)
      const observed: ObservedLLMResponse = {
        response_text: null,
        usage: accumulatedUsage,
        provider_request_id: providerRequestId,
        status,
        error_code,
        started_at: startedAt,
        finished_at: finishedAt,
      }
      await safePersist(request, observed, db)
    } else {
      const observed: ObservedLLMResponse = {
        response_text: null,
        usage: accumulatedUsage,
        provider_request_id: providerRequestId,
        status: 'success',
        started_at: startedAt,
        finished_at: finishedAt,
      }
      await safePersist(request, observed, db)
    }
  }

  if (streamErr) throw streamErr
}

// Injects stream_options.include_usage=true on Chat Completions stream calls.
// Never overrides include_usage if the caller already set it; only ensures
// it's set to true so the adapter sees the final usage chunk.
function withChatStreamUsage(params: AnyRecord): AnyRecord {
  if (!params.stream) return params
  const existing = (params.stream_options as AnyRecord | undefined) ?? {}
  return {
    ...params,
    stream_options: { ...existing, include_usage: true },
  }
}

export class ObservedOpenAIClient {
  public readonly chat: {
    completions: {
      create: (params: AnyRecord, ctx: ObservationContext) => Promise<unknown>
    }
  }
  public readonly responses: {
    create: (params: AnyRecord, ctx: ObservationContext) => Promise<unknown>
  }

  constructor(
    private readonly client: OpenAIShapedClient,
    private readonly db: ObservatoryDb,
  ) {
    this.chat = {
      completions: {
        create: (params, ctx) => this.observeChatCompletion(params, ctx),
      },
    }
    this.responses = {
      create: (params, ctx) => this.observeResponse(params, ctx),
    }
  }

  private async observeChatCompletion(
    params: AnyRecord,
    ctx: ObservationContext,
  ): Promise<unknown> {
    const model = typeof params.model === 'string' ? params.model : 'unknown'
    const { promptText, systemPrompt } = summarizePrompt(params.messages)
    const finalParams = withChatStreamUsage(params)
    const request = buildRequest(ctx, model, finalParams, promptText, systemPrompt)

    if (params.stream === true) {
      const result = await this.client.chat.completions.create(finalParams)
      if (!isAsyncIterable(result)) {
        throw new Error(
          '[openai_observed] expected AsyncIterable for stream=true call',
        )
      }
      return wrapStream<unknown>(request, result as AsyncIterableLike<unknown>, this.db)
    }

    return wrapNonStreamCall(
      request,
      () => this.client.chat.completions.create(finalParams),
      extractChatResponseText,
      this.db,
    )
  }

  private async observeResponse(
    params: AnyRecord,
    ctx: ObservationContext,
  ): Promise<unknown> {
    const model = typeof params.model === 'string' ? params.model : 'unknown'
    const { promptText, systemPrompt } = summarizeResponsesInput(params.input)
    const sysFromInstructions =
      typeof params.instructions === 'string' ? params.instructions : null
    const request = buildRequest(
      ctx,
      model,
      params,
      promptText,
      sysFromInstructions ?? systemPrompt,
    )

    if (params.stream === true) {
      const result = await this.client.responses.create(params)
      if (!isAsyncIterable(result)) {
        throw new Error(
          '[openai_observed] expected AsyncIterable for stream=true call',
        )
      }
      return wrapStream<unknown>(request, result as AsyncIterableLike<unknown>, this.db)
    }

    return wrapNonStreamCall(
      request,
      () => this.client.responses.create(params),
      extractResponsesText,
      this.db,
    )
  }
}
