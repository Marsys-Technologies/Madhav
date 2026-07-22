/**
 * http_client.ts — thin, dependency-free HTTP request wrapper shared by every
 * measurement mode. Uses global `fetch` (Node 18+/24 built-in, no extra dependency),
 * records wall-clock latency around the call, and extracts the cache-hit signal via
 * the target's configured `cacheHitField` dot-path (default `served_from_cache`,
 * `types.ts`).
 */
import { getByPath } from './stats'
import type { LoadTarget, RequestResult } from './types'

export function defaultTarget(baseUrl: string, overrides: Partial<LoadTarget> = {}): LoadTarget {
  return {
    baseUrl,
    path: overrides.path ?? '/query',
    method: overrides.method ?? 'POST',
    headers: overrides.headers ?? { 'content-type': 'application/json' },
    cacheHitField: overrides.cacheHitField ?? 'served_from_cache',
    timeoutMs: overrides.timeoutMs ?? 10_000,
  }
}

export async function sendOne(
  target: LoadTarget,
  body: Record<string, unknown>,
  extra?: { queryClass?: string },
): Promise<RequestResult> {
  const url = `${target.baseUrl}${target.path}`
  const t0 = performance.now()
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), target.timeoutMs)

  try {
    const res = await fetch(url, {
      method: target.method,
      headers: target.headers,
      body: target.method === 'POST' ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
    const latencyMs = performance.now() - t0
    let json: unknown = undefined
    try {
      json = await res.json()
    } catch {
      json = undefined
    }
    const cacheHit = getByPath(json, target.cacheHitField) === true
    const honestlyRefused =
      (res.status === 503 || res.status === 429) &&
      json !== undefined &&
      typeof json === 'object' &&
      (json as Record<string, unknown>).honest_refusal === true
    const queryClass =
      (json !== undefined && typeof json === 'object' && typeof (json as Record<string, unknown>).query_class === 'string'
        ? ((json as Record<string, unknown>).query_class as string)
        : undefined) ?? extra?.queryClass

    return {
      ok: res.ok,
      status: res.status,
      latencyMs,
      cacheHit,
      queryClass,
      principalId: typeof body.principalId === 'string' ? body.principalId : undefined,
      priorityClass: body.priorityClass === 'background' ? 'background' : body.priorityClass === 'interactive' ? 'interactive' : undefined,
      honestlyRefused,
    }
  } catch (err) {
    const latencyMs = performance.now() - t0
    return {
      ok: false,
      status: -1,
      latencyMs,
      cacheHit: false,
      queryClass: extra?.queryClass,
      principalId: typeof body.principalId === 'string' ? body.principalId : undefined,
      priorityClass: body.priorityClass === 'background' ? 'background' : body.priorityClass === 'interactive' ? 'interactive' : undefined,
      error: err instanceof Error ? err.message : String(err),
    }
  } finally {
    clearTimeout(timer)
  }
}
