/**
 * @deprecated lib/retrieve — DEPRECATED as of D7 (2026-06-28).
 *
 * Use lib/retrieval/registry (marsys:// URI scheme) for all NEW tools.
 * The registry is the single source of truth shared by both MCP and chat channels.
 * New capabilities: @see platform/src/lib/retrieval/registry/catalog.ts
 *
 * This module is NOT deleted because it has 17+ active callers (route.ts,
 * tool_catalogue.ts, agentic loop, etc.) that still depend on it.
 * Migration path: replace getTool(name) → getCapability('marsys://...') per tool.
 * Tracking: D7 §3.3 retirement plan.
 *
 * --- ORIGINAL HEADER (retained for history) ---
 * MARSYS-JIS Retrieval tool registry
 *
 * Stream G (BRAHMA-G-1): PyHora capabilities registered here.
 * compute_natal_positions, query_dasha_periods, query_special_lagnas
 *
 * L0FR Stream C (2026-06-07): 5 classical text retrieval tools registered.
 * Types and CONTRACT_CATALOG re-exports are preserved so the serve shell
 * (route.ts, tool_catalogue.ts, agentic loop) compiles and boots.
 */

import crypto from 'crypto'
export * from './types'
import type { RetrievalTool, ToolBundle, QueryPlan } from './types'

// Stream G — PyHora L1 Gaṇita capabilities (BRAHMA-G-1)
import { tool as computeNatalPositions } from './pyhora_natal_positions'
import { tool as queryDashaPeriods } from './pyhora_dasha_periods'
import { tool as querySpecialLagnas } from './pyhora_special_lagnas'

// ── Shared bundle helpers ─────────────────────────────────────────────────────

function resultHash(data: unknown): string {
  return 'sha256:' + crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex')
}

function emptyBundle(toolName: string, params: object, latencyMs: number): ToolBundle {
  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: toolName,
    tool_version: '1.0',
    invocation_params: params,
    results: [],
    served_from_cache: false,
    latency_ms: latencyMs,
    result_hash: resultHash([]),
    schema_version: '1.0',
  }
}

// ── L0FR Stream C: Classical text retrieval tools ────────────────────────────

