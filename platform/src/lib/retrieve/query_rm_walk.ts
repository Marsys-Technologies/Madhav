/**
 * MARSYS-JIS Retrieval tool — query_rm_walk (COV-S5)
 *
 * File-based walk over the Resonance Map (RM_v2_0.md).
 * Parses RM element blocks (RM.01–RM.35) and returns structured
 * resonance entries. When seed_signal_id is provided, returns only
 * entries whose msr_anchors list contains that signal ID. Full-dump
 * mode (no params) returns all 35 RM element blocks.
 *
 * Each RM element block is a YAML-in-markdown block introduced by
 * "### RM.NN — <name>" and containing a ```yaml ... ``` fence.
 *
 * Data source: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md (canonical_id: RM)
 * canonical_id: RM_WALK_TOOL
 */

import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_rm_walk'
const TOOL_VERSION = '1.0.0'

const RM_PATH = path.resolve(
  __dirname,
  '../../../../025_HOLISTIC_SYNTHESIS/RM_v2_0.md'
)

export interface QueryRmWalkInput {
  seed_signal_id?: string
  depth?: number
}

// ---------------------------------------------------------------------------
// Parse RM markdown into structured entries
// ---------------------------------------------------------------------------

interface RmEntry {
  rm_id: string
  signal_id: string
  resonance_type: string
  strength: string
  domains: string[]
  msr_anchors: string[]
  net_resonance: string
}

/**
 * Parse RM_v2_0.md element blocks.
 *
 * Block format:
 *   ### RM.NN — <element name>
 *   ```yaml
 *   element: "..."
 *   domains_primary: [D1, D2, ...]
 *   msr_anchors: [MSR.413, ...]
 *   net_resonance: "..."
 *   ...
 *   ```
 *
 * Returns all entries in full-dump mode, or only those whose msr_anchors
 * contain seed_signal_id in seeded mode.
 */
function parseRm(seedSignalId?: string): RmEntry[] {
  const raw = fs.readFileSync(RM_PATH, 'utf-8')
  const lines = raw.split('\n')

  const entries: RmEntry[] = []

  let rmId = ''
  let elementName = ''
  let inYaml = false
  let domains: string[] = []
  let msrAnchors: string[] = []
  let netResonance = ''

  const flushEntry = () => {
    if (!rmId) return
    const entry: RmEntry = {
      rm_id: rmId,
      // Use the RM ID itself as the primary signal_id for indexing
      signal_id: rmId,
      resonance_type: elementName,
      // Derive strength from net_resonance text: STRONGLY AMPLIFIED > AMPLIFIED > TENSION-BEARING > NEUTRAL
      strength: inferStrength(netResonance),
      domains,
      msr_anchors: msrAnchors,
      net_resonance: netResonance,
    }
    entries.push(entry)
    rmId = ''
    elementName = ''
    inYaml = false
    domains = []
    msrAnchors = []
    netResonance = ''
  }

  // RM element header: "### RM.01 — Mercury 10H Capricorn ..."
  const rmHeader = /^###\s+(RM\.\d+)\s*[—–-]\s*(.+)/

  for (const line of lines) {
    const headerMatch = rmHeader.exec(line)
    if (headerMatch) {
      flushEntry()
      rmId = headerMatch[1]
      elementName = headerMatch[2].trim()
      continue
    }

    if (!rmId) continue

    // YAML fence toggles
    if (line.trim() === '```yaml') { inYaml = true; continue }
    if (line.trim() === '```') { inYaml = false; continue }

    if (!inYaml) continue

    const trimmed = line.trim()

    // domains_primary: [D1, D2, D3, D8, D9]
    const domainsMatch = /^domains_primary:\s*\[(.+)\]/.exec(trimmed)
    if (domainsMatch) {
      domains = domainsMatch[1].split(',').map((s) => s.trim()).filter(Boolean)
      continue
    }

    // msr_anchors: [MSR.413, MSR.190]
    const anchorsMatch = /^msr_anchors:\s*\[(.+)\]/.exec(trimmed)
    if (anchorsMatch) {
      msrAnchors = anchorsMatch[1]
        .split(',')
        .map((s) => s.trim().replace(/^["']|["']$/g, '').split('(')[0].trim())
        .filter(Boolean)
      continue
    }

    // net_resonance: "STRONGLY AMPLIFIED ..."
    const netMatch = /^net_resonance:\s*"?(.+?)"?\s*$/.exec(trimmed)
    if (netMatch) {
      netResonance = netMatch[1].trim()
      continue
    }
  }

  // Flush the last entry
  flushEntry()

  // Filter by seed_signal_id if provided
  if (seedSignalId) {
    return entries.filter(
      (e) =>
        e.rm_id === seedSignalId ||
        e.msr_anchors.includes(seedSignalId)
    )
  }

  return entries
}

function inferStrength(netResonance: string): string {
  const upper = netResonance.toUpperCase()
  if (upper.includes('STRONGLY AMPLIFIED')) return 'STRONGLY_AMPLIFIED'
  if (upper.includes('AMPLIFIED')) return 'AMPLIFIED'
  if (upper.includes('TENSION')) return 'TENSION_BEARING'
  if (upper.includes('BENEFIC')) return 'BENEFIC'
  return 'MODERATE'
}

// ---------------------------------------------------------------------------
// Core retrieve function
// ---------------------------------------------------------------------------

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'RM',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as QueryRmWalkInput
  const seedSignalId = input.seed_signal_id?.trim() || undefined

  const rmEntries = parseRm(seedSignalId)

  const results: ToolBundleResult[] = rmEntries.map((entry) => ({
    content: JSON.stringify(entry),
    source_canonical_id: 'RM',
    source_version: '2.2',
    signal_id: entry.signal_id,
    confidence: 0.9,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map((r) => r.signal_id ?? r.content.slice(0, 50)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { seed_signal_id: seedSignalId ?? null },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: results.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: results.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'RM',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'RM walk — scans RM_v2_0.md (35 element blocks, Resonance Map) and returns resonance ' +
    'entries filtered by seed_signal_id (MSR.NNN anchor match) or all entries in full-dump mode. ' +
    'Input: { seed_signal_id?: string (e.g. "MSR.413" or "RM.01"), depth?: number (accepted, unused). } ' +
    'Returns: Array<{ rm_id, signal_id, resonance_type, strength, domains, msr_anchors, net_resonance }>. ' +
    'Use when a query asks about resonance patterns, net resonance classifications, or ' +
    'which RM elements are associated with a specific MSR signal.',
  retrieve,
}
