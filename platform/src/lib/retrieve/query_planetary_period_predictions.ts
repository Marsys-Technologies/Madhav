/**
 * MARSYS-JIS Retrieval tool — query_planetary_period_predictions (UDA-1-S4)
 *
 * Classical MD/AD prediction recipes via vector_search + classical text merge.
 *
 * What it does: Retrieves classical shastra predictions for MD/AD planetary period
 * combinations by composing vector_search + classical_text_search_tool primitives.
 * Deduplicates results by chunk_id (higher relevance_score wins), filters by
 * maha_dasha_lord presence in content, derives school from text_id.
 *
 * Algorithm:
 *   1. Build query: "${maha_dasha_lord} dasha ${antar_dasha_lord} predictions effects results"
 *   2. Call vector_search(query, top_k=15) for semantic similarity.
 *   3. Call classical_text_search(query, limit=15) for keyword-ranked classical chunks.
 *   4. Merge + deduplicate by chunk_id; prefer higher relevance_score.
 *   5. Filter: only chunks where content contains maha_dasha_lord (case-insensitive).
 *   6. Apply optional text_ids filter.
 *   7. Sort by relevance_score descending; return top max_results.
 *   8. Derive school from text_id.
 *
 * Ported from: platform-mcp/src/tools/query_planetary_period_predictions.ts
 * Session: UDA-1-S4
 */

import crypto from 'crypto'
import { classical_text_search } from '@/lib/tools/classical_text_search'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool as vectorSearchTool } from './vector_search'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_planetary_period_predictions'
const TOOL_VERSION = '1.0.0'

// ── School derivation map ─────────────────────────────────────────────────────

const TEXT_ID_TO_SCHOOL: Record<string, string> = {
  BPHS: 'Parashari',
  JAIMINI_SUTRAM: 'Jaimini',
  KP_READER: 'KP',
  TAJAKA_NEELAKANTHI: 'Tajaka',
  PHALADEEPIKA: 'Parashari',
  BRIHAT_JATAKA: 'Parashari',
}

const CLASSICAL_SOURCES = ['BPHS', 'JAIMINI_SUTRAM', 'KP_READER', 'TAJAKA_NEELAKANTHI', 'PHALADEEPIKA']

// ── Input type ────────────────────────────────────────────────────────────────

export interface QueryPlanetaryPeriodPredictionsInput {
  /** The Mahadasha planet lord (e.g. "Rahu", "Jupiter", "Saturn"). Required. */
  maha_dasha_lord: string
  /** The Antardasha planet lord. When supplied, targets the MD/AD combination. */
  antar_dasha_lord?: string
  /** Filter to specific classical texts by text_id (e.g. ["BPHS", "KP_READER"]). */
  text_ids?: string[]
  /** Maximum number of results to return after dedup and filtering (1–20, default 10). */
  max_results?: number
}

// ── Internal chunk type ───────────────────────────────────────────────────────

interface PredictionChunk {
  chunk_id: string
  text_id: string
  chapter: number | null
  verse: number | null
  content: string
  relevance_score: number
  school: string
}

// ── School derivation ─────────────────────────────────────────────────────────

function deriveSchool(textId: string, existingSchool?: string): string {
  if (existingSchool && existingSchool.trim().length > 0) return existingSchool
  const normalized = textId.toUpperCase()
  return TEXT_ID_TO_SCHOOL[normalized] ?? 'Unknown'
}

// ── Extract chunks from vector_search ToolBundle ──────────────────────────────

function extractFromVectorBundle(bundle: ToolBundle): Map<string, PredictionChunk> {
  const result = new Map<string, PredictionChunk>()
  for (const r of bundle.results) {
    // vector_search encodes content as "text\n\n[Source: file | Layer: layer]"
    // signal_id holds the chunk_id; source_canonical_id holds doc_type
    const chunkId = r.signal_id ?? `v-${r.source_canonical_id}-${r.content.slice(0, 40)}`
    const textId = (r.source_canonical_id ?? 'UNKNOWN').toUpperCase()
    const content = r.content
    const score = r.confidence ?? 0

    result.set(chunkId, {
      chunk_id: chunkId,
      text_id: textId,
      chapter: null,
      verse: null,
      content,
      relevance_score: score,
      school: deriveSchool(textId),
    })
  }
  return result
}

// ── Extract chunks from classical_text_search output ─────────────────────────

function extractFromClassicalResults(
  classicalResults: Awaited<ReturnType<typeof classical_text_search>>['results'],
): Map<string, PredictionChunk> {
  const result = new Map<string, PredictionChunk>()
  for (const r of classicalResults) {
    const chunkId = r.chunk_id
    const textId = (r.text_key ?? 'UNKNOWN').toUpperCase()
    const content = r.content
    const score = r.confidence_baseline ?? r.similarity ?? 0.5

    result.set(chunkId, {
      chunk_id: chunkId,
      text_id: textId,
      chapter: r.chapter ? Number(r.chapter) : null,
      verse: r.verse_range ? Number(r.verse_range.split('-')[0]) : null,
      content,
      relevance_score: score,
      school: deriveSchool(textId, r.tradition),
    })
  }
  return result
}

// ── Merge + deduplicate ───────────────────────────────────────────────────────
// Vector results take precedence on relevance_score; classical results fill gaps.