const CLASSICAL_TOOLS: RetrievalTool[] = [
  {
    name: 'read_classical_text',
    version: '1.0',
    description: 'Semantic + full-text search over the classical Jyotish text corpus.',
    async retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
      const t0 = Date.now()
      const query = (params?.['query'] as string | undefined) ?? plan.query_text
      const limit = (params?.['limit'] as number | undefined) ?? 5
      try {
        // Dynamic import to avoid server-only issues in tests
        const mod = await import('../tools/classical_text_search')
        const result = await mod.classical_text_search({ query, limit })
        const latencyMs = Date.now() - t0
        return {
          tool_bundle_id: crypto.randomUUID(),
          tool_name: 'read_classical_text',
          tool_version: '1.0',
          invocation_params: { query, limit },
          results: result.results.map(r => ({
            content: r.text,
            source_canonical_id: r.text_key,
            confidence: r.confidence_baseline,
          })),
          served_from_cache: false,
          latency_ms: latencyMs,
          result_hash: resultHash(result.results),
          schema_version: '1.0',
        }
      } catch {
        return emptyBundle('read_classical_text', { query }, Date.now() - t0)
      }
    },
  },
  {
    name: 'read_chapter',
    version: '1.0',
    description: 'Fetch all verse chunks for a specific chapter of a classical text.',
    async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
      const t0 = Date.now()
      const text_id = (params?.['text_id'] as string | undefined) ?? ''
      const chapter = (params?.['chapter'] as number | undefined) ?? 1
      try {
        const mod = await import('../tools/classical_text_tools')
        const result = await mod.read_chapter({ text_id, chapter })
        const latencyMs = Date.now() - t0
        return {
          tool_bundle_id: crypto.randomUUID(),
          tool_name: 'read_chapter',
          tool_version: '1.0',
          invocation_params: { text_id, chapter },
          results: result.chunks.map(c => ({
            content: c.content_en,
            source_canonical_id: text_id,
          })),
          served_from_cache: false,
          latency_ms: latencyMs,
          result_hash: resultHash(result.chunks),
          schema_version: '1.0',
        }
      } catch {
        return emptyBundle('read_chapter', { text_id, chapter }, Date.now() - t0)
      }
    },
  },
  {
    name: 'list_classical_texts',
    version: '1.0',
    description: 'List all classical Jyotish texts ingested in the corpus with metadata.',
    async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
      const t0 = Date.now()
      try {
        const mod = await import('../tools/classical_text_tools')
        const result = await mod.list_classical_texts()
        const latencyMs = Date.now() - t0
        return {
          tool_bundle_id: crypto.randomUUID(),
          tool_name: 'list_classical_texts',
          tool_version: '1.0',
          invocation_params: params ?? {},
          results: result.texts.map(t => ({
            content: JSON.stringify(t),
            source_canonical_id: t.text_id,
          })),
          served_from_cache: false,
          latency_ms: latencyMs,
          result_hash: resultHash(result.texts),
          schema_version: '1.0',
        }
      } catch {
        return emptyBundle('list_classical_texts', params ?? {}, Date.now() - t0)
      }
    },
  },
  {
    name: 'find_verses_about',
    version: '1.0',
    description: 'Discover classical text verses about a specific astrological topic using embedding similarity.',
    async retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
      const t0 = Date.now()
      const topic = (params?.['topic'] as string | undefined) ?? plan.query_text
      const text_ids = params?.['text_ids'] as string[] | undefined
      const top_k = (params?.['top_k'] as number | undefined) ?? 10
      try {
        const mod = await import('../tools/classical_text_tools')
        const result = await mod.find_verses_about({ topic, text_ids, top_k })
        const latencyMs = Date.now() - t0
        return {
          tool_bundle_id: crypto.randomUUID(),
          tool_name: 'find_verses_about',
          tool_version: '1.0',
          invocation_params: { topic, text_ids, top_k },
          results: result.results.map(r => ({
            content: r.text,
            source_canonical_id: r.text_key,
            confidence: r.confidence_baseline,
          })),
          served_from_cache: false,
          latency_ms: latencyMs,
          result_hash: resultHash(result.results),
          schema_version: '1.0',
        }
      } catch {
        return emptyBundle('find_verses_about', { topic }, Date.now() - t0)
      }
    },
  },
  {
    name: 'search_classical_texts',
    version: '1.0',
    description: 'Combined embedding + full-text search over the classical Jyotish corpus. Alias for read_classical_text.',
    async retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
      const t0 = Date.now()
      const query = (params?.['query'] as string | undefined) ?? plan.query_text
      const top_k = (params?.['top_k'] as number | undefined) ?? 5
      try {
        const mod = await import('../tools/classical_text_search')
        const result = await mod.classical_text_search({ query, limit: top_k })
        const latencyMs = Date.now() - t0
        return {
          tool_bundle_id: crypto.randomUUID(),
          tool_name: 'search_classical_texts',
          tool_version: '1.0',
          invocation_params: { query, top_k },
          results: result.results.map(r => ({
            content: r.text,
            source_canonical_id: r.text_key,
            confidence: r.confidence_baseline,
          })),
          served_from_cache: false,
          latency_ms: latencyMs,
          result_hash: resultHash(result.results),
          schema_version: '1.0',
        }
      } catch {
        return emptyBundle('search_classical_texts', { query }, Date.now() - t0)
      }
    },
  },
]

// BRAHMA L0 Stream D — Sūtravali pattern extraction tools (SQL-only, ZERO LLM)
import { SUTRAVALI_RETRIEVAL_TOOLS } from './sutravali_tools'
// L0FR Stream F — Remedy Corpus retrieval tools
import { REMEDY_TOOLS } from './remedy_tools'
export { REMEDY_TOOLS } from './remedy_tools'

// ── Registry ─────────────────────────────────────────────────────────────────

export const RETRIEVAL_TOOLS: RetrievalTool[] = [
  // L1 Gaṇita — PyJHora natal computation (Stream G)
  computeNatalPositions,
  queryDashaPeriods,
  querySpecialLagnas,
  // Classical text retrieval (Stream C)
  ...CLASSICAL_TOOLS,
  // Sūtravali pattern extraction (Stream D)
  ...SUTRAVALI_RETRIEVAL_TOOLS,
  // Remedy Corpus retrieval (Stream F)
  ...REMEDY_TOOLS,
]

export function getTool(name: string): RetrievalTool | undefined {
  return RETRIEVAL_TOOLS.find(t => t.name === name)
}

// CONTRACT_CATALOG re-exports — registry is also empty after teardown.
export {
  CONTRACT_CATALOG,
  CONTRACT_CATALOG_BY_NAME,
  CONTRACT_TOOL_NAMES,
} from '../contract'
