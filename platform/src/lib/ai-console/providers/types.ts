import 'server-only'
import { inspect } from 'node:util'
import type { LanguageModelV3, LanguageModelV3StreamPart } from '@ai-sdk/provider'
import type { AiRole, ProviderId } from '../types'
import { AiConsoleError, normalizeAiError } from '../errors'

export interface DiscoveredModel {
  modelId: string
  displayName: string
  compatibleRoles: AiRole[]
  supportsTools: boolean
  supportsStructuredOutput: boolean
  contextWindow?: number
  outputLimit?: number
}
export interface ProbeUsage { inputTokens: number | null; outputTokens: number | null; reasoningTokens?: number }
export interface RuntimeModelBinding {
  readonly providerId: ProviderId
  readonly modelId: string
  readonly model: LanguageModelV3
  dispose(): void
}
export type RequestPreflight = () => Promise<void>
export interface ProviderValidationAdapter {
  readonly providerId: ProviderId
  discover(apiKey: string, signal: AbortSignal, preflight?: RequestPreflight): Promise<DiscoveredModel[]>
  probe(apiKey: string, model: DiscoveredModel, signal: AbortSignal, preflight?: RequestPreflight): Promise<ProbeUsage>
  createRuntimeBinding(apiKey: string, model: DiscoveredModel, preflight?: RequestPreflight): RuntimeModelBinding
}

export const PROVIDER_BASE_URLS = Object.freeze({
  openai: 'https://api.openai.com/v1', anthropic: 'https://api.anthropic.com/v1',
  google: 'https://generativelanguage.googleapis.com/v1beta', xai: 'https://api.x.ai/v1',
  deepseek: 'https://api.deepseek.com', kimi: 'https://api.moonshot.ai/v1', openrouter: 'https://openrouter.ai/api/v1',
})
export const PROBE_OUTPUT_TOKENS = 16
export const MAX_CATALOG_PAGES = 10
// Never persisted, returned, logged, traced or included in error metadata.
export const PROBE_PROMPT = 'Reply OK.'
export const fail = () => new AiConsoleError('AI_EXECUTION_FAILED')
export function assertApiKey(key: string): void {
  if (typeof key !== 'string' || key.length < 8 || key.length > 16_384 || !/^[\x21-\x7e]+$/.test(key)) {
    throw new AiConsoleError('AI_CONNECTION_INVALID')
  }
}
export function object(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}
export function tokenCount(value: unknown): number | null {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : null
}
export function providerHeaders(provider: ProviderId, key: string): Headers {
  assertApiKey(key)
  const headers = new Headers({ 'Content-Type': 'application/json', Accept: 'application/json' })
  if (provider === 'anthropic') { headers.set('x-api-key', key); headers.set('anthropic-version', '2023-06-01') }
  else if (provider === 'google') headers.set('x-goog-api-key', key)
  else headers.set('Authorization', `Bearer ${key}`)
  return headers
}

