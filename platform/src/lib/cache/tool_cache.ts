/**
 * MARSYS-JIS Stream D — Request-scoped tool-call cache
 * schema_version: 1.0
 *
 * Stores Promises (not resolved values) so concurrent calls with the same key
 * share ONE promise — the tool executes exactly once under concurrency.
 */

import crypto from 'crypto'
import type { ToolBundle } from '../retrieval/shared_types'

export class RequestScopedToolCache {
  private cache: Map<string, Promise<ToolBundle>> = new Map()

  /**
   * Generate a deterministic cache key regardless of object key order.
   */
  generateKey(toolName: string, params: Record<string, unknown>): string {
    const normalized = JSON.stringify(params, Object.keys(params).sort())
    const hash = crypto.createHash('sha256').update(normalized).digest('hex')
    return `${toolName}:${hash}`
  }

  /**
   * Synchronously check whether a promise is stored for this key.
   * Returns the raw Promise so callers can await it themselves.
   * Use this inside executeWithCache to enable coalescing: two concurrent
   * calls both see the same Promise before either has awaited it.
   */
  getPromise(
    toolName: string,
    params: Record<string, unknown>,
  ): Promise<ToolBundle> | undefined {
    const key = this.generateKey(toolName, params)
    return this.cache.get(key)
  }

  async get(
    toolName: string,
    params: Record<string, unknown>,
  ): Promise<ToolBundle | undefined> {
    const key = this.generateKey(toolName, params)
    const promise = this.cache.get(key)
    return promise ? await promise : undefined
  }

  put(
    toolName: string,
    params: Record<string, unknown>,
    resultPromise: Promise<ToolBundle>,
  ): void {
    const key = this.generateKey(toolName, params)
    this.cache.set(key, resultPromise)
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }
}

export function createToolCache(): RequestScopedToolCache {
  return new RequestScopedToolCache()
}
