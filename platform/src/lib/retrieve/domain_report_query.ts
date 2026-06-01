/**
 * MARSYS-JIS Stream B — Tool: domain_report_query (M2-D.2)
 *
 * Queries rag_chunks where doc_type='domain_report' and returns L3 domain-report
 * content for the specified domain(s). The 9 domain reports cover: career_dharma,
 * children, financial, health_longevity, parents, psychology_mind, relationships,
 * spiritual, travel.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'domain_report_query'
const TOOL_VERSION = '1.0.0'
const NATIVE_CHART_ID = process.env.NATIVE_CHART_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'

export interface DomainReportQueryInput {
  domains?: string[]   // e.g. ['career', 'relationships']
  keyword?: string     // free-text keyword to match in chunk content (ILIKE)
  limit?: number       // default 10
}

const DOMAIN_TO_PATTERN: Record<string, string> = {
  career:        '%CAREER_DHARMA%',
  dharma:        '%CAREER_DHARMA%',
  children:      '%CHILDREN%',
  financial:     '%FINANCIAL%',
  finance:       '%FINANCIAL%',
  wealth:        '%FINANCIAL%',
  health:        '%HEALTH_LONGEVITY%',
  longevity:     '%HEALTH_LONGEVITY%',
  parents:       '%PARENTS%',
  psychology:    '%PSYCHOLOGY_MIND%',
  mind:          '%PSYCHOLOGY_MIND%',
  relationships: '%RELATIONSHIPS%',
  marriage:      '%RELATIONSHIPS%',
  spiritual:     '%SPIRITUAL%',
  travel:        '%TRAVEL%',
}

interface RagChunkRow {
  content: string
  doc_type: string
  source_file: string | null
  chunk_id: string
  canonical_id: string | null
  source_version: string | null
}

function buildQuery(p: DomainReportQueryInput): { sql: string; args: unknown[] } {
  const conditions: string[] = ["doc_type = 'domain_report'"]
  const args: unknown[] = []
  let idx = 1

  if (p.domains && p.domains.length > 0) {
    const patterns = [...new Set(
      p.domains.flatMap(d => DOMAIN_TO_PATTERN[d.toLowerCase()] ? [DOMAIN_TO_PATTERN[d.toLowerCase()]] : [])
    )]
    if (patterns.length > 0) {
      const domainClauses = patterns.map(() => {
        const clause = `source_file ILIKE $${idx}`
        idx++
        return clause
      })
      conditions.push(`(${domainClauses.join(' OR ')})`)
      args.push(...patterns)
    }
  }

  if (p.keyword) {
    conditions.push(`content ILIKE $${idx}`)
    args.push(`%${p.keyword}%`)
    idx++
  }

  const limit = Math.min(p.limit ?? 10, 25)
  const chartCondition = `(chart_id = $${idx}::uuid OR chart_id IS NULL)`
  args.push(NATIVE_CHART_ID)
  const sql = `
    SELECT content, doc_type, source_file, chunk_id, canonical_id, source_version
    FROM rag_chunks
    WHERE ${conditions.join(' AND ')} AND ${chartCondition}
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
      data_asset_id: 'DOMAIN_REPORT',
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
  const p: DomainReportQueryInput = {
    domains: (params?.domains as string[] | undefined) ?? plan.domains,
    keyword: params?.keyword as string | undefined,
    limit: params?.limit as number | undefined,
  }

  const { sql, args } = buildQuery(p)
  const { rows } = await getStorageClient().query<RagChunkRow>(sql, args)

  const results: ToolBundleResult[] = rows.map((row) => ({
    content: JSON.stringify({
      content: row.content,
      doc_type: row.doc_type,
      source_doc: row.source_file,
      chunk_id: row.chunk_id,
    }),
    source_canonical_id: row.canonical_id ?? row.source_file?.split('/').pop()?.replace('.md', '') ?? 'domain_report',
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
      domains: p.domains,
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
      `domain_report_query: ToolBundle schema validation failed: ${JSON.stringify(validation.errors)}`
    )
  }

  telemetry.recordLatency(TOOL_NAME, 'retrieve', latency_ms)

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: results.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: results.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'DOMAIN_REPORT',
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
