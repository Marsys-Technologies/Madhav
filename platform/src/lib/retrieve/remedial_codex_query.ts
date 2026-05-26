/**
 * MARSYS-JIS Stream B — Tool: remedial_codex_query (M2-D.3)
 *
 * Queries rag_chunks where doc_type='l4_remedial' and returns L4 remedial
 * prescriptions — planetary propitiation, gemology, mantra, yantra, devata,
 * lifestyle protocols.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'remedial_codex_query'
const TOOL_VERSION = '1.0.0'

export type PracticeType = 'gemstone' | 'mantra' | 'yantra' | 'devata' | 'dinacharya' | 'propit'

export interface RemedialCodexQueryInput {
  planet?: string        // e.g. 'Mercury', 'Saturn', 'Mars'
  practice_type?: PracticeType
  keyword?: string       // free-text keyword (ILIKE on content)
  limit?: number         // default 8
}

const PRACTICE_TYPE_KEYWORDS: Record<PracticeType, string> = {
  gemstone:  'gem',
  mantra:    'mantra',
  yantra:    'yantra',
  devata:    'devata',
  dinacharya: 'dinacharya',
  propit:    'propitiat',
}

interface RagChunkRow {
  content: string
  doc_type: string
  chunk_id: string
  canonical_id: string | null
  source_file: string | null
  source_version: string | null
}

function buildQuery(p: RemedialCodexQueryInput): { sql: string; args: unknown[] } {
  const conditions: string[] = ["doc_type = 'l4_remedial'"]
  const args: unknown[] = []
  let idx = 1

  if (p.planet) {
    // Word-boundary regex prevents "Saturn" matching "Saturnine" or substring-only hits.
    // PostgreSQL POSIX: \m = word start, \M = word end.
    conditions.push(`content ~* $${idx}`)
    args.push(`\\m${p.planet}\\M`)
    idx++
  }

  if (p.practice_type) {
    const kw = PRACTICE_TYPE_KEYWORDS[p.practice_type]
    conditions.push(`content ILIKE $${idx}`)
    args.push(`%${kw}%`)
    idx++
  }

  if (p.keyword) {
    conditions.push(`content ILIKE $${idx}`)
    args.push(`%${p.keyword}%`)
    idx++
  }

  const limit = Math.min(p.limit ?? 8, 20)
  const sql = `
    SELECT content, doc_type, chunk_id, canonical_id, source_file, source_version
    FROM rag_chunks
    WHERE ${conditions.join(' AND ')}
    ORDER BY chunk_id
    LIMIT ${limit}
  `.trim()

  return { sql, args }
}

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
  const p: RemedialCodexQueryInput = {
    planet: (params?.planet as string | undefined) ??
      (plan.planets && plan.planets.length > 0 ? plan.planets[0] : undefined),
    practice_type: params?.practice_type as PracticeType | undefined,
    keyword: params?.keyword as string | undefined,
    limit: params?.limit as number | undefined,
  }

  const { sql, args } = buildQuery(p)
  const { rows } = await getStorageClient().query<RagChunkRow>(sql, args)

  const results: ToolBundleResult[] = rows.map((row) => ({
    content: JSON.stringify({
      content: row.content,
      doc_type: row.doc_type,
      chunk_id: row.chunk_id,
    }),
    source_canonical_id: row.canonical_id ?? 'REMEDIAL_CODEX_v2_0',
    source_version: row.source_version ?? undefined,
    confidence: 1.0,
    significance: 0.85,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      planet: p.planet,
      practice_type: p.practice_type,
      keyword: p.keyword,
      limit: p.limit,
    },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `remedial_codex_query: ToolBundle schema validation failed: ${JSON.stringify(validation.errors)}`
    )
  }

  telemetry.recordLatency(TOOL_NAME, 'retrieve', latency_ms)

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: rows.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: rows.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(rows).length / 4),
    data_asset_id: 'REMEDIAL_CODEX_v2_0',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
    raw_result_count: rows.length,
    kept_result_count: results.length,
    dropped_items: [],
    kept_items: results.slice(0, 200).map(r => ({
      item_id: r.signal_id ?? r.source_canonical_id,
      score: r.confidence ?? null,
      contribution_tokens: null,
    })),
    tool_input_payload: bundle.invocation_params,
    error_class: 'OK',
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  retrieve,
}
