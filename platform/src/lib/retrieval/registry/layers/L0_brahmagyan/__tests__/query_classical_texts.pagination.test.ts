import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock, embedTextMock } = vi.hoisted(() => ({ queryMock: vi.fn(), embedTextMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/embeddings/embedText', () => ({ embedText: embedTextMock }))

import { queryClassicalTextsCapability } from '../query_classical_texts'

const SPEC = '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6'
const DIGEST = 'a'.repeat(64)
const signingEnv = {
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1',
  INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: Buffer.alloc(32, 7).toString('base64url'),
}
const previousEnv = Object.fromEntries(Object.keys(signingEnv).map((key) => [key, process.env[key]]))

const corpusRows = Array.from({ length: 5 }, (_, index) => ({
  id: `row-${index + 1}`,
  text_id: 'BPHS',
  chunk_id: `chunk-${index + 1}`,
  verse_ref: `1.${index + 1}`,
  chapter: 1,
  verse_start: index + 1,
  content_en: `verse ${index + 1}`,
  content_sa: null,
  content_summary: null,
  source_citation: 'BPHS',
  tradition_school: null,
  topics: [],
  vector_score: null,
  keyword_score: 0.5,
}))

function receiptSnapshot(overrides: Record<string, unknown> = {}) {
  return {
    eligible_receipt_count: '1', replacement_in_progress: false,
    receipt_version: '7', partition_key: '__global__', output_digest: DIGEST,
    output_digest_spec_sha256: SPEC, rows: [], ...overrides,
  }
}

function installPagedSnapshot(overrides: Record<string, unknown> = {}) {
  queryMock.mockImplementation((_sql: string, params: unknown[]) => {
    const limit = Number(params.at(-2))
    const offset = Number(params.at(-1))
    return Promise.resolve({ rows: [receiptSnapshot({ rows: corpusRows.slice(offset, offset + limit), ...overrides })] })
  })
}

function contentOf(result: { content: unknown }) { return result.content as Record<string, unknown> }

describe('query_classical_texts receipt-pinned pagination', () => {
  beforeEach(() => {
    queryMock.mockReset()
    embedTextMock.mockReset()
    embedTextMock.mockResolvedValue(null)
    Object.assign(process.env, signingEnv)
    installPagedSnapshot()
  })

  afterEach(() => {
    for (const [key, value] of Object.entries(previousEnv)) {
      if (value === undefined) delete process.env[key]
      else process.env[key] = value
    }
  })

  it.each([
    { args: { query_text: 'dasha', top_k: 2 } },
    { args: { limit: 2 } },
  ])('traverses first, middle, and final signed pages without duplicate ids', async ({ args }) => {
    const pages: Record<string, unknown>[] = []
    let pageCursor: unknown
    do {
      const result = await queryClassicalTextsCapability.handler({ ...args, ...(pageCursor ? { page_cursor: pageCursor } : {}) }, undefined)
      expect(result.is_error).toBe(false)
      const content = contentOf(result)
      pages.push(content)
      pageCursor = content['next_page_cursor']
    } while (pageCursor)

    const served = pages.flatMap((page) => (page['citations'] as Array<{ id?: string; chunk_id: string }>).map((row) => row.id ?? row.chunk_id))
    expect(served).toHaveLength(5)
    expect(new Set(served).size).toBe(served.length)
    expect(pages.map((page) => page['more_available'])).toEqual([true, true, false])
    expect(pages.map((page) => page['next_offset'])).toEqual([2, 4, null])
    expect(pages.at(-1)?.['next_page_cursor']).toBeNull()
    expect(pages.every((page) => (page['snapshot_provenance'] as Record<string, unknown>)['output_digest'] === DIGEST)).toBe(true)
  })

  it.each([-1, 0.5, 2, '0', 'invalid', Number.POSITIVE_INFINITY])('rejects unsafe first-page raw offset %s', async (offset) => {
    await expect(queryClassicalTextsCapability.handler({ limit: 2, offset }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_required', restart_required: true } })
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('accepts literal numeric integer zero as the only explicit first-page offset', async () => {
    await expect(queryClassicalTextsCapability.handler({ limit: 2, offset: 0 }, undefined)).resolves.toMatchObject({
      is_error: false, content: { pagination: { offset: 0 } },
    })
  })

  it('rejects malformed cursors and unavailable signing', async () => {
    await expect(queryClassicalTextsCapability.handler({ limit: 2, page_cursor: 'forged.payload.signature' }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'invalid_page_cursor', restart_required: true } })
    delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
    delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
    await expect(queryClassicalTextsCapability.handler({ limit: 2 }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_signing_unavailable', restart_required: true } })
  })

  it('rejects normalized route/filter changes while preserving topic as free text', async () => {
    const first = contentOf(await queryClassicalTextsCapability.handler({ topic: 'dasha', text_source: 'BPHS', top_k: 1 }, undefined))
    expect(first['search_mode']).toBe('keyword_trigram_only')
    await expect(queryClassicalTextsCapability.handler({ query_text: 'different', text_source: 'BPHS', top_k: 1, page_cursor: first['next_page_cursor'] }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_filter_mismatch' } })
    await expect(queryClassicalTextsCapability.handler({ query: 'dasha', text_source: 'Saravali', top_k: 1, page_cursor: first['next_page_cursor'] }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_filter_mismatch' } })
  })

  it.each([
    ['output digest', { output_digest: 'b'.repeat(64) }],
    ['digest specification', { output_digest_spec_sha256: 'b'.repeat(64) }],
    ['partition', { partition_key: 'replacement' }],
    ['receipt version', { receipt_version: '8' }],
  ])('rejects continuation after %s drift', async (_label, drift) => {
    const first = contentOf(await queryClassicalTextsCapability.handler({ limit: 1 }, undefined))
    installPagedSnapshot(drift)
    await expect(queryClassicalTextsCapability.handler({ limit: 1, page_cursor: first['next_page_cursor'] }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_snapshot_changed', restart_required: true } })
  })

  it.each([
    ['missing/stale/unproven', { eligible_receipt_count: '0', receipt_version: null }],
    ['ambiguous', { eligible_receipt_count: '2' }],
    ['replacement', { replacement_in_progress: true }],
  ])('fails closed for a %s bg_texts snapshot', async (_label, snapshot) => {
    installPagedSnapshot(snapshot)
    const result = await queryClassicalTextsCapability.handler({ limit: 2 }, undefined)
    expect(result.is_error).toBe(true)
    expect(contentOf(result)).toMatchObject({ restart_required: true, next_page_cursor: null })
  })

  it('rejects vector/trigram and embedding-hash drift', async () => {
    embedTextMock.mockResolvedValue([0.1, 0.2])
    const first = contentOf(await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 1 }, undefined))
    embedTextMock.mockResolvedValue(null)
    await expect(queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 1, page_cursor: first['next_page_cursor'] }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_ranking_mode_changed' } })
    embedTextMock.mockResolvedValue([0.1, 0.3])
    await expect(queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 1, page_cursor: first['next_page_cursor'] }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_embedding_changed' } })
  })

  it('pins ILIKE fallback and rejects continuation if trigram becomes available', async () => {
    queryMock.mockRejectedValueOnce(new Error('similarity unavailable')).mockResolvedValueOnce({ rows: [receiptSnapshot({ rows: corpusRows.slice(0, 2) })] })
    const first = contentOf(await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 1 }, undefined))
    expect(first['search_mode']).toBe('keyword_ilike_fallback')
    installPagedSnapshot()
    await expect(queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 1, page_cursor: first['next_page_cursor'] }, undefined)).resolves.toMatchObject({ is_error: true, content: { code: 'page_cursor_ranking_mode_changed' } })
  })

  it('pins exact SQL ordering, one receipt boundary, and the canonical digest specification', async () => {
    await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 2 }, undefined)
    const hybridSql = String(queryMock.mock.calls[0]?.[0]).replace(/\s+/g, ' ')
    expect(hybridSql).toContain('ORDER BY combined_score DESC, text_id ASC, chapter ASC NULLS LAST, verse_ref ASC NULLS LAST, chunk_id ASC, id ASC')
    for (const marker of [
      'FROM asset_provenance_receipts receipt',
      'JOIN asset_freshness freshness',
      'freshness.asset_id = receipt.asset_id',
      'freshness.scope_key = receipt.scope_key',
      'freshness.partition_key = receipt.partition_key',
      'freshness.receipt_version = receipt.receipt_version',
      'JOIN asset_output_digest_specs digest_spec',
      'digest_spec.asset_id = receipt.asset_id',
      'digest_spec.spec_sha256 = receipt.output_digest_spec_sha256',
      "receipt.receipt_state = 'proven'",
      "freshness.freshness_state = 'fresh'",
      'receipt.chart_id IS NULL',
      "receipt.scope_key = '__global__'",
      'receipt.output_digest IS NOT NULL',
      'receipt.output_digest_spec_sha256 = $2::text',
      'digest_spec.retired_at IS NULL',
      'COUNT(*)::text AS eligible_receipt_count',
      "snapshot.eligible_receipt_count = '1'",
      'FROM build_run_assets asset',
      'JOIN build_runs run',
      'asset.asset_id = $1::text',
      "run.state IN ('planned', 'running', 'paused')",
      "asset.state IN ('queued', 'building')",
      'FROM classical_text_chunks',
    ]) expect(hybridSql).toContain(marker)
    expect((queryMock.mock.calls[0]?.[1] as unknown[]).slice(0, 2)).toEqual(['bg_texts', SPEC])
    queryMock.mockClear(); installPagedSnapshot()
    await queryClassicalTextsCapability.handler({ limit: 2 }, undefined)
    const listSql = String(queryMock.mock.calls[0]?.[0]).replace(/\s+/g, ' ')
    expect(listSql).toContain('ORDER BY text_id ASC, chapter ASC NULLS LAST, verse_start ASC NULLS LAST, chunk_id ASC, id ASC')
  })

  it('computes legacy empty-keyword nearest topics inside the same receipt-fenced SQL snapshot', async () => {
    queryMock.mockResolvedValueOnce({ rows: [receiptSnapshot({ rows: [], nearest_indexed_topics: ['dasha', 'mahadasha'] })] })

    const result = await queryClassicalTextsCapability.handler({ keyword: 'dashaa' }, undefined)

    expect(result.is_error).toBe(false)
    expect(contentOf(result)).toMatchObject({
      citations: [], rows: [], nearest_indexed_topics: ['dasha', 'mahadasha'],
      empty_reason: expect.stringContaining('is not indexed in the corpus'),
    })
    expect(queryMock).toHaveBeenCalledTimes(1)
    const sql = String(queryMock.mock.calls[0]?.[0]).replace(/\s+/g, ' ')
    expect(sql).toContain('topic_candidates AS')
    expect(sql).toContain('topic_suggestions AS')
    expect(sql).toContain("snapshot.eligible_receipt_count = '1'")
    expect(sql).toContain('NOT fence.replacement_in_progress')
    expect(sql).toContain('similarity(topic,')
    expect(sql).toContain('NOT EXISTS (SELECT 1 FROM page_rows)')
    expect(sql).toContain('LIMIT 5')
  })

  it('retries the complete receipt-fenced list query without suggestions when pg_trgm is unavailable', async () => {
    queryMock.mockRejectedValueOnce(new Error('function similarity(text, text) does not exist'))
      .mockResolvedValueOnce({ rows: [receiptSnapshot({ rows: [] })] })

    const result = await queryClassicalTextsCapability.handler({ keyword: 'dashaa' }, undefined)

    expect(result.is_error).toBe(false)
    expect(contentOf(result)).toMatchObject({ citations: [], rows: [], nearest_indexed_topics: [] })
    expect(queryMock).toHaveBeenCalledTimes(2)
    const retrySql = String(queryMock.mock.calls[1]?.[0]).replace(/\s+/g, ' ')
    expect(retrySql).not.toContain('topic_candidates AS')
    for (const marker of [
      'FROM asset_provenance_receipts receipt',
      'JOIN asset_freshness freshness',
      'JOIN asset_output_digest_specs digest_spec',
      "snapshot.eligible_receipt_count = '1'",
      'NOT fence.replacement_in_progress',
      'FROM build_run_assets asset',
      'JOIN build_runs run',
      'FROM classical_text_chunks c',
    ]) expect(retrySql).toContain(marker)
    expect((queryMock.mock.calls[1]?.[1] as unknown[]).slice(0, 3)).toEqual(['bg_texts', SPEC, 'dashaa'])
  })
})
