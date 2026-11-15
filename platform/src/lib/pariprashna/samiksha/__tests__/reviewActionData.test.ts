import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { createSourceFile, ScriptTarget, isImportDeclaration, isStringLiteral } from 'typescript'

const m = vi.hoisted(() => ({
  order: [] as string[], auth: vi.fn(), query: vi.fn(), last: vi.fn(), computed: vi.fn(),
  confirm: vi.fn(), transition: vi.fn(), record: vi.fn(), revalidate: vi.fn(),
}))
vi.mock('server-only', () => ({}))
vi.mock('next/cache', () => ({ revalidatePath: m.revalidate }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: m.auth }))
vi.mock('@/lib/db/client', () => ({ query: m.query }))
vi.mock('@/lib/pariprashna/provenance/stamp', () => ({ getLastTurnStamp: m.last, computeTurnProvenanceStamp: m.computed }))
vi.mock('@/lib/pariprashna/samiksha/reviewConfirm', () => ({ confirmDetectedCandidate: m.confirm }))
vi.mock('@/lib/pariprashna/samiksha/writer', () => ({ transitionLifecycle: m.transition }))
vi.mock('@/lib/pariprashna/samiksha/outcome_recorder', () => ({ recordConversationalOutcome: m.record }))
import { confirmCandidateAction, editCandidateAction, dismissCandidateAction, resolvePredictionAction, batchResolveAction } from '../../../../app/clients/[id]/samiksha/actions'

const ROW = 'row', CHART = 'chart'
const STAMP = { build_id: 'build', priors_version: 'priors', formula_versions: { formula: 'v1' }, ranking_config: { rank: 'v1' }, now_context_date: '2026-11-15' }
const OWNERSHIP = 'SELECT chart_id FROM brahma_mimamsa_prediction_ledger WHERE id = $1'
const ORIGIN = `SELECT cm.conversation_id
       FROM brahma_mimamsa_prediction_ledger l
       LEFT JOIN message_parts mp ON mp.id = l.message_part_id
       LEFT JOIN conversation_messages cm ON cm.id = mp.message_id
      WHERE l.id = $1`
const EDIT = `UPDATE brahma_mimamsa_prediction_ledger SET claim_text = $2
      WHERE id = $1 AND chart_id = $3 AND lifecycle_status = 'detected'
        AND chart_context_stale_at IS NULL`
const invalidation = `/clients/${CHART}/samiksha`

beforeEach(() => {
  vi.resetAllMocks()
  m.order.length = 0
  m.auth.mockImplementation(async () => { m.order.push('auth'); return { permission: 'all' } })
  m.query.mockImplementation(async (sql: string) => {
    m.order.push(sql === OWNERSHIP ? 'ownership' : sql === ORIGIN ? 'origin' : 'edit')
    return { rows: sql === OWNERSHIP ? [{ chart_id: CHART }] : sql === ORIGIN ? [{ conversation_id: 'conversation' }] : [] }
  })
  m.last.mockImplementation(async () => { m.order.push('last-stamp'); return { ...STAMP, internal: 'excluded' } })
  m.computed.mockImplementation(async () => { m.order.push('computed-stamp'); return { ...STAMP, internal: 'excluded' } })
  for (const [name, fn] of [['confirm', m.confirm], ['dismiss', m.transition], ['record', m.record]] as const) {
    fn.mockImplementation(async () => { m.order.push(name) })
  }
  m.revalidate.mockImplementation(() => { m.order.push('revalidate') })
})

const actions = [
  () => confirmCandidateAction({ chartId: CHART, rowId: ROW, probability: 0.7 }),
  () => editCandidateAction({ chartId: CHART, rowId: ROW, claimText: 'edited' }),
  () => dismissCandidateAction({ chartId: CHART, rowId: ROW, reason: 'reason' }),
  () => resolvePredictionAction({ chartId: CHART, rowId: ROW, outcome: 'happened' }),
  () => batchResolveAction({ chartId: CHART, items: [{ rowId: ROW, outcome: 'happened' }] }),
]

