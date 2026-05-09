/**
 * MARSYS-JIS Stream C — Tool C.7: vector_search (secondary)
 *
 * Semantic similarity search over rag_embeddings + rag_chunks using pgvector
 * cosine distance. Embeds the query text via Vertex AI text-multilingual-embedding-002
 * (768 dims, ADC auth), then runs a nearest-neighbour SQL query against the
 * native's embedding store.
 *
 * Model matches python-sidecar/rag/embed.py (B.3 migration, 2026-04-28).
 * Voyage-3-large replaced by Vertex AI text-multilingual-embedding-002.
 *
 * This is a SECONDARY tool — it supplements primary retrieval tools and is
 * skipped entirely when the VECTOR_SEARCH_ENABLED feature flag is off.
 *
 * Gracefully degrades when Vertex AI is unavailable or the DB query fails.
 */

import crypto from 'crypto'
import { GoogleAuth } from 'google-auth-library'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { getFlag, configService } from '@/lib/config'
import { VECTOR_SEARCH_TOP_K_KEY, VECTOR_SEARCH_TOP_K_DEFAULT } from '@/lib/config/feature_flags'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'vector_search'
const TOOL_VERSION = '1.1.0'
const DEFAULT_NATIVE_ID = 'abhisek_mohanty'

// Must match embed.py EMBED_MODEL and EMBED_DIM (B.3 migration)
const VERTEX_MODEL = 'text-multilingual-embedding-002'
const VERTEX_EMBED_DIM = 768

// [D.5 TODO] Author L3/spiritual_domain_report.md — needed for mantra/spiritual
// remedial retrieval. Until that document is indexed, vector_search({ doc_type:
// ["domain_report"] }) will return [] for spiritual/remedial queries. The
// function handles empty results safely (returns [] bundle, no throw).
// When authored: ingest with doc_type="domain_report", layer="L3" so the
// existing SQL_VECTOR_SEARCH query picks it up via the doc_type filter.

// ---------------------------------------------------------------------------
// SQL
// ---------------------------------------------------------------------------

const SQL_VECTOR_SEARCH = `
  SELECT e.chunk_id, c.content, c.source_file, c.layer, c.doc_type,
         c.source_version, e.embedding <=> $1::vector AS distance
  FROM rag_embeddings e
  JOIN rag_chunks c ON e.chunk_id = c.chunk_id
  WHERE c.is_stale = false
    AND ($3::text[] IS NULL OR c.doc_type = ANY($3::text[]))
    AND ($4::text IS NULL OR c.layer = $4)
    AND ($5::text IS NULL OR c.metadata->>'varga' = $5)
    AND ($6::text IS NULL OR c.metadata->>'section_id' LIKE $6 || '%')
  ORDER BY e.embedding <=> $1::vector
  LIMIT $2
`.trim()

// ---------------------------------------------------------------------------
// Row type
// ---------------------------------------------------------------------------

interface ChunkRow {
  chunk_id: string
  content: string
  source_file: string
  layer: string
  doc_type: string
  source_version: string
  distance: number
}

// ---------------------------------------------------------------------------
// Vertex AI embedding (ADC — no API key required; uses Application Default Credentials)
// ---------------------------------------------------------------------------

async function getQueryEmbedding(queryText: string): Promise<number[]> {
  const project = process.env.GCP_PROJECT ?? ''
  const location = process.env.VERTEX_AI_LOCATION

  if (!project) {
    throw new Error('GCP_PROJECT env var not set — required for Vertex AI embeddings')
  }
  if (!location) {
    throw new Error('VERTEX_AI_LOCATION env var not set — refusing to fall back to wrong region (would corrupt vector similarity against asia-south1 embeddings)')
  }

  const endpoint =
    `https://${location}-aiplatform.googleapis.com/v1/projects/${project}` +
    `/locations/${location}/publishers/google/models/${VERTEX_MODEL}:predict`

  // Obtain ADC bearer token via google-auth-library
  const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] })
  const client = await auth.getClient()
  const tokenResponse = await client.getAccessToken()
  const token = tokenResponse.token ?? ''

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      instances: [{ task_type: 'RETRIEVAL_QUERY', content: queryText }],
    }),
  })

  if (!response.ok) {
    throw new Error(`Vertex AI Embeddings API returned ${response.status}`)
  }

  const data = await response.json()
  const values = data.predictions?.[0]?.embeddings?.values as number[] | undefined
  if (!values || values.length !== VERTEX_EMBED_DIM) {
    throw new Error(
      `Vertex AI returned unexpected embedding shape: got ${values?.length ?? 0}, expected ${VERTEX_EMBED_DIM}`
    )
  }
  return values
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildEmptyBundle(
  start: number,
  nativeId: string,
  topK: number,
  queryText: string
): ToolBundle {
  const latency_ms = Date.now() - start
  const result_hash =
    'sha256:' + crypto.createHash('sha256').update(JSON.stringify([])).digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { native_id: nativeId, top_k: topK, query_text: queryText },
    results: [],
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `vector_search produced invalid empty ToolBundle: ${JSON.stringify(validation.errors)}`
    )
  }

  return bundle
}

