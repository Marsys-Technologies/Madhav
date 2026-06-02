/**
 * registry.ts — CLEAN SLATE STUB
 *
 * All tool contracts removed as part of legacy-teardown (feature/legacy-teardown).
 * Rebuild per layer during the Layer-0 → Layer-3 arc.
 */

import type { ToolContract } from './types'

export const TOOL_CONTRACTS: readonly ToolContract<unknown>[] = []

export function getContract(canonical_name: string): ToolContract<unknown> | undefined {
  return TOOL_CONTRACTS.find(c => c.canonical_name === canonical_name)
}

export function getContractNames(): string[] {
  return TOOL_CONTRACTS.map(c => c.canonical_name)
}
