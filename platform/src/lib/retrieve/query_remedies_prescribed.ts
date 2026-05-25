/**
 * MARSYS-JIS Retrieval tool — query_remedies_prescribed (UDA-1-S7)
 *
 * Cross-references natal chart conditions with the MARSYS remedial codex.
 *
 * Algorithm:
 *   1. Build composite search query from affliction/planet/house/condition params.
 *   2. Call remedial_codex_query (portal tool) for remedy matches.
 *   3. Optionally enrich with chart_facts remedy/strength rows for the planet.
 *   4. Detect remedy_type from content keywords (mantra/gem/ritual/charity).
 *   5. Filter by remedy_type if not "all". Return top 10 structured results.
 *
 * Keyword → remedy_type detection:
 *   "mantra"|"japa"|"stotra" → mantra
 *   "gem"|"gemstone"|"ratna" → gem
 *   "ritual"|"puja"|"homa"|"yagna"|"yajna" → ritual
 *   "donate"|"charity"|"daan"|"dana" → charity
 *   (no match) → unknown
 *
 * Ported from: platform-mcp/src/tools/query_remedies_prescribed.ts (TR-P8-S2)
 * Session: UDA-1-S7
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool as remedialCodexQueryTool } from './remedial_codex_query'
import { tool as chartFactsQueryTool } from './chart_facts_query'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_remedies_prescribed'
const TOOL_VERSION = '1.0.0'

// ── Input interface ────────────────────────────────────────────────────────────

export interface QueryRemediesPrescribedInput {
  /** Description of the affliction or astrological condition requiring remedy. */
  affliction?: string
  /** Planet name for which to retrieve remedies, e.g. "Saturn", "Rahu". */
  planet?: string
  /** Afflicted or relevant house number (1–12). */
  house?: number
  /** Free-text condition query for RAG search. */
  condition?: string
  /** Filter results by remedy type. "all" returns all types. Default: "all". */
  remedy_type?: 'mantra' | 'gem' | 'ritual' | 'charity' | 'all'
}

// ── Types ─────────────────────────────────────────────────────────────────────

type RemedyType = 'mantra' | 'gem' | 'ritual' | 'charity' | 'unknown'

