/**
 * MARSYS-JIS Stream F — Brahmagyan Remedy Retrieval Tools
 * schema_version: 1.0
 *
 * RETIRED / DEPRECATED — lib/retrieve layer (legacy chat-route pipeline)
 * -----------------------------------------------------------------------
 * This file is part of the legacy lib/retrieve layer used by the Consume
 * chat route (runAdapterDispatch → getTool()). It is RETIRED in favour of
 * the retrieval registry layer (platform/src/lib/retrieval/registry).
 *
 * Replacement registry capabilities (Gate C citation):
 *   marsys://tool/L0/query_remedy_corpus  — registered in
 *     platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_remedy_corpus.ts
 *   marsys://tool/L0/query_remedies_tool  — registered in
 *     platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts
 *   MCP surface: platform-mcp/src/tools/retrieval/remedy_tools.ts (7 tools)
 *
 * This file is retained for the chat-route pipeline until full migration of
 * the chat channel to the retrieval registry (tracked by D7 channel descriptor
 * marsys://tool/channel/chat_dispatch). Do NOT remove until that migration
 * is complete. Do NOT add new capabilities here — add them to the registry.
 * -----------------------------------------------------------------------
 *
 * 7 retrieval capabilities for brahma_remedy_corpus:
 *   1. query_remedies           — planet + domain + category + top_k
 *   2. query_remedies_for_chart — affliction keyword (global corpus; NOT chart-scoped)
 *   3. list_remedies_by_category — category
 *   4. read_remedy              — remedy_id
 *   5. query_tantric_remedies   — deity + purpose
 *   6. query_remedies_by_planet — planet
 *   7. query_mantras            — planet
 *
 * ZERO LLM — all retrieval is deterministic SQL against brahma_remedy_corpus.
 */

import { createHash, randomUUID } from 'crypto'
import type { RetrievalTool, QueryPlan, ToolBundle, ToolBundleResult } from './types'
import {
  readRemedies,
  readRemediesForAffliction,
  readRemediesByCategory,
  readRemedyById,
  readTantricRemedies,
  readRemediesByPlanet,
  readMantraRemedies,
} from './remedy_reference_store'

// ── Utility ───────────────────────────────────────────────────────────────────

function makeBundle(
  toolName: string,
  version: string,
  params: Record<string, unknown>,
  rows: Record<string, unknown>[],
  latencyMs: number,
): ToolBundle {
  const results: ToolBundleResult[] = rows.map((row) => ({
    content: JSON.stringify(row),
    source_canonical_id: String(row['source_canonical_id'] ?? 'BPHS'),
    source_version: '1.0',
    confidence: Number(row['confidence'] ?? 0.85),
  }))
  const hash = createHash('sha256')
    .update(JSON.stringify(results))
    .digest('hex')
  return {
    tool_bundle_id: randomUUID(),
    tool_name: toolName,
    tool_version: version,
    invocation_params: params,
    results,
    served_from_cache: false,
    latency_ms: latencyMs,
    result_hash: `sha256:${hash}`,
    schema_version: '1.0',
  }
}

// ── Tool 1: query_remedies ────────────────────────────────────────────────────

