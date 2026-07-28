/**
 * L0 retrieval: classical_text_chunks (classical text chunks)
 * Tool: marsys://tool/L0/query_classical_texts
 *
 * R5 W2 corpus lane (design doc §3 CORPUS idiom / instrument #13 `ref_search`):
 * genuine hybrid vector + keyword ranking, not an either/or fallback. This is
 * also the target capability `vector_search` / `ref_vector_search` now resolve
 * to (tool_name_bridge.ts) — the P7 401 fix's second half (the first half was
 * the auth-header fix; this half is that the primitive it called had nothing
 * real to call — see tool_name_bridge.ts comment for the full story).
 *
 * Free-text search accepts any of `query_text` (canonical corpus-idiom name,
 * design §3), `query` (the ref_vector_search alias's param name), or `topic`
 * (find_verses_about's param name) — all three MCP-facing entry points land
 * on this one handler; normalizing the param name here means one real
 * implementation instead of three near-duplicates (the exact trap W1's
 * address-resolver work already hit once).
 *
 * Ranking: cosine similarity over the Vertex `text-multilingual-embedding-002`
 * embedding (768d, already populated on classical_text_chunks.embedding —
 * see migration 081_l0fr_schema.sql) combined with pg_trgm trigram similarity
 * over content_en, in ONE SQL ORDER BY (weighted sum) — a genuine hybrid, not
 * vector-then-fallback-to-keyword. If the embedding call fails (e.g. no GCP
 * credentials in a local/test environment), degrades to trigram-only ranking
 * rather than erroring the whole call.
 *
 * "Interpretation intent" (design §3 corpus idiom: "interpretation-intent
 * calls attach classical attestation"): any call using the free-text search
 * path (as opposed to the legacy exact `keyword` ILIKE path) is, by
 * construction, an interpretation-flavored query (asking about a topic/
 * meaning, not an exact-phrase lookup) — so it always returns full verse text
 * in hand (content_en + content_sa, never just an id) via the `citations`
 * array, capped at top_k≈5 by default per the design's "5 verses in hand"
 * framing (callers may raise top_k up to 50 for a wider FAN-OUT read).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { embedText } from '@/lib/embeddings/embedText'

const DEFAULT_INTERPRETATION_TOP_K = 5
const MAX_TOP_K = 50

// Hybrid weighting: vector similarity carries more signal for free-text/
// interpretation queries than raw trigram overlap on long verse translations
// (pg_trgm degrades as the length gap between query and content grows), but
// keyword overlap still matters — e.g. exact technical terms ("neecha
// bhanga") that an embedding alone can blur across near-synonyms.
const VECTOR_WEIGHT = 0.65
const KEYWORD_WEIGHT = 0.35

interface HybridRow {
  id: string
  text_id: string
  chunk_id: string
  verse_ref: string | null
  chapter: number | null
  content_en: string
  content_sa: string | null
  content_summary: string | null
  source_citation: string
  tradition_school: string | null
  topics: string[] | null
  vector_score: number | null
  keyword_score: number
  combined_score: number
}

// PARISHODHANA B1 (newly-discovered regression): embedText()'s Vertex AI call
// (platform/src/lib/embeddings/embedText.ts) wires no internal timeout of its own —
// neither the ADC auth handshake (getAuth().getClient()/getAccessToken()) nor the
// :predict fetch() carries an AbortSignal. A slow/hung credential or network path there
// previously blocked this function INDEFINITELY, because the try/catch below only
// catches a REJECTED promise, never a HUNG one. Every caller of the free-text/hybrid
// path (ref_dasha_systems_get, ref_nakshatra_get, ref_rules_search, ref_vector_search —
// anything that populates query_text/query/topic) inherited that hang and paid for it
// as a bare "TimeoutError: The operation was aborted due to timeout" once the MCP tool's
// own outer 15s AbortSignal.timeout finally cut the whole HTTP round-trip — an internal
// error with no honest degradation, even though this function's own doc comment already
// promised graceful degradation to trigram-only ranking. EMBED_TIMEOUT_MS bounds the
// wait so a slow embedding call degrades exactly the way the comment always claimed.
const EMBED_TIMEOUT_MS = 4_000

/** Best-effort query embedding — never throws and never hangs past
 * EMBED_TIMEOUT_MS; null on any failure OR timeout so the caller degrades to
 * trigram-only ranking instead of blocking on an unbounded embedding call. */
async function tryEmbedQuery(text: string): Promise<number[] | null> {
  try {
    return await Promise.race([
      embedText(text),
      new Promise<null>(resolve => setTimeout(() => resolve(null), EMBED_TIMEOUT_MS)),
    ])
  } catch {
    return null
  }
}

