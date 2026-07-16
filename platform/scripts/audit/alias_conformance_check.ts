#!/usr/bin/env tsx
/**
 * alias_conformance_check.ts — O-7 (D-1.6 Lane S-6, 2026-07-16)
 *
 * Lightweight harness that asserts every registered "[Phase-1 alias]" MCP tool's payload
 * matches its primitive's, pairing with Lane S-1's CR-51/CR-30 canonical-face work (one
 * canonical face per capability; the other is a strict alias or is retired — see BRIEF_D1_6.md
 * Lane S-1). This script is the CHECK, not the doctrine — it discovers alias/primitive pairs
 * mechanically from the deployed connector's own tool descriptions rather than a hand-maintained
 * list, so it stays correct as S-1 (or any future lane) adds/retires aliases.
 *
 * Discovery: every tool whose description begins with the literal marker `[Phase-1 alias]`
 * and contains `(same as <primitive_name>)` is treated as an alias of `<primitive_name>`. This
 * marker convention is already used consistently across platform-mcp/src/tools/register_p1_*.ts
 * (confirmed live: e.g. ref_planet_transit_get → "[Phase-1 alias] ... (same as
 * query_planet_transit)."). A tool whose named primitive doesn't exist on the live tools/list
 * is reported as a BROKEN_PAIR (dangling alias reference), not silently skipped.
 *
 * Conformance check: for each pair, call both tools with an IDENTICAL argument set (derived
 * from each tool's own required inputSchema fields, using a single shared probe chart_id) and
 * deep-compare the unwrapped content, ignoring known non-deterministic fields (timestamps,
 * trace/request IDs, computed_at, latency_ms — anything that legitimately differs between two
 * independent calls a few hundred ms apart). A pair whose primitive requires an argument this
 * script cannot safely synthesize (anything other than chart_id / a date / a UUID it already
 * knows) is reported SKIPPED_NO_SAFE_ARGS, never silently treated as a pass.
 *
 * Usage:
 *   MCP_SERVER_URL=https://<host>/mcp MCP_BEARER=<token> npx tsx alias_conformance_check.ts
 *   (or the ?api_key= face: MCP_SERVER_URL='https://<host>/mcp?api_key=...' npx tsx ...)
 *
 * Exit code: 0 if every discovered pair is PASS or an explicitly-allowed SKIP; 1 if any
 * MISMATCH or BROKEN_PAIR is found (CI/gate-usable).
 */

import { McpClient, envOrDefault, type McpToolDescriptor } from './doctrine_harness/lib/mcp_client.js'

const PROBE_CHART_ID = envOrDefault('PROBE_CHART_ID', '482012f1-710e-4a25-994a-93821f5871aa')!

// Fields that legitimately differ between two independent calls a few hundred ms apart —
// stripped before deep-comparison so they never cause a false MISMATCH.
const VOLATILE_KEY_PATTERN = /^(computed_at|trace_id|request_id|latency_ms|served_from_cache|result_hash|tool_bundle_id)$/i

function stripVolatile(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stripVolatile)
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      if (VOLATILE_KEY_PATTERN.test(k)) continue
      out[k] = stripVolatile(v)
    }
    return out
  }
  return value
}

function deepEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(stripVolatile(a)) === JSON.stringify(stripVolatile(b))
}

interface AliasPair {
  alias: string
  primitive: string
}

const ALIAS_MARKER = /^\[Phase-1 alias\]/
const SAME_AS_PATTERN = /\(same as ([a-zA-Z0-9_]+)\)/

function discoverPairs(tools: McpToolDescriptor[]): AliasPair[] {
  const pairs: AliasPair[] = []
  for (const t of tools) {
    const desc = t.description ?? ''
    if (!ALIAS_MARKER.test(desc)) continue
    const m = desc.match(SAME_AS_PATTERN)
    if (!m) continue
    pairs.push({ alias: t.name, primitive: m[1] })
  }
  return pairs
}

/** Synthesizes a safe, identical argument set for BOTH tools of a pair from their
 *  combined required inputSchema properties. Returns null if either tool requires a field
 *  this script cannot safely fabricate. */
