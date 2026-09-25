/**
 * L0 classical-corpus retrieval with receipt-pinned, authenticated pagination.
 * A page is served only from the same database snapshot that proves one current,
 * fresh global bg_texts receipt and no replacement build in progress.
 */
import { createHash, createHmac, timingSafeEqual } from 'node:crypto'
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { embedText } from '@/lib/embeddings/embedText'
import { loadInquiryLifecycleSigningKeyRing, type InquiryLifecycleSigningKeyRing } from '@/lib/vidhi/inquiry/lifecycle_token'

const DEFAULT_INTERPRETATION_TOP_K = 5
const MAX_TOP_K = 50
const DEFAULT_LIST_LIMIT = 20
const MAX_LIST_LIMIT = 200
const MAX_OFFSET = 1_000_000
const VECTOR_WEIGHT = 0.65
const KEYWORD_WEIGHT = 0.35
const EMBED_TIMEOUT_MS = 4_000
const BG_TEXTS_ASSET_ID = 'bg_texts'
const BG_TEXTS_OUTPUT_DIGEST_SPEC_SHA256 = '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6'
const PAGE_CURSOR_DOMAIN = 'madhav:query_classical_texts:page_cursor:v1'

type RankingMode = 'hybrid_vector_keyword' | 'keyword_trigram_only' | 'keyword_ilike_fallback' | 'legacy_list'

interface SnapshotIdentity {
  readonly receipt_version: string
  readonly partition_key: string
  readonly output_digest: string
  readonly output_digest_spec_sha256: string
}

interface ClassicalPageCursor extends SnapshotIdentity {
  readonly version: 1
  readonly offset: number
  readonly filter_fingerprint: string
  readonly ranking_mode: RankingMode
  readonly embedding_hash: string | null
}

interface PageSnapshot extends Partial<SnapshotIdentity> {
  readonly eligible_receipt_count: string
  readonly replacement_in_progress: boolean
  readonly rows: Record<string, unknown>[]
  readonly nearest_indexed_topics?: string[]
}

function normalizeLimit(value: unknown, fallback: number, maximum: number): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return fallback
  const normalized = Math.floor(parsed)
  return normalized >= 1 ? Math.min(normalized, maximum) : fallback
}

function normalizeOffset(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return 0
  return Math.min(Math.max(Math.floor(parsed), 0), MAX_OFFSET)
}

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex')
}

function cursorMessage(kid: string, payload: string): string {
  return `${PAGE_CURSOR_DOMAIN}:${kid}.${payload}`
}

function encodePageCursor(cursor: ClassicalPageCursor, ring: InquiryLifecycleSigningKeyRing): string {
  const kid = ring.current.kid
  const payload = Buffer.from(JSON.stringify(cursor), 'utf8').toString('base64url')
  const signature = createHmac('sha256', ring.current.material).update(cursorMessage(kid, payload)).digest('base64url')
  return `${kid}.${payload}.${signature}`
}

function decodePageCursor(value: unknown, ring: InquiryLifecycleSigningKeyRing): ClassicalPageCursor | null {
  if (typeof value !== 'string' || !value) return null
  try {
    const parts = value.split('.')
    if (parts.length !== 3) return null
    const [kid, payload, signature] = parts
    if (!kid || !payload || !signature || !/^[A-Za-z0-9_-]+$/.test(payload) || !/^[A-Za-z0-9_-]+$/.test(signature)) return null
    const key = [ring.current, ...(ring.previous ?? [])].find((candidate) => candidate.kid === kid)
    if (!key) return null
    const payloadBytes = Buffer.from(payload, 'base64url')
    const actual = Buffer.from(signature, 'base64url')
    if (payloadBytes.toString('base64url') !== payload || actual.toString('base64url') !== signature) return null
    const expected = createHmac('sha256', key.material).update(cursorMessage(kid, payload)).digest()
    if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) return null
    const parsed = JSON.parse(payloadBytes.toString('utf8')) as Partial<ClassicalPageCursor>
    const modes: RankingMode[] = ['hybrid_vector_keyword', 'keyword_trigram_only', 'keyword_ilike_fallback', 'legacy_list']
    if (parsed.version !== 1 || typeof parsed.offset !== 'number' || !Number.isSafeInteger(parsed.offset)
      || parsed.offset < 0 || parsed.offset > MAX_OFFSET
      || typeof parsed.filter_fingerprint !== 'string' || !/^[a-f0-9]{64}$/.test(parsed.filter_fingerprint)
      || !modes.includes(parsed.ranking_mode as RankingMode)
      || !(parsed.embedding_hash === null || (typeof parsed.embedding_hash === 'string' && /^[a-f0-9]{64}$/.test(parsed.embedding_hash)))
      || typeof parsed.receipt_version !== 'string' || !parsed.receipt_version
      || typeof parsed.partition_key !== 'string' || !parsed.partition_key
      || typeof parsed.output_digest !== 'string' || !/^[a-f0-9]{64}$/.test(parsed.output_digest)
      || typeof parsed.output_digest_spec_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(parsed.output_digest_spec_sha256)) return null
    return parsed as ClassicalPageCursor
  } catch {
    return null
  }
}

