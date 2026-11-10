// observe() / observeStream() — the two public entry points provider adapters
// (S1.4–S1.8) call to wrap an LLM call. Wrapping does three things:
//   1. Brackets the call with started_at / finished_at timestamps.
//   2. On both success and failure paths, emits one telemetry row via
//      persistObservation (cost computed locally; pricing_version_id frozen).
//   3. Never lets observability errors surface to the caller — the original
//      provider response (or thrown error) passes through untouched.
//
// OD.S1.7.1 — RESOLVED 2026-05-03 (USTAD_S1_13). Both observe() and
// observeStream() classify every thrown error as `status: 'error'`. They do
// NOT distinguish a provider timeout (AbortError, deadline exceeded, etc.)
// from any other thrown error — the wrapper has no provider-specific
// knowledge. Adapters that detect a timeout call persistObservation()
// directly with `status: 'timeout'` before re-throwing, then skip the
// observe() wrapping for that specific call. See persistObservation() JSDoc
// for the escape-hatch contract.

import { computeCost } from './cost'
import { persistObservation } from './persist'
import type {
  CostResult,
  ObservatoryDb,
  ObservedLLMRequest,
  ObservedLLMResponse,
  PersistedObservation,
  TokenUsage,
} from './types'
import { ZERO_USAGE } from './types'

interface ProviderCallResult<T> {
  response: T
  rawUsage: TokenUsage
  providerRequestId?: string
}

interface StreamYield<T> {
  chunk: T
  finalUsage?: TokenUsage
  providerRequestId?: string
}

function extractErrorCode(err: unknown): string {
  if (err && typeof err === 'object') {
    const e = err as { code?: unknown; name?: unknown; message?: unknown }
    if (typeof e.code === 'string' && e.code.length > 0) return e.code
    if (typeof e.name === 'string' && e.name.length > 0) return e.name
    if (typeof e.message === 'string' && e.message.length > 0) return e.message
  }
  return 'unknown_error'
}

async function safeComputeCost(
  request: ObservedLLMRequest,
  response: ObservedLLMResponse,
  db: ObservatoryDb,
): Promise<CostResult | null> {
  try {
    return await computeCost(
      request.provider,
      request.model,
      response.usage,
      response.started_at,
      db,
    )
  } catch (err) {

    console.error('[observability] computeCost failed:', err)
    return null
  }
}

export async function observe<T>(
  request: ObservedLLMRequest,
  providerCall: () => Promise<ProviderCallResult<T>>,
  db: ObservatoryDb,
): Promise<{ response: T; observation: PersistedObservation | null }> {
  const startedAt = new Date()

  try {
    const result = await providerCall()
    const finishedAt = new Date()
    const observed: ObservedLLMResponse = {
      response_text: null,
      usage: result.rawUsage,
      provider_request_id: result.providerRequestId,
      status: 'success',
      started_at: startedAt,
      finished_at: finishedAt,
    }

    let observation: PersistedObservation | null = null
    try {
      const cost = await safeComputeCost(request, observed, db)
      observation = await persistObservation(request, observed, cost, db)
    } catch (err) {

      console.error('[observability] observe() persistence path failed:', err)
    }

    return { response: result.response, observation }
  } catch (providerErr) {
    const finishedAt = new Date()
    const observed: ObservedLLMResponse = {
      response_text: null,
      usage: { ...ZERO_USAGE },
      status: 'error',
      error_code: extractErrorCode(providerErr),
      started_at: startedAt,
      finished_at: finishedAt,
    }

    try {
      const cost = await safeComputeCost(request, observed, db)
      await persistObservation(request, observed, cost, db)
    } catch (err) {

      console.error('[observability] observe() error-path persistence failed:', err)
    }

    throw providerErr
  }
}

export async function* observeStream<T>(
  request: ObservedLLMRequest,
  streamCall: () => AsyncIterable<StreamYield<T>>,
  db: ObservatoryDb,
): AsyncGenerator<T> {
  const startedAt = new Date()
  let accumulatedUsage: TokenUsage = { ...ZERO_USAGE }
  let providerRequestId: string | undefined
  let streamErr: unknown = null

  try {
    for await (const item of streamCall()) {
      if (item.finalUsage) {
        accumulatedUsage = item.finalUsage
      }
      if (item.providerRequestId) {
        providerRequestId = item.providerRequestId
      }
      yield item.chunk
    }
  } catch (err) {
    streamErr = err
  } finally {
    const finishedAt = new Date()
    const observed: ObservedLLMResponse = streamErr
      ? {
          response_text: null,
          usage: accumulatedUsage,
          provider_request_id: providerRequestId,
          status: 'error',
          error_code: extractErrorCode(streamErr),
          started_at: startedAt,
          finished_at: finishedAt,
        }
      : {
          response_text: null,
          usage: accumulatedUsage,
          provider_request_id: providerRequestId,
          status: 'success',
          started_at: startedAt,
          finished_at: finishedAt,
        }

    try {
      const cost = await safeComputeCost(request, observed, db)
      await persistObservation(request, observed, cost, db)
    } catch (err) {

      console.error('[observability] observeStream persistence failed:', err)
    }
  }

  if (streamErr) throw streamErr
}
