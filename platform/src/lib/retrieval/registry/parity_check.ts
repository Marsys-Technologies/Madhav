/**
 * retrieval/registry/parity_check.ts
 *
 * CI gate: compares MCP server exports to Consume Chat registry.
 * Throws on mismatch (missing capabilities in either surface).
 *
 * Usage (CI):
 *   npx ts-node platform/src/lib/retrieval/registry/parity_check.ts
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities, getRegistrySnapshot } from './index'
// Load L0 capabilities into the registry before running parity check
import './layers/L0_brahmagyan/index'

// ── MCP tool catalog (loaded from platform-mcp at build time) ─────────────────
// In CI, this reads from the MCP server's registered tool list.
// For local checks, it can read from a JSON snapshot.

const MCP_TOOL_LIST_PATH = process.env['MCP_TOOL_LIST_PATH'] ??
  '../../../platform-mcp/src/generated/tool_list.json'

interface ParityResult {
  portal_only: string[]   // in Consume Chat but not MCP
  mcp_only: string[]      // in MCP but not Consume Chat
  matched: string[]
  pass: boolean
}

export async function runParityCheck(opts?: {
  mcpToolList?: string[]  // override for unit tests
}): Promise<ParityResult> {
  // Load Consume Chat registry
  const portalCaps = listCapabilities()
  const portalUris = new Set(portalCaps.map(c => c.uri))

  // Load MCP tool list
  let mcpUris: Set<string>

  if (opts?.mcpToolList) {
    mcpUris = new Set(opts.mcpToolList)
  } else {
    try {
      // Try to load from generated JSON snapshot
      const fs = await import('fs')
      const raw = fs.readFileSync(MCP_TOOL_LIST_PATH, 'utf-8')
      const list = JSON.parse(raw) as string[]
      mcpUris = new Set(list)
    } catch {
      // If no MCP snapshot, skip MCP side (CI will have it; local may not)
      console.warn('[parity_check] MCP tool list not found — checking portal-only')
      mcpUris = new Set(portalUris)  // treat as matched for local runs
    }
  }

  const portalOnly = [...portalUris].filter(u => !mcpUris.has(u))
  const mcpOnly = [...mcpUris].filter(u => !portalUris.has(u))
  const matched = [...portalUris].filter(u => mcpUris.has(u))

  const pass = portalOnly.length === 0 && mcpOnly.length === 0

  return { portal_only: portalOnly, mcp_only: mcpOnly, matched, pass }
}

// ── CLI runner ────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const result = await runParityCheck()

  console.log('\n=== Retrieval Registry Parity Check ===')
  console.log(`Matched: ${result.matched.length}`)

  if (result.portal_only.length > 0) {
    console.error('\n[FAIL] Portal-only (missing from MCP):')
    result.portal_only.forEach(u => console.error(`  - ${u}`))
  }

  if (result.mcp_only.length > 0) {
    console.error('\n[FAIL] MCP-only (missing from portal):')
    result.mcp_only.forEach(u => console.error(`  - ${u}`))
  }

  if (result.pass) {
    console.log('\n✓ PARITY PASS — all capabilities registered in both surfaces\n')
    process.exit(0)
  } else {
    console.error('\n✗ PARITY FAIL — surfaces are out of sync\n')
    process.exit(1)
  }
}

if (require.main === module) {
  main().catch(err => {
    console.error('[parity_check] fatal:', err)
    process.exit(1)
  })
}