function paginationError(code: string, error: string, extra: Record<string, unknown> = {}) {
  return {
    content: {
      code, error, restart_required: true, citations: [], rows: [], total: 0,
      total_scope: 'page', more_available: false, next_offset: null, next_page_cursor: null,
      ...extra,
    },
    is_error: true,
  }
}

async function tryEmbedQuery(text: string): Promise<number[] | null> {
  try {
    return await Promise.race([
      embedText(text),
      new Promise<null>((resolve) => setTimeout(() => resolve(null), EMBED_TIMEOUT_MS)),
    ])
  } catch {
    return null
  }
}

function receiptBoundarySql(): string {
  return `eligible_receipts AS (
    SELECT receipt.receipt_version, receipt.partition_key, receipt.output_digest,
           receipt.output_digest_spec_sha256
      FROM asset_provenance_receipts receipt
      JOIN asset_freshness freshness
        ON freshness.asset_id = receipt.asset_id
       AND freshness.scope_key = receipt.scope_key
       AND freshness.partition_key = receipt.partition_key
       AND freshness.receipt_version = receipt.receipt_version
      JOIN asset_output_digest_specs digest_spec
        ON digest_spec.asset_id = receipt.asset_id
       AND digest_spec.spec_sha256 = receipt.output_digest_spec_sha256
       AND digest_spec.retired_at IS NULL
     WHERE receipt.asset_id = $1::text
       AND receipt.chart_id IS NULL
       AND receipt.scope_key = '__global__'
       AND receipt.receipt_state = 'proven'
       AND receipt.output_digest IS NOT NULL
       AND receipt.output_digest_spec_sha256 = $2::text
       AND freshness.freshness_state = 'fresh'
  ), receipt_snapshot AS (
    SELECT COUNT(*)::text AS eligible_receipt_count,
           MIN(receipt_version) AS receipt_version, MIN(partition_key) AS partition_key,
           MIN(output_digest) AS output_digest,
           MIN(output_digest_spec_sha256) AS output_digest_spec_sha256
      FROM eligible_receipts
  ), replacement_fence AS (
    SELECT EXISTS (
      SELECT 1 FROM build_run_assets asset
      JOIN build_runs run ON run.id = asset.run_id
      WHERE asset.asset_id = $1::text
        AND (run.state IN ('planned', 'running', 'paused') OR asset.state IN ('queued', 'building'))
    ) AS replacement_in_progress
  )`
}

function envelopeSql(pageCtes: string, extraSelect = ''): string {
  return `WITH ${receiptBoundarySql()}, ${pageCtes}
    SELECT snapshot.*, fence.replacement_in_progress,
           COALESCE((SELECT jsonb_agg(row ORDER BY order_position) FROM page_rows), '[]'::jsonb) AS rows${extraSelect}
      FROM receipt_snapshot snapshot CROSS JOIN replacement_fence fence`
}