function buildWarningBundle(
  start: number,
  nativeId: string,
  topK: number,
  queryText: string,
  message: string
): ToolBundle {
  const latency_ms = Date.now() - start
  const warningResults: ToolBundleResult[] = [
    {
      content: message,
      source_canonical_id: 'vector_search',
      source_version: '1.0',
      confidence: 0,
    },
  ]

  const result_hash =
    'sha256:' +
    crypto.createHash('sha256').update('vector_search_degraded').digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { native_id: nativeId, top_k: topK, query_text: queryText },
    results: warningResults,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `vector_search produced invalid warning ToolBundle: ${JSON.stringify(validation.errors)}`
    )
  }

  return bundle
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
  const nativeId = (params?.native_id as string | undefined) ?? DEFAULT_NATIVE_ID
  const queryText = plan.query_text

  // Resolve topK: params override wins, then configService
  const configTopK = configService.getValue(
    VECTOR_SEARCH_TOP_K_KEY,
    VECTOR_SEARCH_TOP_K_DEFAULT
  ) as number
  const topK =
    typeof params?.top_k === 'number' && params.top_k > 0 ? params.top_k : configTopK

  // Resolve filter: from plan.vector_search_filter; null = no filter
  const docTypeFilter = plan.vector_search_filter?.doc_type ?? null
  const layerFilter = plan.vector_search_filter?.layer ?? null
  const vargaFilter = plan.vector_search_filter?.varga ?? null
  const sectionIdPrefixFilter = plan.vector_search_filter?.section_id_prefix ?? null

  // --- Feature flag gate ---
  if (!getFlag('VECTOR_SEARCH_ENABLED')) {
    const bundle = buildEmptyBundle(start, nativeId, topK, queryText)
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: bundle.invocation_params as Record<string, unknown>,
      status: 'zero_rows',
      rows_returned: 0,
      latency_ms: bundle.latency_ms,
      token_estimate: 0,
      data_asset_id: 'RAG_CHUNKS',
      error_code: null,
      served_from_cache: false,
      fallback_used: false,
    })
    return bundle
  }

  // --- Embed the query ---
  let embedding: number[]
  try {
    embedding = await getQueryEmbedding(queryText)
  } catch (err) {
    telemetry.recordLatency(TOOL_NAME, 'vertex_error', Date.now() - start)
    const bundle = buildWarningBundle(
      start,
      nativeId,
      topK,
      queryText,
      `Vector search unavailable: Vertex AI embedding call failed`
    )
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: bundle.invocation_params as Record<string, unknown>,
      status: 'error',
      rows_returned: 0,
      latency_ms: bundle.latency_ms,
      token_estimate: 0,
      data_asset_id: 'RAG_CHUNKS',
      error_code: err instanceof Error ? err.message : 'vertex_embed_failed',
      served_from_cache: false,
      fallback_used: false,
    })
    return bundle
  }

  // Serialize for pgvector: '[0.1,0.2,...]'
  const embeddingParam = '[' + embedding.join(',') + ']'

  // --- DB query ---
  let rows: ChunkRow[]
  try {
    const storage = getStorageClient()
    const result = await storage.query<ChunkRow>(SQL_VECTOR_SEARCH, [
      embeddingParam,
      topK,
      docTypeFilter,
      layerFilter,
      vargaFilter,
      sectionIdPrefixFilter,
    ])
    rows = result.rows
  } catch (err) {
    telemetry.recordLatency(TOOL_NAME, 'db_error', Date.now() - start)
    const bundle = buildWarningBundle(
      start,
      nativeId,
      topK,
      queryText,
      `Vector search unavailable: DB query failed`
    )
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: bundle.invocation_params as Record<string, unknown>,
      status: 'error',
      rows_returned: 0,
      latency_ms: bundle.latency_ms,
      token_estimate: 0,
      data_asset_id: 'RAG_CHUNKS',
      error_code: err instanceof Error ? err.message : 'vector_db_query_failed',
      served_from_cache: false,
      fallback_used: false,
    })
    return bundle
  }

  // --- Build results ---
  const results: ToolBundleResult[] = rows.map(row => ({
    content: row.content + '\n\n[Source: ' + row.source_file + ' | Layer: ' + row.layer + ']',
    source_canonical_id: row.doc_type,
    source_version: row.source_version,
    confidence: 1 - row.distance,
    signal_id: row.chunk_id,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.signal_id ?? r.content.slice(0, 50)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      native_id: nativeId,
      top_k: topK,
      query_text: queryText,
      doc_type_filter: docTypeFilter,
      layer_filter: layerFilter,
      varga_filter: vargaFilter,
      section_id_prefix_filter: sectionIdPrefixFilter,
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
      `vector_search produced invalid ToolBundle: ${JSON.stringify(validation.errors)}`
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
    data_asset_id: 'RAG_CHUNKS',
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

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export const TOOL_METADATA = {
  secondary: true,
  description: 'vector_search [secondary]: semantic similarity search',
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  retrieve,
  secondary: true,
}
