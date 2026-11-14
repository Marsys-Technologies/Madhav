/**
 * Chart-bound snippet enrichment. Normal tests never open a DB. The optional
 * SQL cases execute the production resolver's SQL/binders on a disposable local
 * Postgres, with a temporary synthetic table on one connection. Enable with
 * MSR_SNIPPET_FIXTURE_SOCKET=<owned scratch.noindex socket directory>.
 * No DATABASE_URL, application DB client, provider or real chart is used.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { Client } from 'pg'
import type { MessagePartInput } from '@/lib/pariprashna/store/schema'
import type { PipelinePlan } from '@/lib/pipeline/types'

const boundary = vi.hoisted(() => ({
  query: vi.fn<(sql: string, params?: unknown[]) => Promise<{ rows: Record<string, unknown>[] }>>(),
  parts: [] as MessagePartInput[],
}))
vi.mock('@/lib/db/client', () => ({ query: boundary.query }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: () => false } }))
vi.mock('@/lib/conversations/writeGuard', () => ({
  checkConversationWritable: vi.fn(async () => ({ ok: true })),
  PersistenceRefusedError: class extends Error {},
  persistenceRefusalOf: () => null,
}))
vi.mock('@/lib/persistence/conversation_writer', () => ({
  writeConversationMessages: vi.fn(async () => ({ verified: true, messageIds: [] })),
}))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: () => ({ clear: vi.fn() }),
}))
vi.mock('@/lib/conversations/title', () => ({ generateConversationTitle: vi.fn() }))
vi.mock('@/lib/conversations', () => ({ updateConversationTitle: vi.fn() }))
vi.mock('@/lib/llm/pricing', () => ({ getModelPricingSync: () => null, computeCostUsd: () => null }))
vi.mock('@/lib/pariprashna/store/writer', () => ({
  writeTurn: vi.fn(async (message, parts: MessagePartInput[]) => {
    if (message.role === 'assistant') boundary.parts.push(...parts)
    return { message_id: message.id, parts_written: parts.length }
  }),
}))
vi.mock('../receipt_stage', () => ({
  computeTurnReceiptProvenance: vi.fn(async () => ({ provenanceStamp: {
    build_id: 'synthetic-build', priors_version: 'fixture', formula_versions: {},
    ranking_config: {}, now_context_date: '2026-11-14', computed_at: '2026-11-14T00:00:00Z',
  } })),
}))
vi.mock('@/lib/pariprashna/samiksha/capture', () => ({ captureDetectedCandidates: vi.fn() }))
// Blind-mode bookkeeping is an existing filesystem append, not a fixture output.
vi.mock('fs/promises', async (importOriginal) => ({
  ...await importOriginal<typeof import('fs/promises')>(), appendFile: vi.fn(async () => {}),
}))

import { fetchMsrSnippets, runPersistenceStage } from '../persistence_stage'
import { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

const CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const FOREIGN_CHART = '22222222-2222-4222-8222-222222222222'
const SAME = 'SIG.MSR.101'
const FOREIGN = 'SIG.MSR.202'
const UNKNOWN = 'SIG.MSR.303'
const SAME_ID = '11111111-1111-4111-8111-111111111111'
const FOREIGN_ID = '22222222-2222-4222-8222-222222222222'
const UNKNOWN_ID = '33333333-3333-4333-8333-333333333333'
const PROSE = `${SAME} ${FOREIGN} ${UNKNOWN}`
const socket = process.env.MSR_SNIPPET_FIXTURE_SOCKET

beforeEach(() => {
  boundary.parts.length = 0
  boundary.query.mockReset().mockResolvedValue({ rows: [] })
})

describe('MSR snippet scope — fail closed', () => {
  it.each(['', '   ', undefined])('does not query without a server chart (%s)', async (chart) => {
    expect(await fetchMsrSnippets([SAME], chart as string)).toEqual(new Map())
    expect(boundary.query).not.toHaveBeenCalled()
  })

  it.each([{ ids: [] }, { ids: [''] }, { ids: [' ', ''] }])('does not query an empty signal set ($ids)', async ({ ids }) => {
    expect(await fetchMsrSnippets(ids, CHART)).toEqual(new Map())
    expect(boundary.query).not.toHaveBeenCalled()
  })

  it('keeps the existing non-fatal empty result on a query error', async () => {
    boundary.query.mockRejectedValueOnce(new Error('synthetic unavailable database'))
    expect(await fetchMsrSnippets([SAME], CHART)).toEqual(new Map())
  })

  it('binds the server chart before signal IDs and removes empty IDs', async () => {
    await fetchMsrSnippets([SAME_ID, '', FOREIGN_ID], CHART)
    expect(boundary.query).toHaveBeenCalledWith(
      expect.stringContaining('WHERE chart_id = $1 AND signal_id::text IN ($2, $3)'),
      [CHART, SAME_ID, FOREIGN_ID],
    )
  })
})

describe.skipIf(!socket)('MSR snippet scope — real SQL synthetic fixture', () => {
  let db: Client
  beforeAll(async () => {
    if (!socket?.startsWith('/Users/Dev/scratch.noindex/codex/madhav/')) {
      throw new Error('Fixture socket must be in owned Madhav scratch.noindex')
    }
    db = new Client({ host: socket, port: 55439, user: 'fixture', database: 'postgres' })
    await db.connect()
    await db.query(`CREATE TEMP TABLE bodha_msr_signals (
      chart_id uuid NOT NULL, signal_id uuid PRIMARY KEY,
      signal_headline_text text, signal_summary_text text
    )`)
    await db.query(`INSERT INTO bodha_msr_signals VALUES
      ($1, $3, 'Same chart', 'Allowed summary'),
      ($2, $4, 'Foreign chart', 'Excluded summary')`, [CHART, FOREIGN_CHART, SAME_ID, FOREIGN_ID])
  })
  afterAll(async () => { await db?.end() })
  beforeEach(() => {
    boundary.query.mockImplementation(async (sql, params) => {
      // Execute exactly what production passes; never emulate chart filtering.
      if (!sql.includes('FROM bodha_msr_signals')) throw new Error('Unexpected fixture query')
      return db.query(sql, params)
    })
  })

  it('retains same-chart text while excluding foreign, unknown and empty IDs', async () => {
    expect(await fetchMsrSnippets([SAME_ID, FOREIGN_ID, UNKNOWN_ID, ''], CHART))
      .toEqual(new Map([[SAME_ID, 'Same chart — Allowed summary']]))
  })

  it('uses only the bound chart even when the other chart has the requested signal', async () => {
    expect(await fetchMsrSnippets([SAME_ID, FOREIGN_ID], FOREIGN_CHART))
      .toEqual(new Map([[FOREIGN_ID, 'Foreign chart — Excluded summary']]))
  })

  it('keeps snippet formatting and truncation', async () => {
    await db.query('INSERT INTO bodha_msr_signals VALUES ($1, $2, $3, NULL)', [CHART, UNKNOWN_ID, 'x'.repeat(310)])
    const snippets = await fetchMsrSnippets([UNKNOWN_ID], CHART)
    expect(snippets.get(UNKNOWN_ID)).toBe('x'.repeat(294) + '…')
  })

  it('binds both canonical persistence and the real shared write-through to identity.chartId', async () => {
    // Current prose extraction emits SIG.MSR.NNN, not stored UUIDs. Real UUID
    // rows therefore yield empty snippets on both paths today. This test pins
    // actual SQL + chart binders without claiming a reachable production leak.
    const chunks: string[] = []
    const em = new PariprashnaEmitter({
      enqueue: (chunk: Uint8Array) => { chunks.push(new TextDecoder().decode(chunk)) },
      desiredSize: 1, close: vi.fn(), error: vi.fn(),
    })
    const outcome = await runPersistenceStage({
      em,
      identity: { chartId: CHART, turnId: 'synthetic-turn', queryId: 'synthetic-turn',
        conversationId: 'synthetic-conversation', isFirstTurn: false },
      params: { selectedStack: 'gpt', modelId: 'fixture-model',
        modelMeta: { provider: 'fixture', maxOutputTokens: 100 }, readingDepth: 'auto',
        deepDive: false, lengthTier: 'standard', lelContextEnabled: false, style: 'plain',
      },
      user: { uid: 'synthetic-user' }, isSuperAdmin: false,
      messages: [], lastUserMessage: undefined,
      plan: { domains: [], query_class: 'diagnostic' } as unknown as PipelinePlan,
      plannerModelId: 'fixture-planner', plannerLatencyMs: 0,
      committedBlocks: [{ id: 'fixture-prose', role: 'prose', text: PROSE }],
      accumulatedText: PROSE, validToolResults: [],
      citationGate: { gateResult: 'PASS', layer1Count: 3, layer2Verified: 0 },
      synthesisStartedAt: Date.now(), citationRewriteEnabled: false,
    })
    expect(outcome).toEqual({ status: 'ok' })
    const canonical = boundary.parts.filter(part => part.kind === 'citation').map(part => part.body)
    const expected = [
      { index: 1, signal_id: SAME, layer: 'L2.5', snippet: '' },
      { index: 2, signal_id: FOREIGN, layer: 'L2.5', snippet: '' },
      { index: 3, signal_id: UNKNOWN, layer: 'L2.5', snippet: '' },
    ]
    expect(canonical).toEqual(expected)
    const events = chunks.join('').split('\n').filter(line => line.startsWith('data: '))
      .map(line => JSON.parse(line.slice(6)))
    const citations = events.filter(event => event.type === 'citation.define')
    expect(citations).toHaveLength(3)
    expected.forEach((citation, index) => expect(citations[index]).toMatchObject(citation))
    // One production query from canonical parts, one from onfinish's enrichment.
    expect(boundary.query).toHaveBeenCalledTimes(2)
    for (const [, params] of boundary.query.mock.calls) {
      expect(params).toEqual([CHART, SAME, FOREIGN, UNKNOWN])
    }
  })
})
