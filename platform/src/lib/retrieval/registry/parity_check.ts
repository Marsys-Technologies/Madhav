/**
 * L0FR Stream A — Parity Check
 * ==============================
 * CI gate: compares MCP exports to Consume Chat registry.
 * Throws on mismatch.
 *
 * Usage (CI):
 *   import { runParityCheck } from '@/lib/retrieval/registry/parity_check'
 *   runParityCheck() // throws on mismatch
 */

import { listCapabilityUris } from './index'
import type { ParityCheckResult, CapabilityUri } from './types'

// ── MCP exports snapshot ──────────────────────────────────────────────────────

/**
 * Returns the set of URIs that the MCP server exports.
 * This function reads the MCP tool registrations at runtime.
 *
 * Implementation: imports the MCP tool list and normalizes to marsys:// URIs.
 * In CI, this compares against the Consume Chat registry to detect drift.
 */
export async function getMcpExportedUris(): Promise<Set<CapabilityUri>> {
  // Dynamic import to avoid hard dependency in non-MCP contexts
  try {
    const { listMcpCapabilityUris } = await import('./mcp_capability_bridge')
    const uris = await listMcpCapabilityUris()
    return new Set(uris)
  } catch {
    // Bridge not available (standalone mode) — return empty set
    return new Set<CapabilityUri>()
  }
}

// ── Parity check ─────────────────────────────────────────────────────────────

/**
 * Run the parity check between MCP exports and Consume Chat registry.
 * Returns a ParityCheckResult with details.
 */
export async function checkParity(): Promise<ParityCheckResult> {
  const consumeUris = new Set(listCapabilityUris())
  const mcpUris = await getMcpExportedUris()

  const missing_in_mcp: CapabilityUri[] = []
  const missing_in_consume: CapabilityUri[] = []
  const extra_in_mcp: CapabilityUri[] = []

  // Find URIs in Consume Chat but not in MCP
  for (const uri of consumeUris) {
    if (!mcpUris.has(uri)) {
      missing_in_mcp.push(uri)
    }
  }

  // Find URIs in MCP but not in Consume Chat
  for (const uri of mcpUris) {
    if (!consumeUris.has(uri)) {
      extra_in_mcp.push(uri)
    }
    if (!consumeUris.has(uri)) {
      missing_in_consume.push(uri)
    }
  }

  const passed = missing_in_mcp.length === 0 && extra_in_mcp.length === 0

  return {
    passed,
    mcp_count: mcpUris.size,
    consume_count: consumeUris.size,
    missing_in_mcp,
    missing_in_consume,
    extra_in_mcp,
  }
}

/**
 * Run parity check and throw on mismatch.
 * For use in CI gates.
 */
export async function runParityCheck(): Promise<void> {
  const result = await checkParity()

  if (!result.passed) {
    const lines: string[] = [
      `[parity_check] FAIL — registry mismatch detected`,
      `  MCP exports: ${result.mcp_count}`,
      `  Consume Chat registry: ${result.consume_count}`,
    ]

    if (result.missing_in_mcp.length > 0) {
      lines.push(`  In Consume Chat but NOT in MCP (${result.missing_in_mcp.length}):`)
      result.missing_in_mcp.forEach((u) => lines.push(`    - ${u}`))
    }

    if (result.extra_in_mcp.length > 0) {
      lines.push(`  In MCP but NOT in Consume Chat (${result.extra_in_mcp.length}):`)
      result.extra_in_mcp.forEach((u) => lines.push(`    - ${u}`))
    }

    throw new Error(lines.join('\n'))
  }

  console.log(
    `[parity_check] PASS — ${result.consume_count} capabilities registered in both channels`
  )
}

/**
 * Synchronous parity check for use in module initialization.
 * Only checks that both registries have the same count (quick sanity).
 */
export function quickParityCheck(mcpUris: CapabilityUri[]): boolean {
  const consumeUris = listCapabilityUris()
  const consumeSet = new Set(consumeUris)
  const mcpSet = new Set(mcpUris)

  for (const uri of consumeSet) {
    if (!mcpSet.has(uri)) {
      console.error(`[parity_check] DRIFT: ${uri} in Consume Chat but not in MCP`)
      return false
    }
  }
  return true
}