/** Total deadline includes headers AND streamed body. Never return upstream errors/bodies. */
export async function boundedFetch(url: string, init: RequestInit, timeoutMs: number, maxBytes: number, providerId?: ProviderId, preflight?: RequestPreflight): Promise<Response> {
  const controller = new AbortController()
  const cancel = () => controller.abort()
  const callerSignal = init.signal
  callerSignal?.addEventListener('abort', cancel, { once: true })
  let expired = false
  const timer = setTimeout(() => { expired = true; cancel() }, timeoutMs)
  const cleanup = () => { clearTimeout(timer); callerSignal?.removeEventListener('abort', cancel) }
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined
  const safeError = (error: unknown) => {
    if (error instanceof AiConsoleError) return error
    if (callerSignal?.aborted) return fail()
    if (expired || error instanceof TypeError) return new AiConsoleError('AI_PROVIDER_UNREACHABLE')
    return new AiConsoleError(normalizeAiError(error, { source: 'provider' }).code)
  }
  let abortListener: (() => void) | undefined
  const abortRace = new Promise<never>((_resolve, reject) => {
    abortListener = () => reject(expired ? new AiConsoleError('AI_PROVIDER_UNREACHABLE') : fail())
    controller.signal.addEventListener('abort', abortListener, { once: true })
  })
  const finish = () => { cleanup(); if (abortListener) controller.signal.removeEventListener('abort', abortListener) }
  try {
    if (callerSignal?.aborted) throw fail()
    if (preflight) await Promise.race([preflight(), abortRace])
    if (controller.signal.aborted) throw expired ? new AiConsoleError('AI_PROVIDER_UNREACHABLE') : fail()
    const response = await Promise.race([fetch(url, { ...init, signal: controller.signal, redirect: 'error', cache: 'no-store' }), abortRace])
    if (response.status < 200 || response.status >= 300) {
      // A small complete JSON error may distinguish billing from rate limiting.
      // Retain no message/body: only allowlisted machine discriminators escape.
      let billing = false
      const bytes = new Uint8Array(4096)
      let length = 0
      try {
        if (response.body && Number(response.headers.get('content-length')) <= bytes.length) {
          reader = response.body.getReader()
          while (true) {
            const chunk = await Promise.race([reader.read(), abortRace])
            if (chunk.done) {
              try {
                const error = object(object(JSON.parse(new TextDecoder().decode(bytes.subarray(0, length)))).error)
                if (response.status === 429 && providerId === 'openai') {
                  const codes = ['insufficient_quota', 'credit_balance_exhausted', 'organization_spend_limit_exceeded', 'project_spend_limit_exceeded', 'organization_usage_limit_exceeded']
                  billing = (typeof error.code === 'string' && codes.includes(error.code)) || error.type === 'insufficient_quota'
                }
                if (response.status === 429 && providerId === 'kimi') billing = error.type === 'exceeded_current_quota_error'
              } catch { /* Malformed error content never overrides the HTTP class. */ }
              break
            }
            if (length + chunk.value.byteLength > bytes.length) break
            bytes.set(chunk.value, length); length += chunk.value.byteLength
          }
        }
      } finally {
        bytes.fill(0)
        if (reader) void reader.cancel().catch(() => undefined)
        else void response.body?.cancel().catch(() => undefined)
      }
      if (billing) throw new AiConsoleError('AI_BILLING_UNAVAILABLE')
      throw response.status === 529 ? new AiConsoleError('AI_PROVIDER_UNREACHABLE')
        : new AiConsoleError(normalizeAiError({ status: response.status }, { source: 'provider' }).code)
    }
    if (!response.body || Number(response.headers.get('content-length')) > maxBytes) {
      void response.body?.cancel().catch(() => undefined)
      throw fail()
    }
    reader = response.body.getReader()
    let bytes = 0
    const body = new ReadableStream<Uint8Array>({
      async pull(stream) {
        try {
          const chunk = await Promise.race([reader!.read(), abortRace])
          if (chunk.done) { finish(); stream.close(); return }
          bytes += chunk.value.byteLength
          if (bytes > maxBytes) throw fail()
          stream.enqueue(chunk.value)
        } catch (error) {
          cancel(); void reader?.cancel().catch(() => undefined); finish(); stream.error(safeError(error))
        }
      },
      cancel() { cancel(); void reader?.cancel().catch(() => undefined); finish() },
    })
    // Do not carry arbitrary upstream headers or status text into SDK error objects.
    const contentType = response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() === 'text/event-stream' ? 'text/event-stream' : 'application/json'
    return new Response(body, { status: 200, headers: { 'Content-Type': contentType } })
  } catch (error) {
    finish(); cancel(); void reader?.cancel().catch(() => undefined)
    throw safeError(error)
  }
}

export async function providerJson(provider: ProviderId, key: string, path: string, signal: AbortSignal, body?: unknown, preflight?: RequestPreflight): Promise<Record<string, unknown>> {
  const response = await boundedFetch(PROVIDER_BASE_URLS[provider] + path,
    { method: body === undefined ? 'GET' : 'POST', headers: providerHeaders(provider, key), signal,
      ...(body === undefined ? {} : { body: JSON.stringify(body) }) }, 15_000, body === undefined ? 2_097_152 : 65_536, provider, preflight)
  try {
    const parsed: unknown = await response.json()
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw fail()
    return object(parsed)
  } catch (error) { throw error instanceof AiConsoleError ? error : fail() }
}

