// Observed Anthropic adapter — wraps an Anthropic-shaped client so every
// `messages.create()` call emits one llm_usage_events row (telemetry layer per
// OBSERVATORY_PLAN_v1_0.md §2.1 + §3.1). The adapter exposes the same surface
// as the underlying client: call sites can substitute the wrapper without
// touching the rest of their code.
//
// Authored by USTAD_S1_4_ANTHROPIC_OBSERVED_ADAPTER (Phase O sub-phase O.1)
// per the S1.4 brief and OBSERVATORY_PLAN §4.1 (Anthropic row in the provider
// matrix).
//
// Design notes:
//   • Structural typing — no `@anthropic-ai/sdk` import (the project does not
//     depend on the raw SDK; the AI-SDK wrapper handles routing today). This
//     adapter is the integration surface for any path that adopts the raw
//     Anthropic client without bringing it into a build-time dependency here.
//   • observe() / observeStream() drive persistence on the success path and
//     the HTTP-error path. Timeouts bypass observe() and call
//     persistObservation directly because observe() hardcodes status='error'
//     for thrown errors and the brief requires status='timeout' for the
//     timeout class. Exactly one llm_usage_events row is written per call.
//   • Streaming is pass-through — chunks forward to the consumer immediately;
//     usage is accumulated from the final `message_delta` event.
//   • Per OD.S1.3.1: this adapter does not capture full raw payloads. The
//     `parameters` jsonb column is used (sans messages, to avoid PII bleed
//     into a column not gated by OBSERVATORY_HASH_PROMPTS).

import {
  observe,
  observeStream,
  persistObservation,
  computeCost,
  PricingNotFoundError,
  ZERO_USAGE,
  type CostResult,
  type ObservatoryDb,
  type ObservedLLMRequest,
  type ObservedLLMResponse,
  type PipelineStage,
  type TokenUsage,
} from '@/lib/llm/observability'

// ────────────────────────────────────────────────────────────────────────────
// Anthropic-shaped client surface (structural typing)
// ────────────────────────────────────────────────────────────────────────────

export interface AnthropicUsage {
  input_tokens?: number | null
  output_tokens?: number | null
  cache_creation_input_tokens?: number | null
  cache_read_input_tokens?: number | null
}

export interface AnthropicMessageResponse {
  id?: string
  type?: string
  role?: string
  model?: string
  content?: unknown
  stop_reason?: string | null
  stop_sequence?: string | null
  usage?: AnthropicUsage
  [extra: string]: unknown
}

export type AnthropicStreamEvent =
  | { type: 'message_start'; message?: { id?: string; usage?: AnthropicUsage } }
  | { type: 'content_block_start'; index?: number; content_block?: unknown }
  | { type: 'content_block_delta'; index?: number; delta?: unknown }
  | { type: 'content_block_stop'; index?: number }
  | { type: 'message_delta'; delta?: unknown; usage?: AnthropicUsage }
  | { type: 'message_stop' }
  | { type: 'ping' }
  | { type: string; [extra: string]: unknown }

export interface AnthropicCreateParamsBase {
  model: string
  messages: unknown[]
  max_tokens?: number
  [extra: string]: unknown
}
export interface AnthropicCreateParamsNonStreaming extends AnthropicCreateParamsBase {
  stream?: false
}
export interface AnthropicCreateParamsStreaming extends AnthropicCreateParamsBase {
  stream: true
}
export type AnthropicCreateParams =
  | AnthropicCreateParamsNonStreaming
  | AnthropicCreateParamsStreaming

export type AnthropicCreateResult<P extends AnthropicCreateParams> =
  P extends AnthropicCreateParamsStreaming
    ? AsyncIterable<AnthropicStreamEvent>
    : Promise<AnthropicMessageResponse>

export interface AnthropicCallOptions {
  headers?: Record<string, string>
  timeout?: number
  signal?: AbortSignal
}

export interface AnthropicMessagesAPI {
  create<P extends AnthropicCreateParams>(
    params: P,
    options?: AnthropicCallOptions,
  ): AnthropicCreateResult<P>
}

export interface AnthropicClient {
  messages: AnthropicMessagesAPI
}

// ────────────────────────────────────────────────────────────────────────────
// Per-adapter context
// ────────────────────────────────────────────────────────────────────────────

export interface AnthropicAdapterContext {
  conversation_id: string
  conversation_name?: string | null
  prompt_id: string
  parent_prompt_id?: string
  user_id: string
  pipeline_stage: PipelineStage
  prompt_text?: string | null
  system_prompt?: string | null
}

// ────────────────────────────────────────────────────────────────────────────
// Token / request-id / error extraction
// ────────────────────────────────────────────────────────────────────────────