function snapshotIdentity(snapshot: PageSnapshot): SnapshotIdentity | null {
  if (snapshot.eligible_receipt_count !== '1'
    || typeof snapshot.receipt_version !== 'string' || !snapshot.receipt_version
    || typeof snapshot.partition_key !== 'string' || !snapshot.partition_key
    || typeof snapshot.output_digest !== 'string' || !/^[a-f0-9]{64}$/.test(snapshot.output_digest)
    || snapshot.output_digest_spec_sha256 !== BG_TEXTS_OUTPUT_DIGEST_SPEC_SHA256) return null
  return {
    receipt_version: snapshot.receipt_version, partition_key: snapshot.partition_key,
    output_digest: snapshot.output_digest, output_digest_spec_sha256: snapshot.output_digest_spec_sha256,
  }
}

function snapshotChanged(cursor: ClassicalPageCursor, snapshot: PageSnapshot): boolean {
  return cursor.receipt_version !== snapshot.receipt_version
    || cursor.partition_key !== snapshot.partition_key
    || cursor.output_digest !== snapshot.output_digest
    || cursor.output_digest_spec_sha256 !== snapshot.output_digest_spec_sha256
}

async function fetchHybridPage(args: {
  freeText: string; textSource: string | null; embedding: number[] | null; limit: number; offset: number; fallback: boolean
}): Promise<PageSnapshot | undefined> {
  const params: unknown[] = [BG_TEXTS_ASSET_ID, BG_TEXTS_OUTPUT_DIGEST_SPEC_SHA256]
  const queryParam = `$${params.push(args.fallback ? `%${args.freeText}%` : args.freeText)}`
  let vectorExpression = 'NULL::float'
  if (!args.fallback && args.embedding) {
    const embeddingParam = `$${params.push(`[${args.embedding.join(',')}]`)}`
    vectorExpression = `(1 - (c.embedding <=> ${embeddingParam}::vector))::float`
  }
  const textSourcePredicate = args.textSource ? ` AND c.text_id = $${params.push(args.textSource)}::text` : ''
  const source = args.fallback
    ? `SELECT c.id, c.text_id, c.chunk_id, c.verse_ref, c.chapter, c.content_en, c.content_sa,
              c.content_summary, c.source_citation, c.tradition_school, c.topics,
              NULL::float AS vector_score, 0.5::float AS keyword_score, 0.5::float AS combined_score
         FROM classical_text_chunks c WHERE c.content_en ILIKE ${queryParam}${textSourcePredicate}`
    : `SELECT c.id, c.text_id, c.chunk_id, c.verse_ref, c.chapter, c.content_en, c.content_sa,
              c.content_summary, c.source_citation, c.tradition_school, c.topics,
              ${vectorExpression} AS vector_score,
              similarity(c.content_en, ${queryParam})::float AS keyword_score,
              (${VECTOR_WEIGHT} * COALESCE(${vectorExpression}, 0)
                + ${KEYWORD_WEIGHT} * COALESCE(similarity(c.content_en, ${queryParam}), 0))::float AS combined_score
         FROM classical_text_chunks c WHERE 1=1${textSourcePredicate}`
  const order = args.fallback
    ? 'text_id ASC, chapter ASC NULLS LAST, verse_ref ASC NULLS LAST, chunk_id ASC, id ASC'
    : 'combined_score DESC, text_id ASC, chapter ASC NULLS LAST, verse_ref ASC NULLS LAST, chunk_id ASC, id ASC'
  const limitParam = `$${params.push(args.limit + 1)}`
  const offsetParam = `$${params.push(args.offset)}`
  const sql = envelopeSql(`search_rows AS (${source}), page_rows AS (
    SELECT to_jsonb(search_rows) AS row, ROW_NUMBER() OVER (ORDER BY ${order}) AS order_position
      FROM search_rows CROSS JOIN receipt_snapshot snapshot CROSS JOIN replacement_fence fence
     WHERE snapshot.eligible_receipt_count = '1' AND NOT fence.replacement_in_progress
     ORDER BY ${order} LIMIT ${limitParam} OFFSET ${offsetParam}
  )`)
  const result = await query<PageSnapshot>(sql, params)
  return result.rows[0]
}

