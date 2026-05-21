/**
 * MARSYS-JIS Retrieval tool — query_cdlm_lookup (COV-S5)
 *
 * File-based lookup over the Cross-Domain Linkage Matrix (CDLM_v1_1.md).
 * Parses the 81-cell YAML-in-markdown CDLM structure and returns matching
 * linkage entries filtered by domain_a, domain_b, or signal_id.
 *
 * Full-dump mode (no params): returns all 81 cells.
 * Seeded mode: filters cells whose row_domain/col_domain match domain_a/
 * domain_b (case-insensitive prefix match), or whose msr_anchors contain
 * the given signal_id.
 *
 * Data source: 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md (canonical_id: CDLM)
 * canonical_id: CDLM_LOOKUP_TOOL
 */

import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_cdlm_lookup'
const TOOL_VERSION = '1.0.0'

const CDLM_PATH = path.resolve(
  __dirname,
  '../../../../025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md'
)

export interface QueryCdlmLookupInput {
  domain_a?: string
  domain_b?: string
  signal_id?: string
}

// ---------------------------------------------------------------------------
// Parse CDLM markdown into structured entries
// ---------------------------------------------------------------------------

interface CdlmEntry {
  domain_pair: string
  row_domain: string
  col_domain: string
  linkage_type: string
  strength: string
  direction: string
  valence: string
  signal_ids: string[]
  key_finding: string
}

/**
 * Parse CDLM_v1_1.md YAML-in-markdown cells.
 *
 * Each cell block starts with "CDLM.Dx.Dy:" and contains YAML-like lines.
 * We extract the key fields with line-by-line scanning.
 */
function parseCdlm(domainA?: string, domainB?: string, signalId?: string): CdlmEntry[] {
  const raw = fs.readFileSync(CDLM_PATH, 'utf-8')
  const lines = raw.split('\n')

  const entries: CdlmEntry[] = []
  let current: Partial<CdlmEntry> | null = null
  let signalIds: string[] = []

  const flushEntry = () => {
    if (current && current.row_domain && current.col_domain) {
      const entry: CdlmEntry = {
        domain_pair: `${current.row_domain}→${current.col_domain}`,
        row_domain: current.row_domain,
        col_domain: current.col_domain,
        linkage_type: current.linkage_type ?? '',
        strength: current.strength ?? '',
        direction: current.direction ?? '',
        valence: current.valence ?? '',
        signal_ids: signalIds,
        key_finding: current.key_finding ?? '',
      }
      entries.push(entry)
    }
    current = null
    signalIds = []
  }

  // CDLM cell header pattern: "CDLM.D1.D2:"
  const cellHeader = /^CDLM\.(D\d+)\.(D\d+):/

  for (const line of lines) {
    const headerMatch = cellHeader.exec(line.trim())
    if (headerMatch) {
      flushEntry()
      current = {}
      signalIds = []
      continue
    }

    if (!current) continue

    const trimmed = line.trim()

    // row_domain: Career
    const rowDomain = /^row_domain:\s*(.+)/.exec(trimmed)
    if (rowDomain) { current.row_domain = rowDomain[1].trim().replace(/^["']|["']$/g, ''); continue }

    // col_domain: Wealth
    const colDomain = /^col_domain:\s*(.+)/.exec(trimmed)
    if (colDomain) { current.col_domain = colDomain[1].trim().replace(/^["']|["']$/g, ''); continue }

    // linkage_type: feeds
    const linkageType = /^linkage_type:\s*(.+)/.exec(trimmed)
    if (linkageType) { current.linkage_type = linkageType[1].trim().replace(/^["']|["']$/g, ''); continue }

    // strength: 0.92
    const strength = /^strength:\s*(.+)/.exec(trimmed)
    if (strength) { current.strength = strength[1].trim(); continue }

    // direction: row→col
    const direction = /^direction:\s*(.+)/.exec(trimmed)
    if (direction) { current.direction = direction[1].trim().replace(/^["']|["']$/g, ''); continue }

    // valence: benefic
    const valence = /^valence:\s*(.+)/.exec(trimmed)
    if (valence) { current.valence = valence[1].trim().replace(/^["']|["']$/g, ''); continue }

    // key_finding: "..."
    const keyFinding = /^key_finding:\s*"?(.+?)"?\s*$/.exec(trimmed)
    if (keyFinding) { current.key_finding = keyFinding[1].trim(); continue }

    // msr_anchors: [MSR.413, MSR.264, MSR.311]
    const msrAnchors = /^msr_anchors:\s*\[(.+)\]/.exec(trimmed)
    if (msrAnchors) {
      signalIds = msrAnchors[1]
        .split(',')
        .map((s) => s.trim().replace(/^["']|["']$/g, ''))
        .filter(Boolean)
      continue
    }
  }

  // Flush the last entry
  flushEntry()

  // Filter
  return entries.filter((entry) => {
    if (domainA) {
      if (!entry.row_domain.toLowerCase().includes(domainA.toLowerCase())) return false
    }
    if (domainB) {
      if (!entry.col_domain.toLowerCase().includes(domainB.toLowerCase())) return false
    }
    if (signalId) {
      if (!entry.signal_ids.includes(signalId)) return false
    }
    return true
  })
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
      data_asset_id: 'CDLM',
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
  const input = (params ?? {}) as QueryCdlmLookupInput
  const domainA = input.domain_a?.trim() || undefined
  const domainB = input.domain_b?.trim() || undefined
  const signalId = input.signal_id?.trim() || undefined

  const cdlmEntries = parseCdlm(domainA, domainB, signalId)

  const results: ToolBundleResult[] = cdlmEntries.map((entry) => ({
    content: JSON.stringify(entry),
    source_canonical_id: 'CDLM',
    source_version: '1.3',
    signal_id: entry.signal_ids[0] ?? entry.domain_pair,
    confidence: entry.strength ? Number(entry.strength) : 0.8,
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
    invocation_params: {
      domain_a: domainA ?? null,
      domain_b: domainB ?? null,
      signal_id: signalId ?? null,
    },
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
    data_asset_id: 'CDLM',
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
    'CDLM lookup — parses CDLM_v1_1.md (81-cell cross-domain linkage matrix) and returns ' +
    'matching cells filtered by domain_a, domain_b, or signal_id. ' +
    'Input: { domain_a?: string (e.g. "Career"), domain_b?: string (e.g. "Wealth"), signal_id?: string (e.g. "MSR.413"). } ' +
    'Returns: Array<{ domain_pair, row_domain, col_domain, linkage_type, strength, direction, valence, signal_ids, key_finding }>. ' +
    'Full-dump mode (no params) returns all 81 cells. ' +
    'Use when a query asks about cross-domain interactions, linkage types, or which domains a signal bridges.',
  retrieve,
}
