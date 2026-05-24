/**
 * query_planetary_period_predictions.ts — MCP Tier 3 composition recipe:
 * classical curator over BPHS + Jaimini + KP + Tajaka + Phaladeepika rag_chunks.
 *
 * What it does: Retrieves classical shastra predictions for MD/AD planetary period
 * combinations by composing vector_search + read_classical_text primitives.
 * Deduplicates results by chunk_id (higher relevance_score wins), filters by
 * maha_dasha_lord presence in content, and derives school from text_id.
 *
 * Algorithm:
 *   1. Build query: "${maha_dasha_lord} dasha ${antar_dasha_lord} predictions effects results"
 *   2. Call vector_search(query, top_k=15) for semantic similarity.
 *   3. Call read_classical_text(query, limit=15) for keyword-ranked classical chunks.
 *   4. Merge + deduplicate by chunk_id; prefer higher relevance_score.
 *   5. Filter: only chunks where content contains maha_dasha_lord (case-insensitive).
 *   6. Sort by relevance_score descending; return top max_results.
 *   7. Derive school from text_id if not present.
 *
 * When to prefer: Use when you need classical textual authority on what a specific
 * MD/AD combination portends per BPHS, Jaimini, KP, Tajaka, or Phaladeepika.
 * Prefer holistic_bundle for full multi-layer MSR synthesis. Prefer vector_search
 * alone when you need cross-layer semantic results including MSR signals.
 *
 * Session: TR-P7-S3
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// ── School derivation map ─────────────────────────────────────────────────────
// Maps text_id (uppercase) to tradition/school name.

const TEXT_ID_TO_SCHOOL: Record<string, string> = {
  BPHS: 'Parashari',
  JAIMINI_SUTRAM: 'Jaimini',
  KP_READER: 'KP',
  TAJAKA_NEELAKANTHI: 'Tajaka',
  PHALADEEPIKA: 'Parashari',
  BRIHAT_JATAKA: 'Parashari',
}

const CLASSICAL_SOURCES = ['BPHS', 'JAIMINI_SUTRAM', 'KP_READER', 'TAJAKA_NEELAKANTHI', 'PHALADEEPIKA']

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_PLANETARY_PERIOD_PREDICTIONS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Retrieves classical shastra predictions for MD/AD planetary period ' +
    'combinations by composing vector_search + read_classical_text. Deduplicates results ' +
    'by chunk_id, filters by maha_dasha_lord in content, derives school from text_id. ' +
    'Returns ranked excerpts from BPHS, Jaimini Sutram, KP Reader, Tajaka Neelakanthi, ' +
    'Phaladeepika with relevance scores.',
  coverageHint: '14 classical texts, 8,349+ chunks; vector + keyword hybrid retrieval',
  whenToPrefer:
    'Use when you need classical textual authority on what a specific MD or MD/AD ' +
    'combination portends. Prefer holistic_bundle for full MSR synthesis. ' +
    'Prefer vector_search alone for cross-layer semantic results including MSR signals.',
})

// ── Input schema ──────────────────────────────────────────────────────────────

const QueryPlanetaryPeriodPredictionsInputSchema = z.object({
  maha_dasha_lord: z.string().describe(
    'The Mahadasha planet lord (e.g. "Rahu", "Jupiter", "Saturn"). Required.'
  ),
  antar_dasha_lord: z.string().optional().describe(
    'The Antardasha planet lord (e.g. "Jupiter"). When supplied, the query targets the MD/AD combination.'
  ),
  text_ids: z.array(z.string()).optional().describe(
    'Filter to specific classical texts by text_id (e.g. ["BPHS", "KP_READER"]). ' +
    'Defaults to all classical texts when omitted.'
  ),
  max_results: z.number().min(1).max(20).default(10).describe(
    'Maximum number of results to return after deduplication and filtering (1–20, default 10).'
  ),
  tier: z.string().optional().describe(
    'Audience tier for access control context. Informational only for this tool.'
  ),
})

type QueryPlanetaryPeriodPredictionsInput = z.infer<typeof QueryPlanetaryPeriodPredictionsInputSchema>

// ── Types ─────────────────────────────────────────────────────────────────────

interface PredictionResult {
  text_id: string
  chapter: number | null
  verse: number | null
  content: string
  relevance_score: number
  school: string
}

interface ChunkRecord {
  chunk_id?: string
  text_id?: string
  text_key?: string
  chapter?: number | null
  verse?: number | null
  content?: string
  text?: string
  score?: number
  relevance_score?: number
  school?: string
  [key: string]: unknown
}

// ── School derivation ─────────────────────────────────────────────────────────

function deriveSchool(textId: string, existingSchool?: string): string {
  if (existingSchool && existingSchool.trim().length > 0) return existingSchool
  const normalized = textId.toUpperCase()
  return TEXT_ID_TO_SCHOOL[normalized] ?? 'Unknown'
}

// ── Chunk extraction from platform response ───────────────────────────────────

function extractChunksFromVectorResult(envelope: unknown): Map<string, PredictionResult> {
  const result = new Map<string, PredictionResult>()
  if (!envelope || typeof envelope !== 'object') return result

  const env = envelope as Record<string, unknown>

  // Navigate to result/chunks
  const resultObj = (env['result'] as Record<string, unknown> | undefined) ?? env
  const chunks = (resultObj['chunks'] as ChunkRecord[] | undefined) ??
    (resultObj['results'] as ChunkRecord[] | undefined) ??
    (env['chunks'] as ChunkRecord[] | undefined) ?? []

  if (!Array.isArray(chunks)) return result

  for (const chunk of chunks) {
    const chunkId = String(chunk['chunk_id'] ?? `v-${chunk['text_id']}-${chunk['chapter']}-${chunk['verse']}`)
    const textId = String(chunk['text_id'] ?? chunk['text_key'] ?? 'UNKNOWN').toUpperCase()
    const content = String(chunk['content'] ?? chunk['text'] ?? '')
    const score = Number(chunk['score'] ?? chunk['relevance_score'] ?? 0)

    result.set(chunkId, {
      text_id: textId,
      chapter: chunk['chapter'] !== undefined ? Number(chunk['chapter']) : null,
      verse: chunk['verse'] !== undefined ? Number(chunk['verse']) : null,
      content,
      relevance_score: score,
      school: deriveSchool(textId, chunk['school'] as string | undefined),
    })
  }

  return result
}

function extractChunksFromClassicalResult(envelope: unknown): Map<string, PredictionResult> {
  const result = new Map<string, PredictionResult>()
  if (!envelope || typeof envelope !== 'object') return result

  const env = envelope as Record<string, unknown>

  // Platform returns envelope.result.results[] or envelope.result.chunks[]
  const resultObj = (env['result'] as Record<string, unknown> | undefined) ?? env
  const chunks = (resultObj['results'] as ChunkRecord[] | undefined) ??
    (resultObj['chunks'] as ChunkRecord[] | undefined) ??
    (env['results'] as ChunkRecord[] | undefined) ?? []

  if (!Array.isArray(chunks)) return result

  for (const chunk of chunks) {
    const chunkId = String(chunk['chunk_id'] ?? `c-${chunk['text_id']}-${chunk['chapter']}-${chunk['verse']}`)
    const textId = String(chunk['text_id'] ?? chunk['text_key'] ?? 'UNKNOWN').toUpperCase()
    const content = String(chunk['content'] ?? chunk['text'] ?? '')
    // classical results may not have a relevance_score; assign a moderate default
    const score = Number(chunk['score'] ?? chunk['relevance_score'] ?? 0.5)

    result.set(chunkId, {
      text_id: textId,
      chapter: chunk['chapter'] !== undefined ? Number(chunk['chapter']) : null,
      verse: chunk['verse'] !== undefined ? Number(chunk['verse']) : null,
      content,
      relevance_score: score,
      school: deriveSchool(textId, chunk['school'] as string | undefined),
    })
  }

  return result
}

// ── Merge + deduplicate ───────────────────────────────────────────────────────
// Vector results take precedence on relevance_score; classical results fill gaps.

function mergeAndDeduplicate(
  vectorChunks: Map<string, PredictionResult>,
  classicalChunks: Map<string, PredictionResult>,
): PredictionResult[] {
  const merged = new Map<string, PredictionResult>(vectorChunks)

  for (const [id, chunk] of classicalChunks) {
    if (!merged.has(id)) {
      // Novel chunk from classical search — add it
      merged.set(id, chunk)
    } else {
      // Duplicate: keep the one with higher relevance_score
      const existing = merged.get(id)!
      if (chunk.relevance_score > existing.relevance_score) {
        merged.set(id, chunk)
      }
    }
  }

  return Array.from(merged.values())
}

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerQueryPlanetaryPeriodPredictions(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_planetary_period_predictions',
    QUERY_PLANETARY_PERIOD_PREDICTIONS_DESCRIPTION,
    QueryPlanetaryPeriodPredictionsInputSchema.shape,
    async (args: QueryPlanetaryPeriodPredictionsInput) => {
      const principal = getPrincipal()
      const { maha_dasha_lord, antar_dasha_lord, max_results } = args

      // ── Build search query ──────────────────────────────────────────────────
      const query = [
        maha_dasha_lord,
        'dasha',
        antar_dasha_lord ?? '',
        'predictions effects results',
      ]
        .join(' ')
        .replace(/\s{2,}/g, ' ')
        .trim()

      // ── Parallel platform calls ─────────────────────────────────────────────
      const [vectorResult, classicalResult] = await Promise.all([
        callPlatformPrimitive(
          'vector_search',
          { text: query, top_k: 15 },
          principal,
        ),
        callPlatformPrimitive(
          'read_classical_text',
          { query, limit: 15 },
          principal,
        ),
      ])

      // ── Extract chunks (graceful on error) ──────────────────────────────────
      let vectorChunks = new Map<string, PredictionResult>()
      if (vectorResult.envelope.ok && vectorResult.status < 400) {
        vectorChunks = extractChunksFromVectorResult(vectorResult.envelope)
      }

      let classicalChunks = new Map<string, PredictionResult>()
      if (classicalResult.envelope.ok && classicalResult.status < 400) {
        classicalChunks = extractChunksFromClassicalResult(classicalResult.envelope)
      }

      // ── Merge + deduplicate ─────────────────────────────────────────────────
      let merged = mergeAndDeduplicate(vectorChunks, classicalChunks)

      // ── Filter: content must contain maha_dasha_lord ────────────────────────
      const mahaLower = maha_dasha_lord.toLowerCase()
      merged = merged.filter(chunk => chunk.content.toLowerCase().includes(mahaLower))

      // ── Apply text_ids filter if specified ──────────────────────────────────
      if (args.text_ids && args.text_ids.length > 0) {
        const textIdSet = new Set(args.text_ids.map(id => id.toUpperCase()))
        merged = merged.filter(chunk => textIdSet.has(chunk.text_id))
      }

      // ── Sort by relevance_score descending, take top max_results ────────────
      merged.sort((a, b) => b.relevance_score - a.relevance_score)
      const topResults = merged.slice(0, max_results)

      // ── Determine sources_searched ──────────────────────────────────────────
      const sourcesSearched = args.text_ids ?? CLASSICAL_SOURCES

      return okResult({
        ok: true,
        maha_dasha_lord,
        antar_dasha_lord: antar_dasha_lord ?? null,
        results: topResults,
        result_count: topResults.length,
        sources_searched: sourcesSearched,
      })
    },
  )
}