describe('review action data ownership and exact call ordering', () => {
  it.each(actions.map((call, index) => ({ call, index })))('action $index refuses denied access before SQL or domain effects', async ({ call }) => {
    m.auth.mockResolvedValue({ permission: 'view' })
    await expect(call()).rejects.toThrow('samiksha: not authorized to modify this chart’s prediction ledger')
    expect(m.query).not.toHaveBeenCalled()
    expect(m.last).not.toHaveBeenCalled()
    expect(m.computed).not.toHaveBeenCalled()
    expect(m.confirm).not.toHaveBeenCalled()
    expect(m.transition).not.toHaveBeenCalled()
    expect(m.record).not.toHaveBeenCalled()
    expect(m.revalidate).not.toHaveBeenCalled()
  })

  it('copies only the persisted stamp fields after exact chart/origin reads, confirms, then invalidates', async () => {
    await actions[0]()
    expect(m.query.mock.calls).toEqual([[OWNERSHIP, [ROW]], [ORIGIN, [ROW]]])
    expect(m.last).toHaveBeenCalledExactlyOnceWith('conversation')
    expect(m.computed).not.toHaveBeenCalled()
    expect(m.confirm).toHaveBeenCalledExactlyOnceWith({ rowId: ROW, probability: 0.7, stamp: STAMP })
    expect(m.revalidate).toHaveBeenCalledExactlyOnceWith(invalidation)
    expect(m.order).toEqual(['auth', 'ownership', 'origin', 'last-stamp', 'confirm', 'revalidate'])
  })

  it.each([null, 'conversation'])('uses the same computed fallback with origin %s and no persisted stamp', async (conversation) => {
    m.query.mockImplementation(async (sql: string) => ({ rows: sql === OWNERSHIP ? [{ chart_id: CHART }] : [{ conversation_id: conversation }] }))
    m.last.mockResolvedValue(null)
    await actions[0]()
    expect(m.last).toHaveBeenCalledTimes(conversation ? 1 : 0)
    expect(m.computed).toHaveBeenCalledExactlyOnceWith(CHART)
    expect(m.confirm).toHaveBeenCalledExactlyOnceWith({ rowId: ROW, probability: 0.7, stamp: STAMP })
    expect(m.revalidate).toHaveBeenCalledExactlyOnceWith(invalidation)
  })

  it('keeps the guarded edit SQL and bind order, including unchanged zero-row invalidation', async () => {
    await actions[1]()
    expect(m.query).toHaveBeenCalledExactlyOnceWith(EDIT, [ROW, 'edited', CHART])
    expect(m.order).toEqual(['auth', 'edit', 'revalidate'])
    expect(m.revalidate).toHaveBeenCalledExactlyOnceWith(invalidation)
  })

  it('propagates a query error without domain effects or invalidation', async () => {
    const failure = new Error('query failed')
    m.query.mockRejectedValue(failure)
    await expect(actions[1]()).rejects.toBe(failure)
    expect(m.confirm).not.toHaveBeenCalled()
    expect(m.revalidate).not.toHaveBeenCalled()
  })

  it('keeps outcome arguments and recorder-before-invalidation ordering', async () => {
    await resolvePredictionAction({ chartId: CHART, rowId: ROW, outcome: 'partial', note: 'note', partialValue: 0.25 })
    expect(m.record).toHaveBeenCalledExactlyOnceWith(ROW, { outcome: 'partial', outcome_note: 'note', partial_value: 0.25 })
    expect(m.order).toEqual(['auth', 'ownership', 'record', 'revalidate'])
  })

  it('preserves sequential batch effects and stops at the first cross-chart row without invalidating', async () => {
    m.query.mockImplementation(async (_sql: string, [row]: string[]) => ({ rows: [{ chart_id: row === 'second' ? 'other-chart' : CHART }] }))
    await expect(batchResolveAction({ chartId: CHART, items: [{ rowId: ROW, outcome: 'happened' }, { rowId: 'second', outcome: 'unverifiable' }] }))
      .rejects.toThrow('samiksha: ledger row second does not belong to chart chart')
    expect(m.auth).toHaveBeenCalledTimes(1)
    expect(m.query.mock.calls).toEqual([[OWNERSHIP, [ROW]], [OWNERSHIP, ['second']]])
    expect(m.record).toHaveBeenCalledExactlyOnceWith(ROW, { outcome: 'happened' })
    expect(m.revalidate).not.toHaveBeenCalled()
  })

  it('propagates a domain failure before invalidation', async () => {
    const failure = new Error('transition failed')
    m.transition.mockRejectedValue(failure)
    await expect(actions[2]()).rejects.toBe(failure)
    expect(m.query).toHaveBeenCalledExactlyOnceWith(OWNERSHIP, [ROW])
    expect(m.transition).toHaveBeenCalledExactlyOnceWith(ROW, 'dismissed', { dismissed_reason: 'reason' })
    expect(m.revalidate).not.toHaveBeenCalled()
  })
})

function directDbImports(source: string) {
  const file = createSourceFile('actions.ts', source, ScriptTarget.Latest, true)
  return file.statements.filter(isImportDeclaration).filter(node => isStringLiteral(node.moduleSpecifier)
    && /(?:^|\/)lib\/db(?:\/|$)/.test(node.moduleSpecifier.text))
}

describe('review actions stay thin while domain outcome calls remain visible', () => {
  it('rejects raw DB imports in the actual actions source and keeps the data owner server-only', () => {
    const source = readFileSync(new URL('../../../../app/clients/[id]/samiksha/actions.ts', import.meta.url), 'utf8')
    expect(directDbImports(source)).toHaveLength(0)
    const owner = readFileSync(new URL('../reviewActionData.ts', import.meta.url), 'utf8')
    expect(owner).toMatch(/^import 'server-only'/)
    expect(owner).not.toMatch(/(?:recordConversationalOutcome|transitionLifecycle|confirmDetectedCandidate)\s*\(/)
  })
  it.each([
    "import { query } from '@/lib/db/client'; query('SELECT 1')",
    "import * as database from '@/lib/db/client'; database.query('SELECT 1')",
  ])('refuses a reintroduced direct/namespace data bypass: %s', source => {
    expect(directDbImports(source)).toHaveLength(1)
  })
})
