/**
 * executor_registry — the gateway's pluggable tool dispatch table.
 *
 * The gateway module (this folder) is contract-only: it knows tool
 * identities, schemas, families, and ayanamsha roles. It does NOT import
 * `platform/src/lib/retrieve/**` (that fence is owned by the sibling
 * 3.tool_asset_recon unit). To call a tool, retrieve-layer code calls
 * `registerExecutor(name, fn)` once at startup; the gateway's `invoke_tool`
 * looks the executor up here at dispatch time.
 *
 * If no executor is registered for a tool name, `invoke_tool` returns
 * GatewayError('NO_EXECUTOR'). This is the "plumbing wired but engine
 * absent" diagnostic — useful in tests and during partial rollout.
 */

import type { ToolExecutor } from './types'

const REGISTRY = new Map<string, ToolExecutor<unknown, unknown>>()

export function registerExecutor<TInput, TOutput>(
  canonical_name: string,
  executor: ToolExecutor<TInput, TOutput>,
): void {
  REGISTRY.set(canonical_name, executor as ToolExecutor<unknown, unknown>)
}

export function getExecutor(
  canonical_name: string,
): ToolExecutor<unknown, unknown> | undefined {
  return REGISTRY.get(canonical_name)
}

export function hasExecutor(canonical_name: string): boolean {
  return REGISTRY.has(canonical_name)
}

/** Test-only: wipe the registry between tests. */
export function __resetRegistryForTests(): void {
  REGISTRY.clear()
}

/** Snapshot of registered names (debug / health). */
export function listRegisteredExecutors(): string[] {
  return Array.from(REGISTRY.keys()).sort()
}