function mergeAndDeduplicate(
  vectorChunks: Map<string, PredictionChunk>,
  classicalChunks: Map<string, PredictionChunk>,
): PredictionChunk[] {
  const merged = new Map<string, PredictionChunk>(vectorChunks)

  for (const [id, chunk] of classicalChunks) {
    if (!merged.has(id)) {
      merged.set(id, chunk)
    } else {
      const existing = merged.get(id)!
      if (chunk.relevance_score > existing.relevance_score) {
        merged.set(id, chunk)
      }
    }
  }

  return Array.from(merged.values())
}

// ── Synthetic QueryPlan factory ───────────────────────────────────────────────

function makeSyntheticPlan(queryText: string): QueryPlan {
  return {
    query_plan_id: crypto.randomUUID(),
    query_text: queryText,
    query_class: 'classical_grounding',
    domains: ['dasha'],
    forward_looking: false,
    audience_tier: 'acharya_reviewer',
    tools_authorized: ['vector_search', 'classical_text_search'],
    history_mode: 'research',
    panel_mode: false,
    expected_output_shape: 'single_answer',
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
      data_asset_id: 'RAG_CHUNKS',
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
  const input = (params ?? {}) as unknown as QueryPlanetaryPeriodPredictionsInput
  const { maha_dasha_lord, antar_dasha_lord, text_ids } = input
  const max_results = input.max_results ?? 10

  if (!maha_dasha_lord) {
    throw new Error('query_planetary_period_predictions: maha_dasha_lord is required')
  }

  // ── Build search query ──────────────────────────────────────────────────────
  const query = [
    maha_dasha_lord,
    'dasha',
    antar_dasha_lord ?? '',
    'predictions effects results',
  ]
    .join(' ')
    .replace(/\s{2,}/g, ' ')
    .trim()

  // ── Synthetic plan for vector_search ───────────────────────────────────────
  const syntheticPlan = makeSyntheticPlan(query)

  // ── Parallel retrieval ──────────────────────────────────────────────────────
  const [vectorBundle, classicalOutput] = await Promise.all([
    vectorSearchTool.retrieve(syntheticPlan, { text: query, top_k: 15 }).catch(() => null),
    classical_text_search({ query, limit: 15 }).catch(() => null),
  ])

  // ── Extract chunks (graceful on error) ─────────────────────────────────────
  const vectorChunks: Map<string, PredictionChunk> =
    vectorBundle ? extractFromVectorBundle(vectorBundle) : new Map()

  const classicalChunks: Map<string, PredictionChunk> =
    classicalOutput ? extractFromClassicalResults(classicalOutput.results) : new Map()

  // ── Merge + deduplicate ─────────────────────────────────────────────────────
  let merged = mergeAndDeduplicate(vectorChunks, classicalChunks)

  // ── Filter: content must contain maha_dasha_lord ────────────────────────────
  const mahaLower = maha_dasha_lord.toLowerCase()
  merged = merged.filter(chunk => chunk.content.toLowerCase().includes(mahaLower))

  // ── Apply text_ids filter if specified ──────────────────────────────────────
  if (text_ids && text_ids.length > 0) {
    const textIdSet = new Set(text_ids.map(id => id.toUpperCase()))
    merged = merged.filter(chunk => textIdSet.has(chunk.text_id))
  }

  // ── Sort by relevance_score descending, take top max_results ────────────────
  merged.sort((a, b) => b.relevance_score - a.relevance_score)
  const topResults = merged.slice(0, max_results)

  // ── Build ToolBundle results ────────────────────────────────────────────────
  const sourcesSearched = text_ids ?? CLASSICAL_SOURCES

  const results: ToolBundleResult[] = topResults.map(chunk => ({
    content: JSON.stringify({
      text_id: chunk.text_id,
      chapter: chunk.chapter,
      verse: chunk.verse,
      content: chunk.content,
      relevance_score: chunk.relevance_score,
      school: chunk.school,
    }),
    source_canonical_id: chunk.text_id,
    source_version: '1.0',
    confidence: chunk.relevance_score,
    signal_id: chunk.chunk_id,
  }))

  // Wrap in envelope for consistency with MCP response shape
  const envelopeContent: ToolBundleResult = {
    content: JSON.stringify({
      ok: true,
      maha_dasha_lord,
      antar_dasha_lord: antar_dasha_lord ?? null,
      results: topResults,
      result_count: topResults.length,
      sources_searched: sourcesSearched,
    }),
    source_canonical_id: 'CLASSICAL_CORPUS',
    source_version: '1.0',
    confidence: topResults.length > 0 ? topResults[0].relevance_score : 0,
  }

  const finalResults = results.length > 0 ? results : [envelopeContent]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(finalResults.map(r => r.signal_id ?? r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: params ?? {},
    results: finalResults,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: (params ?? {}) as Record<string, unknown>,
    status: finalResults.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: finalResults.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(finalResults).length / 4),
    data_asset_id: 'RAG_CHUNKS',
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
    'Classical MD/AD prediction recipes: retrieves classical shastra predictions for ' +
    'planetary period (Mahadasha/Antardasha) combinations by composing vector_search + ' +
    'classical_text_search. Deduplicates by chunk_id, filters by maha_dasha_lord presence, ' +
    'derives school from text_id. Returns ranked excerpts from BPHS, Jaimini Sutram, ' +
    'KP Reader, Tajaka Neelakanthi, Phaladeepika with relevance scores. ' +
    'Use when you need classical textual authority on what a specific MD or MD/AD ' +
    'combination portends. Prefer holistic_bundle for full MSR synthesis.',
  retrieve,
}