export function extractAnthropicUsage(
  usage: AnthropicUsage | undefined | null,
): TokenUsage {
  if (!usage) return { ...ZERO_USAGE }
  return {
    input_tokens: usage.input_tokens ?? 0,
    output_tokens: usage.output_tokens ?? 0,
    cache_read_tokens: usage.cache_read_input_tokens ?? 0,
    cache_write_tokens: usage.cache_creation_input_tokens ?? 0,
    reasoning_tokens: 0,
  }
}

type HeaderLike =
  | Record<string, string | string[] | undefined>
  | Headers
  | null
  | undefined

function readHeader(h: HeaderLike, key: string): string | undefined {
  if (!h) return undefined
  if (h instanceof Headers) return h.get(key) ?? undefined
  const lowerKey = key.toLowerCase()
  for (const k of Object.keys(h)) {
    if (k.toLowerCase() === lowerKey) {
      const v = h[k]
      if (Array.isArray(v)) return v[0]
      return typeof v === 'string' ? v : undefined
    }
  }
  return undefined
}

export function extractAnthropicRequestId(
  responseOrStream: unknown,
  optionsHeaders?: Record<string, string>,
): string | undefined {
  if (responseOrStream && typeof responseOrStream === 'object') {
    const r = responseOrStream as {
      _request_id?: unknown
      request_id?: unknown
      headers?: HeaderLike
    }
    if (typeof r._request_id === 'string' && r._request_id.length > 0) {
      return r._request_id
    }
    if (typeof r.request_id === 'string' && r.request_id.length > 0) {
      return r.request_id
    }
    const fromObj =
      readHeader(r.headers, 'request-id') ??
      readHeader(r.headers, 'x-request-id')
    if (fromObj) return fromObj
  }
  if (optionsHeaders) {
    const fromOpts =
      readHeader(optionsHeaders, 'request-id') ??
      readHeader(optionsHeaders, 'x-request-id')
    if (fromOpts) return fromOpts
  }
  return undefined
}

interface MappedError {
  status: 'error' | 'timeout'
  error_code: string
}

export function mapAnthropicError(err: unknown): MappedError {
  if (!(err && typeof err === 'object')) {
    return { status: 'error', error_code: 'unknown_error' }
  }
  const e = err as {
    status?: unknown
    statusCode?: unknown
    code?: unknown
    name?: unknown
    type?: unknown
    error?: { type?: unknown }
    message?: unknown
  }
  const codeLike =
    (typeof e.code === 'string' ? e.code : '') ||
    (typeof e.name === 'string' ? e.name : '')
  const messageLower =
    typeof e.message === 'string' ? e.message.toLowerCase() : ''

  const isTimeout =
    codeLike === 'ETIMEDOUT' ||
    codeLike === 'AbortError' ||
    codeLike === 'TimeoutError' ||
    codeLike === 'timeout' ||
    messageLower.includes('timed out') ||
    messageLower.includes('timeout')
  if (isTimeout) {
    return { status: 'timeout', error_code: 'timeout' }
  }

  const httpStatus =
    typeof e.status === 'number'
      ? e.status
      : typeof e.statusCode === 'number'
        ? e.statusCode
        : undefined

  if (typeof httpStatus === 'number') {
    if (httpStatus === 429) return { status: 'error', error_code: 'rate_limited' }
    if (httpStatus >= 500) return { status: 'error', error_code: 'server_error' }
    if (httpStatus >= 400) {
      const t = e.error?.type
      if (typeof t === 'string' && t.length > 0) {
        return { status: 'error', error_code: t }
      }
      const tt = e.type
      if (typeof tt === 'string' && tt.length > 0) {
        return { status: 'error', error_code: tt }
      }
      return { status: 'error', error_code: `http_${httpStatus}` }
    }
  }
  if (codeLike) return { status: 'error', error_code: codeLike }
  return { status: 'error', error_code: 'unknown_error' }
}

async function safeComputeCost(
  request: ObservedLLMRequest,
  observed: ObservedLLMResponse,
  db: ObservatoryDb,
): Promise<CostResult | null> {
  try {
    return await computeCost(
      request.provider,
      request.model,
      observed.usage,
      observed.started_at,
      db,
    )
  } catch (err) {
    if (err instanceof PricingNotFoundError) return null

    console.error('[anthropic_observed] computeCost failed:', err)
    return null
  }
}