async function fetchListPage(args: {
  keyword: string | null; textSource: string | null; topic: string | null; limit: number; offset: number
  includeSuggestions: boolean
}): Promise<PageSnapshot | undefined> {
  const params: unknown[] = [BG_TEXTS_ASSET_ID, BG_TEXTS_OUTPUT_DIGEST_SPEC_SHA256]
  let predicates = ''
  const keywordParam = args.keyword ? `$${params.push(args.keyword)}` : null
  if (keywordParam) predicates += ` AND c.content_en ILIKE ('%' || ${keywordParam}::text || '%')`
  if (args.textSource) predicates += ` AND c.text_id = $${params.push(args.textSource)}::text`
  if (args.topic) predicates += ` AND $${params.push(args.topic)}::text = ANY(c.topics)`
  const limitParam = `$${params.push(args.limit + 1)}`
  const offsetParam = `$${params.push(args.offset)}`
  const order = 'text_id ASC, chapter ASC NULLS LAST, verse_start ASC NULLS LAST, chunk_id ASC, id ASC'
  const topicSuggestionCtes = keywordParam && args.includeSuggestions ? `, topic_candidates AS (
    SELECT DISTINCT topic
      FROM classical_text_chunks c
      CROSS JOIN LATERAL unnest(c.topics) AS topic
      CROSS JOIN receipt_snapshot snapshot CROSS JOIN replacement_fence fence
     WHERE snapshot.eligible_receipt_count = '1' AND NOT fence.replacement_in_progress
       AND NOT EXISTS (SELECT 1 FROM page_rows)
       AND similarity(topic, ${keywordParam}::text) > 0.15
  ), topic_suggestions AS (
    SELECT topic, similarity(topic, ${keywordParam}::text) AS score
      FROM topic_candidates ORDER BY score DESC, topic ASC LIMIT 5
  )` : ''
  const sql = envelopeSql(`search_rows AS (
    SELECT c.id, c.text_id, c.chunk_id, c.verse_ref, c.chapter, c.verse_start,
           c.content_en, c.content_sa, c.content_summary, c.source_citation,
           c.tradition_school, c.topics FROM classical_text_chunks c WHERE 1=1${predicates}
  ), page_rows AS (
    SELECT to_jsonb(search_rows) AS row, ROW_NUMBER() OVER (ORDER BY ${order}) AS order_position
     FROM search_rows CROSS JOIN receipt_snapshot snapshot CROSS JOIN replacement_fence fence
     WHERE snapshot.eligible_receipt_count = '1' AND NOT fence.replacement_in_progress
     ORDER BY ${order} LIMIT ${limitParam} OFFSET ${offsetParam}
  )${topicSuggestionCtes}`, keywordParam && args.includeSuggestions
    ? `, COALESCE((SELECT jsonb_agg(topic ORDER BY score DESC, topic ASC) FROM topic_suggestions), '[]'::jsonb) AS nearest_indexed_topics`
    : '')
  const result = await query<PageSnapshot>(sql, params)
  return result.rows[0]
}

function validateSnapshot(snapshot: PageSnapshot | undefined, cursor: ClassicalPageCursor | null) {
  if (!snapshot) return paginationError('bg_texts_receipt_unavailable', 'No consistent bg_texts receipt snapshot was available.')
  if (snapshot.replacement_in_progress) return paginationError('bg_texts_replacement_in_progress', 'A bg_texts replacement is in progress; restart after its fresh provenance receipt is complete.')
  if (cursor && snapshotChanged(cursor, snapshot)) return paginationError('page_cursor_snapshot_changed', 'The bg_texts receipt identity changed after this cursor was minted.')
  if (snapshot.eligible_receipt_count !== '1') {
    return paginationError(snapshot.eligible_receipt_count === '0' ? 'bg_texts_receipt_unavailable' : 'bg_texts_receipt_ambiguous', 'Exactly one current fresh, proven global bg_texts receipt is required.')
  }
  if (!snapshotIdentity(snapshot)) return paginationError('bg_texts_receipt_unavailable', 'The bg_texts receipt did not match the reviewed digest specification.')
  return null
}