export const queryRemedies: RetrievalTool = {
  name: 'query_remedies',
  version: '1.0.0',
  description:
    'Query brahma_remedy_corpus by planet, domain, category, and/or top_k. ' +
    'Returns remedy prescriptions with classical attestation.',
  async retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const planet = (params?.planet as string | undefined) ?? (plan.planets?.[0])
    const domain = params?.domain as string | undefined
    const category = params?.category as string | undefined
    const topK = Number(params?.top_k ?? 10)

    const rows = await readRemedies(planet, domain, category, topK)
    return makeBundle('query_remedies', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Tool 2: query_remedies_for_chart ─────────────────────────────────────────

export const queryRemediesForChart: RetrievalTool = {
  name: 'query_remedies_for_chart',
  version: '1.0.0',
  // F-06 (PARIŚEṢA-V4) scope honesty: the SQL below reads only
  // brahma_remedy_corpus (a global L0 reference table with no chart_id column).
  // No chart-scoped filtering happens or can happen here; the previous
  // "chart_id + affliction" description promised scoping the code never did.
  description:
    'Return corpus remedies matching an affliction keyword (planet name or life domain), ' +
    'matched ILIKE against the planet and domain columns of brahma_remedy_corpus. ' +
    'NOT chart-scoped: chart_id is not read and no chart-scoped SQL runs. ' +
    'For chart-derived remedies use the L2 surface (marsys://tool/L2/query_remedies).',
  async retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const affliction = (params?.affliction as string | undefined) ?? (plan.planets?.[0]) ?? ''
    const topK = Number(params?.top_k ?? 5)

    // Match affliction against both planet and domain columns
    const rows = await readRemediesForAffliction(affliction, topK)
    return makeBundle('query_remedies_for_chart', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Tool 3: list_remedies_by_category ────────────────────────────────────────

export const listRemediesByCategory: RetrievalTool = {
  name: 'list_remedies_by_category',
  version: '1.0.0',
  description:
    'List all remedies in a category. ' +
    'categories: mantras | gemstones | charity | vrata | yantras | puja | tantric | ayurvedic | vastu | behavioral',
  async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const category = (params?.category as string | undefined) ?? 'mantras'
    const rows = await readRemediesByCategory(category)
    return makeBundle('list_remedies_by_category', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Tool 4: read_remedy ───────────────────────────────────────────────────────

export const readRemedy: RetrievalTool = {
  name: 'read_remedy',
  version: '1.0.0',
  description:
    'Fetch the full record for a single remedy by remedy_id. ' +
    'Returns all columns including ingredients_jsonb and timing_rules_jsonb.',
  async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const remedyId = (params?.remedy_id as string | undefined) ?? ''
    const rows = await readRemedyById(remedyId)
    return makeBundle('read_remedy', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Tool 5: query_tantric_remedies ────────────────────────────────────────────

export const queryTantricRemedies: RetrievalTool = {
  name: 'query_tantric_remedies',
  version: '1.0.0',
  description:
    'Query tantric remedies only. All returned rows have passed the tantric careful-inclusion gate ' +
    '(BPHS / Phaladeepika sources only). Optional filter by deity or planet.',
  async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const deity = params?.deity as string | undefined
    const planet = params?.planet as string | undefined

    const rows = await readTantricRemedies(deity, planet)
    return makeBundle('query_tantric_remedies', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Tool 6: query_remedies_by_planet ─────────────────────────────────────────

export const queryRemediesByPlanet: RetrievalTool = {
  name: 'query_remedies_by_planet',
  version: '1.0.0',
  description:
    'Return all remedies for a given planet across all categories. ' +
    'Useful for building a complete upaya profile for a planet.',
  async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const planet = (params?.planet as string | undefined) ?? 'Saturn'
    const rows = await readRemediesByPlanet(planet)
    return makeBundle('query_remedies_by_planet', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Tool 7: query_mantras ─────────────────────────────────────────────────────

export const queryMantras: RetrievalTool = {
  name: 'query_mantras',
  version: '1.0.0',
  description:
    'Return all mantra remedies (category=mantras) for a given planet, ' +
    'including Sanskrit mantra, transliteration, and classical source.',
  async retrieve(_plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
    const t0 = Date.now()
    const planet = params?.planet as string | undefined

    const rows = await readMantraRemedies(planet)
    return makeBundle('query_mantras', '1.0.0', params ?? {}, rows, Date.now() - t0)
  },
}

// ── Export registry ───────────────────────────────────────────────────────────

export const REMEDY_TOOLS: RetrievalTool[] = [
  queryRemedies,
  queryRemediesForChart,
  listRemediesByCategory,
  readRemedy,
  queryTantricRemedies,
  queryRemediesByPlanet,
  queryMantras,
]