/** No key or SDK object is enumerable/serializable. Disposal revokes even extracted models. */
export function runtimeBinding(providerId: ProviderId, apiKey: string, modelId: string,
  create: (http: typeof fetch) => LanguageModelV3, preflight?: RequestPreflight): RuntimeModelBinding {
  assertApiKey(apiKey)
  let secret: string | undefined = apiKey
  const lifetime = new AbortController()
  const expiresAt = Date.now() + 5 * 60_000
  const base = PROVIDER_BASE_URLS[providerId]
  const http: typeof fetch = async (input, init) => {
    if (!secret || Date.now() >= expiresAt) throw fail()
    const url = new URL(input instanceof Request ? input.url : String(input))
    const suffix = url.href.slice(base.length)
    const allowed = providerId === 'anthropic' ? suffix === '/messages'
      : providerId === 'google' ? [`/models/${modelId}:generateContent`, `/models/${modelId}:streamGenerateContent?alt=sse`].includes(suffix)
        : suffix === '/chat/completions'
    if (!url.href.startsWith(base + '/') || !allowed || init?.method !== 'POST') throw fail()
    const request = { ...init, headers: providerHeaders(providerId, secret), signal: AbortSignal.any([lifetime.signal, ...(init.signal ? [init.signal] : [])]) }
    if (providerId !== 'anthropic' && providerId !== 'google') {
      let payload: Record<string, unknown>
      try { payload = object(JSON.parse(String(request.body))) } catch { throw fail() }
      const modernCap = ['openai', 'kimi', 'openrouter'].includes(providerId)
      // Enforce current provider field names even when the installed shared SDK
      // emits the legacy spelling. Exact model only, never provider/model fallback.
      request.body = JSON.stringify({ ...payload, model: modelId,
        ...(modernCap ? { max_completion_tokens: payload.max_completion_tokens ?? payload.max_tokens, max_tokens: undefined }
          : { max_tokens: payload.max_tokens ?? payload.max_completion_tokens, max_completion_tokens: undefined }),
        ...(providerId === 'openrouter' ? { models: undefined, route: undefined, provider: { allow_fallbacks: false, require_parameters: true } } : {}),
      })
    }
    return boundedFetch(url.href, request, 120_000, 8_388_608, providerId, preflight)
  }
  const sdk = create(http)
  const normalized = (cause: unknown) => new AiConsoleError(normalizeAiError(cause, { source: 'provider' }).code)
  let model: LanguageModelV3 | undefined = {
    specificationVersion: sdk.specificationVersion, provider: sdk.provider, modelId: sdk.modelId, supportedUrls: sdk.supportedUrls,
    async doGenerate(options) {
      try { if (!secret || lifetime.signal.aborted) throw fail(); return await sdk.doGenerate(options) }
      catch (cause) { throw normalized(cause) }
    },
    async doStream(options) {
      try {
        if (!secret || lifetime.signal.aborted) throw fail()
        const result = await sdk.doStream(options)
        const reader = result.stream.getReader()
        return { ...result, stream: new ReadableStream<LanguageModelV3StreamPart>({
          async pull(controller) {
            try {
              const chunk = await reader.read()
              if (chunk.done) { controller.close(); return }
              controller.enqueue(chunk.value.type === 'error' ? { type: 'error', error: normalized(chunk.value.error) } : chunk.value)
            } catch (cause) { controller.error(normalized(cause)) }
          },
          cancel() { return reader.cancel() },
        }) }
      } catch (cause) { throw normalized(cause) }
    },
  }
  const binding = Object.create(null)
  Object.defineProperties(binding, {
    providerId: { value: providerId, enumerable: true }, modelId: { value: modelId, enumerable: true },
    model: { get: () => { if (!model || !secret || Date.now() >= expiresAt) throw fail(); return model } },
    dispose: { value: () => { secret = undefined; model = undefined; lifetime.abort() } },
    toJSON: { value: () => { throw fail() } },
    [inspect.custom]: { value: () => '[AI runtime binding: REDACTED]' },
  })
  return Object.freeze(binding) as RuntimeModelBinding
}