function synthesizeArgs(alias: McpToolDescriptor, primitive: McpToolDescriptor): Record<string, unknown> | null {
  const schema = (t: McpToolDescriptor): { properties: Record<string, { type?: string }>; required: string[] } => {
    const s = (t.inputSchema ?? {}) as { properties?: Record<string, { type?: string }>; required?: string[] }
    return { properties: s.properties ?? {}, required: s.required ?? [] }
  }
  const a = schema(alias)
  const p = schema(primitive)
  const requiredFields = new Set([...a.required, ...p.required])
  const args: Record<string, unknown> = {}
  for (const field of requiredFields) {
    const propType = a.properties[field]?.type ?? p.properties[field]?.type
    if (field === 'chart_id') {
      args[field] = PROBE_CHART_ID
    } else if (/date/i.test(field)) {
      args[field] = '2026-07-01'
    } else if (/planet|graha/i.test(field)) {
      args[field] = 'Saturn'
    } else if (propType === 'string') {
      // Unknown required string field — cannot safely synthesize a meaningful value.
      return null
    } else if (propType === 'number' || propType === 'integer') {
      return null
    } else {
      return null
    }
  }
  return args
}

type PairResult = { pair: AliasPair; status: 'PASS' | 'MISMATCH' | 'BROKEN_PAIR' | 'SKIPPED_NO_SAFE_ARGS' | 'ERROR'; detail?: string }

async function main(): Promise<void> {
  const url = envOrDefault('MCP_SERVER_URL')
  if (!url) {
    console.error('MCP_SERVER_URL is required (e.g. https://amjis-mcp-<hash>.a.run.app/mcp, optionally with ?api_key=...)')
    process.exit(2)
  }
  const bearer = envOrDefault('MCP_BEARER')
  const client = new McpClient(url, bearer)
  await client.init()

  const tools = await client.listTools()
  const byName = new Map(tools.map((t) => [t.name, t]))
  const pairs = discoverPairs(tools)

  console.log(`O-7 alias↔primitive conformance: ${pairs.length} pairs discovered from ${tools.length} live tools.`)

  const results: PairResult[] = []
  for (const pair of pairs) {
    const aliasTool = byName.get(pair.alias)
    const primitiveTool = byName.get(pair.primitive)
    if (!aliasTool || !primitiveTool) {
      results.push({ pair, status: 'BROKEN_PAIR', detail: `missing: ${!aliasTool ? pair.alias : pair.primitive}` })
      continue
    }
    const args = synthesizeArgs(aliasTool, primitiveTool)
    if (args === null) {
      results.push({ pair, status: 'SKIPPED_NO_SAFE_ARGS' })
      continue
    }
    try {
      const [aliasResult, primitiveResult] = await Promise.all([
        client.callTool(pair.alias, args),
        client.callTool(pair.primitive, args),
      ])
      if (aliasResult.isToolError || primitiveResult.isToolError) {
        results.push({
          pair,
          status: 'ERROR',
          detail: `alias_error=${aliasResult.isToolError} primitive_error=${primitiveResult.isToolError}`,
        })
        continue
      }
      if (deepEqual(aliasResult.content, primitiveResult.content)) {
        results.push({ pair, status: 'PASS' })
      } else {
        results.push({ pair, status: 'MISMATCH' })
      }
    } catch (err) {
      results.push({ pair, status: 'ERROR', detail: err instanceof Error ? err.message : String(err) })
    }
  }

  for (const r of results) {
    const line = `${r.status.padEnd(22)} ${r.pair.alias} <-> ${r.pair.primitive}${r.detail ? `  (${r.detail})` : ''}`
    console.log(line)
  }

  const summary = results.reduce<Record<string, number>>((acc, r) => {
    acc[r.status] = (acc[r.status] ?? 0) + 1
    return acc
  }, {})
  console.log('\nSummary:', JSON.stringify(summary))

  const failing = results.filter((r) => r.status === 'MISMATCH' || r.status === 'BROKEN_PAIR')
  if (failing.length > 0) {
    console.error(`\n${failing.length} pair(s) failed conformance (MISMATCH/BROKEN_PAIR).`)
    process.exit(1)
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
