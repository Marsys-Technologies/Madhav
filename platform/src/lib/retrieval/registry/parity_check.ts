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

// ── L0 Brahmagyan asset registry (12 assets post Phase α) ────────────────────
// Phase α (2026-06-08): 8 original + 4 new (bg_yogas, bg_dasha_systems,
// bg_doshas, bg_compendium_index). Per design §3 of L0_BRAHMAGYAN_HOLISTIC_DESIGN.
export const L0_BRAHMAGYAN_ASSETS = [
  'bg_ephemeris',
  'bg_reference',
  'bg_texts',
  'bg_ontology',
  'bg_text_index',
  'bg_rules',
  'bg_remedies',
  'bg_concordance',
  'bg_yogas',
  'bg_dasha_systems',
  'bg_doshas',
  'bg_compendium_index',
] as const

export type L0BrahmagyanAsset = (typeof L0_BRAHMAGYAN_ASSETS)[number]

// FK integrity assertions (run against prod periodically; non-blocking):
//   - every brahma_yoga_catalog.canonical_id appears in brahma_ontology (entity_class='yoga')
//   - every brahma_dosha_catalog.canonical_id appears in brahma_ontology (entity_class='dosha')
//   - every brahma_dasha_systems.canonical_id appears in brahma_ontology (entity_class='dasha_system')
//   - every brahma_compendium_index.text_id resolves in classical_texts
//   - every brahma_compendium_index.topic_id resolves in reference_topic_tags

import { listCapabilityUris } from './index'
import type { ParityCheckResult, CapabilityUri } from './types'

// ── MCP exports snapshot ──────────────────────────────────────────────────────

/**
 * Returns the set of URIs that the MCP server exports, plus the bridge's
 * error state (GT-36).
 *
 * Implementation: imports the MCP tool list and normalizes to marsys:// URIs.
 * In CI, this compares against the Consume Chat registry to detect drift.
 *
 * IMPORTANT: a failed dynamic import (`bridgeError !== null`) is NOT the same
 * condition as "the bridge loaded and legitimately exports zero URIs". The
 * caller (buildParityResult) must treat a failed bridge as a hard failure,
 * never as an empty-but-passing set.
 */
export async function getMcpExportedUris(): Promise<{
  uris: Set<CapabilityUri>
  bridgeError: string | null
}> {
  // Dynamic import to avoid hard dependency in non-MCP contexts
  try {
    const { listMcpCapabilityUris } = await import('./mcp_capability_bridge')
    const uris = await listMcpCapabilityUris()
    return { uris: new Set(uris), bridgeError: null }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { uris: new Set<CapabilityUri>(), bridgeError: message }
  }
}

// ── Parity check ─────────────────────────────────────────────────────────────

/**
 * Pure decision function: computes a ParityCheckResult from already-resolved
 * URI sets and bridge status. Split out from checkParity() so the GT-36
 * invariant — a failed bridge import is ALWAYS a hard failure, even in the
 * degenerate case where the Consume Chat registry is also empty — can be
 * unit-tested directly without mocking the dynamic import.
 */
export function buildParityResult(
  consumeUris: Set<CapabilityUri>,
  mcpUris: Set<CapabilityUri>,
  bridgeError: string | null,
): ParityCheckResult {
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
      missing_in_consume.push(uri)
    }
  }

  // GT-36: a failed bridge import must NEVER silently auto-pass — not even in
  // the degenerate case where the Consume Chat registry is also empty (which
  // would otherwise leave missing_in_mcp and extra_in_mcp both trivially
  // empty and report a false PASS).
  const passed = bridgeError === null && missing_in_mcp.length === 0 && extra_in_mcp.length === 0

  return {
    passed,
    mcp_count: mcpUris.size,
    consume_count: consumeUris.size,
    missing_in_mcp,
    missing_in_consume,
    extra_in_mcp,
    bridge_error: bridgeError,
  }
}

/**
 * Run the parity check between MCP exports and Consume Chat registry.
 * Returns a ParityCheckResult with details.
 */
export async function checkParity(): Promise<ParityCheckResult> {
  const consumeUris = new Set(listCapabilityUris())
  const { uris: mcpUris, bridgeError } = await getMcpExportedUris()
  return buildParityResult(consumeUris, mcpUris, bridgeError)
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

    if (result.bridge_error) {
      lines.push(`  MCP bridge FAILED to load: ${result.bridge_error}`)
      lines.push(
        `  (GT-36: parity cannot be verified while the bridge is unavailable — this is always a hard failure, never an auto-pass)`
      )
    }

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