export const queryClassicalTextsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_classical_texts',
  type: 'tool',
  layer: 'L0',
  name: 'query_classical_texts',
  description:
    'Query the classical text corpus (classical_text_chunks) — classical text chunks ' +
    'from Brihat Parashara Hora Shastra, Saravali, Brihat Jataka, Uttara Kalamrita, ' +
    'Phala Deepika, Jataka Parijata, and other canonical texts. ' +
    'Each chunk is a verse or shloka with: text_id, chapter, verse_ref, topics, ' +
    'tradition_school, and the original Sanskrit + English translation. ' +
    'Use to cite classical sources for astrological observations. ' +
    'Free-text search (query_text/query/topic) runs genuine hybrid vector+keyword ' +
    'ranking and returns verse text IN HAND (content_en/content_sa), not just a ' +
    'citation id — this is the corpus idiom\'s ref_search / vector_search target. ' +
    'Exact-phrase search (keyword) does ILIKE substring matching with empty-with-reason.',
  input_schema: {
    query_text: { type: 'string', description: 'Free-text topic/meaning query — hybrid vector+keyword search (top_k≈5 verses in hand). Same field as query/topic.' },
    query:      { type: 'string', description: 'Alias for query_text (ref_vector_search naming).' },
    topic:      { type: 'string', description: 'Alias for query_text when used as free text (find_verses_about naming). NOTE: if you want the topics-array TAG filter instead, use text_source + the exact tag.' },
    keyword:     { type: 'string', description: 'Exact-phrase keyword to search in English translation (ILIKE substring, legacy path).' },
    text_source: { type: 'string', description: 'Filter by source text id (e.g. BPHS, Saravali, Brihat_Jataka).' },
    top_k:  { type: 'number', description: 'Max results for the hybrid search path (default 5).' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 20 },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval',
  emits_references: false,
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  // Band phase 6 ("Consulting the classics"), not a phase-5 retrieval facet — this is the
  // classical-corpus consultation phase in the fixed band sequence.
  register: { reader_label: 'Consulting the classics' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: false },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const freeText =
        (args.query_text as string | undefined) ??
        (args.query as string | undefined) ??
        (args.topic as string | undefined) ??
        undefined

      // ── Hybrid vector + keyword path (free-text / interpretation intent) ──
      if (freeText && freeText.trim().length > 0) {
        const topK = Math.min(
          Math.max(Number(args.top_k ?? args.limit ?? DEFAULT_INTERPRETATION_TOP_K), 1),
          MAX_TOP_K,
        )
        const textSource = args.text_source as string | undefined

        const embedding = await tryEmbedQuery(freeText)
        const params: unknown[] = [freeText]
        let vectorSelect = `NULL::float AS vector_score`
        if (embedding) {
          const embeddingStr = '[' + embedding.join(',') + ']'
          params.push(embeddingStr)
          vectorSelect = `(1 - (c.embedding <=> $${params.length}::vector))::float AS vector_score`
        }

        // NOTE: Postgres does NOT resolve a SELECT-list alias when it appears
        // inside a compound ORDER BY expression (only a bare "ORDER BY alias"
        // resolves — verified live against the prod-mirrored DB during this
        // wave: "column vector_score does not exist"). Wrapping in a subquery
        // makes vector_score/keyword_score real output columns of `sub`, which
        // the outer ORDER BY can then combine freely.
        let innerSql = `
          SELECT
            c.id, c.text_id, c.chunk_id, c.verse_ref, c.chapter,
            c.content_en, c.content_sa, c.content_summary, c.source_citation,
            c.tradition_school, c.topics,
            ${vectorSelect},
            similarity(c.content_en, $1)::float AS keyword_score
          FROM classical_text_chunks c
          WHERE 1=1
        `
        if (textSource) { innerSql += ` AND c.text_id = $${params.length + 1}`; params.push(textSource) }
        const sql = `
          SELECT * FROM (${innerSql}) sub
          ORDER BY (
            ${VECTOR_WEIGHT} * COALESCE(vector_score, 0) + ${KEYWORD_WEIGHT} * COALESCE(keyword_score, 0)
          ) DESC
          LIMIT $${params.length + 1}
        `
        params.push(topK)

        let rows: HybridRow[]
        try {
          const result = await query<Omit<HybridRow, 'combined_score'>>(sql, params)
          rows = result.rows.map(r => ({
            ...r,
            combined_score:
              VECTOR_WEIGHT * (r.vector_score ?? 0) + KEYWORD_WEIGHT * (r.keyword_score ?? 0),
          }))
        } catch {
          // pg_trgm similarity() unavailable — degrade to plain ILIKE substring
          // rather than erroring the whole call.
          const fallback = await query<Record<string, unknown>>(
            `SELECT id, text_id, chunk_id, verse_ref, chapter, content_en, content_sa,
                    content_summary, source_citation, tradition_school, topics
             FROM classical_text_chunks
             WHERE content_en ILIKE $1 ${textSource ? 'AND text_id = $2' : ''}
             LIMIT $${textSource ? 3 : 2}`,
            textSource ? [`%${freeText}%`, textSource, topK] : [`%${freeText}%`, topK],
          )
          rows = fallback.rows.map(r => ({
            ...(r as unknown as Omit<HybridRow, 'vector_score' | 'keyword_score' | 'combined_score'>),
            vector_score: null,
            keyword_score: 0.5,
            combined_score: 0.5,
          }))
        }

        // Verse text IN HAND: every citation carries the actual verse content,
        // not merely a citation_ref id (P7/E-4 fix per the design doc's
        // "citation arrives WITH verse text" gate).
        const citations = rows.map(r => ({
          citation_ref: `${r.text_id}:${r.verse_ref ?? r.chunk_id}`,
          chunk_id: r.chunk_id,
          text_id: r.text_id,
          verse_ref: r.verse_ref,
          chapter: r.chapter,
          verse_text_en: r.content_en,
          verse_text_sa: r.content_sa,
          content_summary: r.content_summary,
          tradition_school: r.tradition_school,
          topics: r.topics,
          source_citation: r.source_citation,
          vector_score: r.vector_score,
          keyword_score: r.keyword_score,
          combined_score: r.combined_score,
        }))

        return {
          content: {
            search_mode: embedding ? 'hybrid_vector_keyword' : 'keyword_trigram_only',
            query_used: freeText,
            citations,
            rows: citations, // back-compat alias — earlier callers read `rows`
            total: citations.length,
          },
          is_error: false,
        }
      }

      // ── Legacy exact-phrase / list path (unchanged behaviour) ────────────
      const limit  = Math.min((args.limit as number) ?? 20, 200)
      const offset = (args.offset as number) ?? 0
      const params: unknown[] = [limit, offset]
      // R6 3b-budgets (R-26): `SELECT *` was leaking the 768-dim `embedding` vector column
      // (~8KB/row of served bytes for zero consumer value — no caller reads a raw embedding
      // out of an MCP tool response) on ref_classical_citation_get's legacy keyword/topic-
      // filter path. The hybrid free-text path above never had this bug (it already selects
      // an explicit column list without `embedding`); this is the same fix applied here.
      let sql = `
        SELECT id, text_id, chunk_id, verse_ref, chapter, verse_start, content_en, content_sa,
               content_summary, source_citation, tradition_school, topics
        FROM classical_text_chunks WHERE 1=1
      `
      if (args.keyword)     { sql += ` AND content_en ILIKE $${params.length + 1}`; params.push(`%${args.keyword as string}%`) }
      if (args.text_source) { sql += ` AND text_id = $${params.length + 1}`; params.push(args.text_source as string) }
      if (args.topic)       { sql += ` AND $${params.length + 1} = ANY(topics)`; params.push(args.topic as string) }
      sql += ` ORDER BY text_id, chapter, verse_start LIMIT $1 OFFSET $2`
      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // E-3 empty-with-reason (R5 W0a punch-list, P8): a bare {rows: [], total: 0}
      // is indistinguishable from "the corpus has nothing on this term" (false) vs.
      // "this exact spelling/keyword is not indexed" (usually true). When a keyword
      // search comes back empty, say WHY and — where pg_trgm is available — surface
      // the nearest indexed topic tags as an honest, computed (not fabricated)
      // alternate-spelling suggestion.
      if (rows.length === 0 && args.keyword) {
        const keyword = args.keyword as string
        let nearestTopics: string[] = []
        try {
          const suggest = await query<{ topic: string }>(
            `
              SELECT topic FROM (
                SELECT DISTINCT unnest(topics) AS topic FROM classical_text_chunks
              ) t
              WHERE similarity(topic, $1) > 0.15
              ORDER BY similarity(topic, $1) DESC
              LIMIT 5
            `,
            [keyword]
          )
          nearestTopics = suggest.rows.map(r => r.topic)
        } catch {
          // pg_trgm similarity() unavailable or query failed — degrade to a
          // reason-only empty response rather than erroring the whole call.
          nearestTopics = []
        }
        return {
          content: {
            rows: [],
            total: 0,
            empty_reason: `No classical_text_chunks rows matched keyword "${keyword}" — this exact ` +
              `spelling/phrase is not indexed in the corpus (this does NOT mean the corpus is silent ` +
              `on the underlying concept — try a topic filter or an alternate spelling).`,
            nearest_indexed_topics: nearestTopics,
          },
          is_error: false,
        }
      }

      return { content: { rows, total: rows.length }, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