function buildBaseRequest(
  ctx: AnthropicAdapterContext,
  params: AnthropicCreateParams,
): ObservedLLMRequest {
  // Strip `messages` from the parameters jsonb to keep PII gated only by the
  // OBSERVATORY_HASH_PROMPTS redaction policy on prompt_text/system_prompt.
  const paramsRecord = params as Record<string, unknown>
  const paramsWithoutMessages: Record<string, unknown> = {}
  for (const k of Object.keys(paramsRecord)) {
    if (k !== 'messages') paramsWithoutMessages[k] = paramsRecord[k]
  }
  return {
    provider: 'anthropic',
    model: params.model,
    prompt_text: ctx.prompt_text ?? null,
    system_prompt: ctx.system_prompt ?? null,
    parameters: paramsWithoutMessages,
    conversation_id: ctx.conversation_id,
    conversation_name: ctx.conversation_name ?? null,
    prompt_id: ctx.prompt_id,
    parent_prompt_id: ctx.parent_prompt_id,
    user_id: ctx.user_id,
    pipeline_stage: ctx.pipeline_stage,
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Adapter
// ────────────────────────────────────────────────────────────────────────────

export interface ObservedAnthropicAdapter {
  messages: {
    create: AnthropicMessagesAPI['create']
  }
}

export function wrapAnthropic(
  client: AnthropicClient,
  ctx: AnthropicAdapterContext,
  db: ObservatoryDb,
): ObservedAnthropicAdapter {
  return {
    messages: {
      create: <P extends AnthropicCreateParams>(
        params: P,
        options?: AnthropicCallOptions,
      ): AnthropicCreateResult<P> => {
        const baseRequest = buildBaseRequest(ctx, params)
        if (params.stream === true) {
          return executeStreaming(
            client,
            baseRequest,
            params,
            options,
            db,
          ) as AnthropicCreateResult<P>
        }
        return executeNonStreaming(
          client,
          baseRequest,
          params,
          options,
          db,
        ) as AnthropicCreateResult<P>
      },
    },
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Non-streaming path
// ────────────────────────────────────────────────────────────────────────────

async function executeNonStreaming(
  client: AnthropicClient,
  baseRequest: ObservedLLMRequest,
  params: AnthropicCreateParams,
  options: AnthropicCallOptions | undefined,
  db: ObservatoryDb,
): Promise<AnthropicMessageResponse> {
  const startedAt = new Date()
  let raw: AnthropicMessageResponse
  try {
    raw = (await client.messages.create(
      params,
      options,
    )) as AnthropicMessageResponse
  } catch (err) {
    const mapped = mapAnthropicError(err)
    if (mapped.status === 'timeout') {
      await persistTimeoutRow(baseRequest, startedAt, db)
      throw err
    }
    if (err && typeof err === 'object') {
      try {
        ;(err as { code?: string }).code = mapped.error_code
      } catch {
        // ignore failure to set property on frozen errors
      }
    }
    // observe() handles the error-path persist (status='error', error_code).
    await observe<AnthropicMessageResponse>(
      baseRequest,
      async () => {
        throw err
      },
      db,
    ).catch(() => {
      // observe() re-throws after persisting; we plan to re-throw below.
    })
    throw err
  }

  const { response } = await observe<AnthropicMessageResponse>(
    baseRequest,
    async () => ({
      response: raw,
      rawUsage: extractAnthropicUsage(raw.usage),
      providerRequestId: extractAnthropicRequestId(raw, options?.headers),
    }),
    db,
  )
  return response
}

async function persistTimeoutRow(
  baseRequest: ObservedLLMRequest,
  startedAt: Date,
  db: ObservatoryDb,
): Promise<void> {
  const finishedAt = new Date()
  const observed: ObservedLLMResponse = {
    response_text: null,
    usage: { ...ZERO_USAGE },
    status: 'timeout',
    error_code: 'timeout',
    started_at: startedAt,
    finished_at: finishedAt,
  }
  try {
    const cost = await safeComputeCost(baseRequest, observed, db)
    await persistObservation(baseRequest, observed, cost, db)
  } catch (err) {

    console.error('[anthropic_observed] timeout persistence failed:', err)
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Streaming path
// ────────────────────────────────────────────────────────────────────────────

function executeStreaming(
  client: AnthropicClient,
  baseRequest: ObservedLLMRequest,
  params: AnthropicCreateParams,
  options: AnthropicCallOptions | undefined,
  db: ObservatoryDb,
): AsyncIterable<AnthropicStreamEvent> {
  async function* streamCall() {
    const stream = client.messages.create(
      params,
      options,
    ) as AsyncIterable<AnthropicStreamEvent>
    const providerRequestId = extractAnthropicRequestId(
      stream,
      options?.headers,
    )

    let accumulated: AnthropicUsage = {}
    for await (const event of stream) {
      if (
        event.type === 'message_start' &&
        (event as { message?: { usage?: AnthropicUsage } }).message?.usage
      ) {
        accumulated = {
          ...accumulated,
          ...(event as { message: { usage: AnthropicUsage } }).message.usage,
        }
      }
      if (
        event.type === 'message_delta' &&
        (event as { usage?: AnthropicUsage }).usage
      ) {
        accumulated = {
          ...accumulated,
          ...(event as { usage: AnthropicUsage }).usage,
        }
      }
      const isFinal =
        event.type === 'message_delta' || event.type === 'message_stop'
      yield {
        chunk: event,
        finalUsage: isFinal ? extractAnthropicUsage(accumulated) : undefined,
        providerRequestId,
      }
    }
  }

  return observeStream<AnthropicStreamEvent>(baseRequest, streamCall, db)
}