interface RemedyResult {
  condition: string
  remedy_type: RemedyType
  remedy_text: string
  timing: string | null
  classical_source: string | null
  relevance_score: number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Detect remedy type from content string using keyword matching.
 * Priority order: mantra, gem/ratna, ritual/puja/homa, charity/daan.
 */
function detectRemedyType(content: string): RemedyType {
  const lower = content.toLowerCase()
  if (lower.includes('mantra') || lower.includes('japa') || lower.includes('stotra')) {
    return 'mantra'
  }
  if (lower.includes('gem') || lower.includes('gemstone') || lower.includes('ratna')) {
    return 'gem'
  }
  if (lower.includes('ritual') || lower.includes('puja') || lower.includes('homa') ||
      lower.includes('yagna') || lower.includes('yajna')) {
    return 'ritual'
  }
  if (lower.includes('donate') || lower.includes('charity') || lower.includes('daan') ||
      lower.includes('dana')) {
    return 'charity'
  }
  return 'unknown'
}

/**
 * Extract a string field from a row object, trying multiple field name aliases.
 */
function extractStr(row: Record<string, unknown>, ...fields: string[]): string | null {
  for (const f of fields) {
    const v = row[f]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return null
}

/**
 * Unwrap the bundle's result data, supporting both ToolBundle JSON-string and direct shapes.
 */
function unwrapBundleResult(bundle: ToolBundle): unknown {
  if (bundle.results.length === 0) return null
  const first = bundle.results[0]!
  if (typeof first.content === 'string') {
    try { return JSON.parse(first.content) } catch { /* fall through */ }
    return first.content
  }
  return first.content
}

/**
 * Extract remedy chunks from a ToolBundle by iterating all results.
 * Each result content is a JSON string with { content, doc_type, chunk_id }.
 */
function extractRemedyChunksFromBundle(bundle: ToolBundle): unknown[] {
  const chunks: unknown[] = []
  for (const r of bundle.results) {
    try {
      const parsed = JSON.parse(r.content) as Record<string, unknown>
      if (parsed) chunks.push(parsed)
    } catch {
      // skip malformed
    }
  }
  return chunks
}

/**
 * Extract chart_facts remedy/strength rows from a ToolBundle.
 */
function extractChartFactsRemedyRows(bundle: ToolBundle): unknown[] {
  const rows: unknown[] = []
  for (const r of bundle.results) {
    try {
      const parsed = JSON.parse(r.content) as Record<string, unknown>
      const cat = parsed['category'] as string | undefined
      if (cat === 'remedy' || cat === 'strength' || cat === 'weakness') {
        rows.push(parsed)
      } else {
        // Include all rows — chart_facts_query already filters by categories param
        rows.push(parsed)
      }
    } catch {
      // skip malformed
    }
  }
  return rows
}

/**
 * Convert a raw chunk/row into a RemedyResult.
 */
function rowToRemedyResult(
  row: Record<string, unknown>,
  idx: number,
  totalCount: number,
): RemedyResult {
  const content = extractStr(row, 'content', 'text', 'value_text', 'description') ?? ''
  const remedyType = detectRemedyType(content)

  const conditionLabel =
    extractStr(row, 'condition', 'affliction', 'planet', 'category_detail', 'yoga_name') ??
    extractStr(row, 'category', 'doc_type') ??
    'remedial prescription'

  const timing =
    extractStr(row, 'timing', 'time', 'muhurta', 'when') ?? null

  const classicalSource =
    extractStr(row, 'classical_source', 'source', 'chunk_id', 'text_id', 'text_key') ?? null

  let relevanceScore: number
  const simVal = row['similarity'] ?? row['score'] ?? row['relevance_score']
  if (typeof simVal === 'number' && simVal >= 0 && simVal <= 1) {
    relevanceScore = Math.round(simVal * 100) / 100
  } else {
    // Positional decay: first result = 0.95, decays by 0.05 per rank, floor 0.50
    relevanceScore = Math.max(0.5, 0.95 - idx * (0.45 / Math.max(totalCount - 1, 1)))
    relevanceScore = Math.round(relevanceScore * 100) / 100
  }

  return {
    condition: conditionLabel,
    remedy_type: remedyType,
    remedy_text: content || 'No remedy text available',
    timing,
    classical_source: classicalSource,
    relevance_score: relevanceScore,
  }
}

// ── Synthetic QueryPlan factory ───────────────────────────────────────────────

function makeSyntheticPlan(toolsAuthorized: string[]): QueryPlan {
  return {
    query_plan_id: crypto.randomUUID(),
    query_text: 'remedial prescription cross-reference',
    query_class: 'remedial',
    domains: ['remedial'],
    forward_looking: false,
    audience_tier: 'acharya_reviewer',
    tools_authorized: toolsAuthorized,
    history_mode: 'research',
    panel_mode: false,
    expected_output_shape: 'structured_data',
    manifest_fingerprint: 'synthetic',
    schema_version: '1.0',
  }
}

// ── Core retrieval ────────────────────────────────────────────────────────────

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
      data_asset_id: 'REMEDIAL_CODEX_v2_0',
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
  const input = (params ?? {}) as unknown as QueryRemediesPrescribedInput

  // ── Step 1: Build composite search query ─────────────────────────────────────
  const queryParts: string[] = []
  if (input.affliction) queryParts.push(input.affliction)
  if (input.planet) queryParts.push(input.planet)
  if (input.house !== undefined) queryParts.push(`house ${input.house}`)
  if (input.condition) queryParts.push(input.condition)
  queryParts.push('remedy mantra gem')
  const afflictionQuery = queryParts.join(' ').trim()

  // ── Step 2: Call remedial_codex_query ─────────────────────────────────────────
  const remedialParams: Record<string, unknown> = { limit: 12 }
  if (input.planet) remedialParams['planet'] = input.planet
  if (input.house !== undefined || input.affliction || input.condition) {
    const keywordParts: string[] = []
    if (input.house !== undefined) keywordParts.push(`house ${input.house}`)
    if (input.affliction) keywordParts.push(input.affliction)
    if (input.condition) keywordParts.push(input.condition)
    if (keywordParts.length > 0) {
      remedialParams['keyword'] = keywordParts.join(' ')
    }
  }

  const syntheticRemedialPlan = makeSyntheticPlan(['remedial_codex_query'])
  const remedialBundle = await remedialCodexQueryTool.retrieve(syntheticRemedialPlan, remedialParams)

  // ── Step 3: Optionally fetch chart_facts remedy/strength rows for planet ──────
  let chartFactsRows: unknown[] = []
  if (input.planet) {
    try {
      const syntheticCfPlan = makeSyntheticPlan(['chart_facts_query'])
      const cfBundle = await chartFactsQueryTool.retrieve(syntheticCfPlan, {
        categories: ['remedy', 'strength'],
        planet: input.planet,
        limit: 5,
      })
      chartFactsRows = extractChartFactsRemedyRows(cfBundle)
    } catch {
      // chart_facts enrichment is optional — swallow errors
    }
  }

  // ── Step 4: Merge and convert raw results ─────────────────────────────────────
  const remedialChunks = extractRemedyChunksFromBundle(remedialBundle)
  const allRawRows = [...remedialChunks, ...chartFactsRows]

  // ── Step 5: Convert to RemedyResult structs and detect remedy_type ────────────
  const allResults: RemedyResult[] = allRawRows
    .filter(r => r && typeof r === 'object')
    .map((r, idx) =>
      rowToRemedyResult(r as Record<string, unknown>, idx, allRawRows.length),
    )

  // ── Step 6: Filter by remedy_type if not "all" ────────────────────────────────
  const remedyTypeFilter = input.remedy_type ?? 'all'
  const filtered =
    remedyTypeFilter === 'all'
      ? allResults
      : allResults.filter(r => r.remedy_type === remedyTypeFilter)

  // ── Step 7: Return top 10 ─────────────────────────────────────────────────────
  const top10 = filtered.slice(0, 10)

  const resultContent = JSON.stringify({
    ok: true,
    affliction_query: afflictionQuery,
    results: top10,
    result_count: top10.length,
    epistemics: { surgical: true },
  })

  const results: ToolBundleResult[] = [{
    content: resultContent,
    source_canonical_id: 'REMEDIAL_CODEX_v2_0',
    confidence: 0.9,
    significance: 0.85,
  }]

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
    invocation_params: params ?? {},
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: (params ?? {}) as Record<string, unknown>,
    status: 'success',
    rows_returned: top10.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'REMEDIAL_CODEX_v2_0',
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
    'Cross-references natal chart conditions with the MARSYS remedial codex. ' +
    'Accepts affliction description, planet name, house number, free-text condition, ' +
    'and remedy_type filter ("mantra", "gem", "ritual", "charity", "all"). ' +
    'Retrieves L4 remedial prescriptions from the rag_chunks corpus and optionally ' +
    'chart_facts remedy/strength rows for the planet. Detects remedy_type from ' +
    'content keywords (mantra/gem/gemstone/ratna/ritual/puja/homa/donate/charity/daan). ' +
    'Returns up to 10 structured results with condition, remedy_type, remedy_text, ' +
    'timing, classical_source, and relevance_score. ' +
    'Use when the native needs planetary propitiation or remedial protocol recommendations.',
  retrieve,
}
