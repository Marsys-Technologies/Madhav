/**
 * MARSYS-JIS Retrieval Tool: query_cdlm_lookup (COV-S5)
 *
 * Looks up a specific domain-pair cell in CDLM_v1_1.md — the Cross-Domain
 * Linkage Matrix. The CDLM maps structural interdependencies between the 9
 * life domains (D1–D9).
 *
 * WHY THIS TOOL EXISTS:
 *   - The CDLM has an 81-cell structure (9×9 domain pairs) with YAML-style
 *     cells labelled CDLM.D{from}.D{to}.
 *   - vector_search cannot reliably extract a specific cell by domain-pair ID.
 *   - query_cdlm_lookup provides direct cell extraction by domain name or Dx ID.
 *   - Use when the query involves cross-domain questions (e.g., how career
 *     affects health, how wealth affects relationships).
 */

import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_cdlm_lookup'
const TOOL_VERSION = '1.0.0'
// Resolve relative to repo root (one level up from the platform/ Next.js app dir)
const REPO_ROOT = path.resolve(process.cwd(), '..')
const CDLM_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md')

export interface CdlmLookupInput {
  /** Source domain ID: 'D1'..'D9' or a domain name like 'career', 'wealth' */
  domain_from: string
  /** Target domain ID: 'D1'..'D9' or a domain name like 'health', 'relationship' */
  domain_to: string
}

/** Map of domain names to Dx IDs */
const DOMAIN_NAME_MAP: Record<string, string> = {
  // D1 — Career
  career: 'D1',
  work: 'D1',
  profession: 'D1',
  // D2 — Wealth
  wealth: 'D2',
  finance: 'D2',
  money: 'D2',
  financial: 'D2',
  income: 'D2',
  // D3 — Communication/siblings/short-travel
  communication: 'D3',
  siblings: 'D3',
  'short-travel': 'D3',
  travel_short: 'D3',
  courage: 'D3',
  // D4 — Home/family/mother
  home: 'D4',
  family: 'D4',
  mother: 'D4',
  property: 'D4',
  // D5 — Creativity/children/intelligence
  creativity: 'D5',
  children: 'D5',
  intelligence: 'D5',
  education: 'D5',
  // D6 — Health/service/conflict
  health: 'D6',
  service: 'D6',
  conflict: 'D6',
  disease: 'D6',
  // D7 — Relationship/partnership
  relationship: 'D7',
  relationships: 'D7',
  partnership: 'D7',
  marriage: 'D7',
  spouse: 'D7',
  // D8 — Transformation/occult/longevity
  transformation: 'D8',
  occult: 'D8',
  longevity: 'D8',
  death: 'D8',
  mysticism: 'D8',
  // D9 — Dharma/spirituality/luck/long-travel
  dharma: 'D9',
  spirituality: 'D9',
  luck: 'D9',
  'long-travel': 'D9',
  travel_long: 'D9',
  fortune: 'D9',
  spirit: 'D9',
}

/** Resolve a domain string to its Dx ID */
function resolveDomain(input: string): string | null {
  const trimmed = input.trim()
  // Already in Dx format (case-insensitive)
  if (/^[Dd][1-9]$/.test(trimmed)) {
    return trimmed.toUpperCase()
  }
  // Look up by name
  const lower = trimmed.toLowerCase()
  return DOMAIN_NAME_MAP[lower] ?? null
}

/** Extract the CDLM cell content for a given cell label like "CDLM.D1.D2" */
function extractCdlmCell(content: string, cellLabel: string): string | null {
  // The cell label appears at the start of a line (no leading ###)
  // Pattern: "^CDLM.D1.D2:" at line start, then YAML block until next CDLM cell or blank line sequence
  const escapedLabel = cellLabel.replace(/\./g, '\\.')
  const cellPattern = new RegExp(`^${escapedLabel}:`, 'm')
  const match = cellPattern.exec(content)
  if (!match) return null

  const startIdx = match.index
  // Find the next cell label (starts with CDLM.D at line start) or end of section
  const afterStart = content.slice(startIdx)
  const nextCellMatch = /\nCDLM\.D\d\.D\d:/m.exec(afterStart.slice(1))
  const endIdx = nextCellMatch
    ? startIdx + 1 + nextCellMatch.index
    : Math.min(startIdx + 2000, content.length)

  return content.slice(startIdx, endIdx).trim()
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()

  const domain_from = (params?.domain_from as string | undefined) ?? ''
  const domain_to = (params?.domain_to as string | undefined) ?? ''

  const fromId = resolveDomain(domain_from)
  const toId = resolveDomain(domain_to)

  const results: ToolBundleResult[] = []

  if (fromId && toId) {
    const cellLabel = `CDLM.${fromId}.${toId}`
    const rawContent = fs.readFileSync(CDLM_PATH, 'utf-8')
    const cellContent = extractCdlmCell(rawContent, cellLabel)

    if (cellContent) {
      results.push({
        content: cellContent.slice(0, 1500),
        source_canonical_id: 'CDLM',
        source_version: '1.3',
        confidence: 1.0,
        significance: 0.9,
        signal_id: `cdlm_${fromId}_${toId}`,
      })
    }
  }

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { domain_from, domain_to, resolved_from: fromId, resolved_to: toId },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Looks up a specific domain-pair cell in the CDLM (Cross-Domain Linkage Matrix) — the L2.5 ' +
    'document mapping structural interdependencies between the 9 life domains. Use when the query ' +
    'involves cross-domain questions (e.g., how career affects health, how wealth affects relationships).',
  retrieve,
}
