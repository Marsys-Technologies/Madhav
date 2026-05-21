/**
 * MARSYS-JIS Retrieval tool — query_ucn_walk (COV-S5)
 *
 * File-based walk over the Unified Chart Narrative (UCN_v4_0.md).
 * When seed_signal_id is provided, returns lines/sections containing
 * that signal ID. When called with no input (full-dump mode), returns
 * all extracted section/signal entries from the UCN.
 *
 * Implementation: reads UCN_v4_0.md at runtime using fs.readFileSync,
 * extracts section headers and MSR.NNN anchor references, and filters
 * by seed if provided. Depth parameter is accepted but unused in the
 * file-parse implementation (no graph edges in UCN; depth semantics
 * reserved for a future structured-table version).
 *
 * Data source: 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md (canonical_id: UCN)
 * canonical_id: UCN_WALK_TOOL
 */

import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_ucn_walk'
const TOOL_VERSION = '1.0.0'

// Resolve the UCN markdown file relative to the project root.
// In production (Cloud Run), __dirname is within /app/platform/src/lib/retrieve/.
// The markdown files live four levels up from this file: ../../../../025_HOLISTIC_SYNTHESIS/UCN_v4_0.md
const UCN_PATH = path.resolve(
  __dirname,
  '../../../../025_HOLISTIC_SYNTHESIS/UCN_v4_0.md'
)

export interface QueryUcnWalkInput {
  seed_signal_id?: string
  depth?: number
}

// ---------------------------------------------------------------------------
// Parse UCN markdown into structured entries
// ---------------------------------------------------------------------------

interface UcnEntry {
  signal_id: string
  confluence_type: string
  domain: string
}

/**
 * Parse UCN_v4_0.md and return a list of UcnEntry records.
 *
 * Strategy:
 *   1. Scan for MSR.NNN anchors (msr_anchors: [...] blocks or inline mentions).
 *   2. Capture the nearest section heading as the confluence_type.
 *   3. Infer domain from heading keywords (or use the heading as-is).
 *
 * Returns all entries in full-dump mode, or only entries whose signal_id
 * matches seed_signal_id in seeded mode.
 */
function parseUcn(seedSignalId?: string): UcnEntry[] {
  const raw = fs.readFileSync(UCN_PATH, 'utf-8')
  const lines = raw.split('\n')

  const entries: UcnEntry[] = []
  let currentSection = 'UCN_SECTION'

  // MSR.NNN pattern (e.g. MSR.413, MSR.391)
  const msrPattern = /MSR\.(\d+)/g

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Track section headings (## or ### prefixed lines)
    if (line.startsWith('##') || line.startsWith('###')) {
      currentSection = line.replace(/^#+\s*/, '').trim().slice(0, 80)
      continue
    }

    // Find all MSR signal references in this line
    let match: RegExpExecArray | null
    msrPattern.lastIndex = 0
    const found = new Set<string>()

    while ((match = msrPattern.exec(line)) !== null) {
      found.add(`MSR.${match[1]}`)
    }

    for (const signalId of found) {
      if (seedSignalId && signalId !== seedSignalId) continue

      // Infer domain from section name using keyword mapping
      const domain = inferDomainFromSection(currentSection)

      entries.push({
        signal_id: signalId,
        confluence_type: currentSection,
        domain,
      })
    }
  }

  // De-duplicate: keep first occurrence per (signal_id, confluence_type) pair
  const seen = new Set<string>()
  const deduped: UcnEntry[] = []
  for (const e of entries) {
    const key = `${e.signal_id}::${e.confluence_type}`
    if (!seen.has(key)) {
      seen.add(key)
      deduped.push(e)
    }
  }

  return deduped
}

const DOMAIN_KEYWORDS: Array<[RegExp, string]> = [
  [/career|10H|profession|work/i, 'D1_Career'],
  [/wealth|2H|11H|gain|money|finance/i, 'D2_Wealth'],
  [/relation|7H|partner|marr|spouse/i, 'D3_Relationships'],
  [/health|6H|8H|disease|illness/i, 'D4_Health'],
  [/child|5H|progeny/i, 'D5_Children'],
  [/spirit|9H|12H|dharma|moksha|soul/i, 'D6_Spirit'],
  [/parent|father|mother|4H|9H.*parent/i, 'D7_Parents'],
  [/mind|4H|mental|intellect|moon/i, 'D8_Mind'],
  [/travel|foreign|12H|abroad/i, 'D9_Travel'],
]

function inferDomainFromSection(section: string): string {
  for (const [regex, domain] of DOMAIN_KEYWORDS) {
    if (regex.test(section)) return domain
  }
  return 'General'
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
      data_asset_id: 'UCN',
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
  const input = (params ?? {}) as QueryUcnWalkInput
  const seedSignalId = input.seed_signal_id?.trim() || undefined

  const ucnEntries = parseUcn(seedSignalId)

  const results: ToolBundleResult[] = ucnEntries.map((entry) => ({
    content: JSON.stringify(entry),
    source_canonical_id: 'UCN',
    source_version: '4.1',
    signal_id: entry.signal_id,
    confidence: 0.85,
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
    data_asset_id: 'UCN',
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
    'UCN walk — scans UCN_v4_0.md for signal references near a seed signal ID or returns ' +
    'all signal-section associations in full-dump mode. ' +
    'Input: { seed_signal_id?: string (e.g. "MSR.413"), depth?: number (accepted, unused). } ' +
    'Returns: Array<{ signal_id, confluence_type (section heading), domain }>. ' +
    'Use when a query asks for the UCN narrative context around a specific MSR signal or ' +
    'to enumerate which UCN sections reference a particular signal.',
  retrieve,
}