export const queryClassicalTextsCapability: CapabilityDescriptor = {
  // W-L0-4 served-surface contract: explicit declaration (detector:
  // __tests__/l0_density_contract.test.ts — do not remove; values follow the
  // deriveDensityContract evidence rules in ../../descriptor_defaults.ts).
  density_contract: {
    max_verdict_bytes: 5120,
    max_digest_bytes: 20480,
    paginated: true,
    facets: ['query_text', 'query', 'topic', 'keyword', 'text_source', 'page_cursor'],
    empty_reason: true,
  },
  uri: 'marsys://tool/L0/query_classical_texts', type: 'tool', layer: 'L0', name: 'query_classical_texts',
  description: 'Query the classical text corpus with signed, receipt-pinned cursor pagination and verse text in hand.',
  input_schema: {
    query_text: { type: 'string', description: 'Free-text topic/meaning query.' },
    query: { type: 'string', description: 'Alias for query_text.' },
    topic: { type: 'string', description: 'Alias for free text; with no free-text route it remains the legacy topics filter.' },
    keyword: { type: 'string', description: 'Exact-phrase English substring search.' },
    text_source: { type: 'string', description: 'Source text id filter.' },
    top_k: { type: 'number', description: 'Hybrid result limit (default 5, max 50).' },
    offset: { type: 'number', default: 0, description: 'First-page diagnostic offset only; nonzero continuation requires page_cursor.' },
    limit: { type: 'number', default: 20 },
    page_cursor: { type: 'string', description: 'Opaque signed continuation token returned as next_page_cursor.' },
  },
  required_inputs: [], scope: 'global', archetype: 'prose_citation', traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval', emits_references: false, lel_capable: false,
  register: { reader_label: 'Consulting the classics' },
  llm_hints: { agentic: { cost_class: 'cheap', cacheable: false }, bulk_context: { pre_fetch_priority: 55, always_include: false } },

  async handler(args, _ctx) {
    void _ctx
    const suppliedCursor = args.page_cursor !== undefined && args.page_cursor !== null
    const initialOffsetIsSafe = args.offset === undefined || args.offset === null
      || (typeof args.offset === 'number' && Number.isInteger(args.offset) && args.offset === 0)
    if (!suppliedCursor && !initialOffsetIsSafe) return paginationError('page_cursor_required', 'Only numeric integer zero is accepted as a first-page offset; use next_page_cursor for continuation.')
    const requestedOffset = normalizeOffset(args.offset)

    let signingRing: InquiryLifecycleSigningKeyRing
    try {
      signingRing = loadInquiryLifecycleSigningKeyRing()
    } catch {
      return paginationError('page_cursor_signing_unavailable', 'Classical pagination signing is unavailable; a stable snapshot cannot be established.')
    }
    const cursor = suppliedCursor ? decodePageCursor(args.page_cursor, signingRing) : null
    if (suppliedCursor && !cursor) return paginationError('invalid_page_cursor', 'The supplied page_cursor is malformed, forged, or no longer signed by an accepted key.')

    const queryText = typeof args.query_text === 'string' ? args.query_text : undefined
    const queryAlias = typeof args.query === 'string' ? args.query : undefined
    const topicAlias = typeof args.topic === 'string' ? args.topic : undefined
    const freeText = queryText ?? queryAlias ?? topicAlias
    const usesFreeText = Boolean(freeText && freeText.trim().length > 0)
    const textSource = typeof args.text_source === 'string' && args.text_source ? args.text_source : null
    const keyword = typeof args.keyword === 'string' && args.keyword ? args.keyword : null
    const routeFingerprint = sha256(usesFreeText
      ? { route: 'free_text', query: freeText, text_source: textSource }
      : { route: 'legacy_list', keyword, text_source: textSource, topic: topicAlias || null })
    if (cursor && cursor.filter_fingerprint !== routeFingerprint) return paginationError('page_cursor_filter_mismatch', 'The cursor was minted for different normalized query filters.')

    const offset = cursor?.offset ?? requestedOffset
    const limit = usesFreeText
      ? normalizeLimit(args.top_k ?? args.limit, DEFAULT_INTERPRETATION_TOP_K, MAX_TOP_K)
      : normalizeLimit(args.limit, DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT)

    try {
      let rankingMode: RankingMode = 'legacy_list'
      let embeddingHash: string | null = null
      let snapshot: PageSnapshot | undefined
      if (usesFreeText && freeText) {
        const embedding = await tryEmbedQuery(freeText)
        rankingMode = embedding ? 'hybrid_vector_keyword' : 'keyword_trigram_only'
        embeddingHash = embedding ? sha256(embedding) : null
        if (cursor && cursor.ranking_mode !== 'keyword_ilike_fallback' && cursor.ranking_mode !== rankingMode) {
          return paginationError('page_cursor_ranking_mode_changed', 'The free-text ranking mode changed after this cursor was minted.')
        }
        if (cursor && cursor.ranking_mode === 'hybrid_vector_keyword' && cursor.embedding_hash !== embeddingHash) {
          return paginationError('page_cursor_embedding_changed', 'The query embedding changed after this cursor was minted.')
        }
        try {
          snapshot = await fetchHybridPage({ freeText, textSource, embedding, limit, offset, fallback: false })
          if (cursor?.ranking_mode === 'keyword_ilike_fallback') return paginationError('page_cursor_ranking_mode_changed', 'The free-text ranking mode changed after this cursor was minted.')
        } catch {
          if (cursor && cursor.ranking_mode !== 'keyword_ilike_fallback') return paginationError('page_cursor_ranking_mode_changed', 'The free-text ranking mode changed to ILIKE fallback after this cursor was minted.')
          rankingMode = 'keyword_ilike_fallback'
          embeddingHash = null
          snapshot = await fetchHybridPage({ freeText, textSource, embedding: null, limit, offset, fallback: true })
        }
      } else {
        if (cursor && cursor.ranking_mode !== 'legacy_list') return paginationError('page_cursor_ranking_mode_changed', 'The list ranking mode changed after this cursor was minted.')
        try {
          snapshot = await fetchListPage({ keyword, textSource, topic: topicAlias || null, limit, offset, includeSuggestions: Boolean(keyword) })
        } catch (error) {
          if (!keyword) throw error
          // pg_trgm suggestions are ancillary. Retry the complete page query,
          // including the receipt and replacement fence, without suggestion
          // CTEs rather than serving rows from an unfenced secondary read.
          snapshot = await fetchListPage({ keyword, textSource, topic: topicAlias || null, limit, offset, includeSuggestions: false })
        }
      }

      const snapshotError = validateSnapshot(snapshot, cursor)
      if (snapshotError) return snapshotError
      const identity = snapshotIdentity(snapshot!)!
      const fetchedRows = Array.isArray(snapshot!.rows) ? snapshot!.rows : []
      const rows = fetchedRows.slice(0, limit)
      const moreAvailable = fetchedRows.length > limit
      const nextOffset = moreAvailable ? offset + rows.length : null
      const nextPageCursor = moreAvailable ? encodePageCursor({
        version: 1, offset: nextOffset!, filter_fingerprint: routeFingerprint,
        ranking_mode: rankingMode, embedding_hash: embeddingHash, ...identity,
      }, signingRing) : null

      const citations = usesFreeText ? rows.map((row) => ({
        citation_ref: `${row['text_id']}:${row['verse_ref'] ?? row['chunk_id']}`,
        chunk_id: row['chunk_id'], text_id: row['text_id'], verse_ref: row['verse_ref'], chapter: row['chapter'],
        verse_text_en: row['content_en'], verse_text_sa: row['content_sa'], content_summary: row['content_summary'],
        tradition_school: row['tradition_school'], topics: row['topics'], source_citation: row['source_citation'],
        vector_score: row['vector_score'], keyword_score: row['keyword_score'], combined_score: row['combined_score'],
      })) : rows

      return {
        content: {
          search_mode: rankingMode, ...(usesFreeText ? { query_used: freeText } : {}),
          citations, rows: citations, total: citations.length, total_scope: 'page',
          more_available: moreAvailable, next_offset: nextOffset, next_page_cursor: nextPageCursor,
          pagination: { limit, offset, more_available: moreAvailable },
          snapshot_provenance: { asset_id: BG_TEXTS_ASSET_ID, ...identity },
          ...(!usesFreeText && citations.length === 0 && keyword ? {
            empty_reason: `No classical_text_chunks rows matched keyword "${keyword}" — this exact spelling/phrase is not indexed in the corpus.`,
            nearest_indexed_topics: Array.isArray(snapshot!.nearest_indexed_topics) ? snapshot!.nearest_indexed_topics : [],
          } : {}),
        },
        is_error: false,
      }
    } catch (error) {
      return { content: { error: String(error), citations: [], rows: [] }, is_error: true }
    }
  },
}
