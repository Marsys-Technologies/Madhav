import { beforeEach, describe, expect, it, vi } from 'vitest'
import { buildTurnDeepLink } from '@/lib/pariprashna/samiksha/deepLink'
import { readReviewSource } from '../reviewSource'
import { safeNextPath } from '@/lib/auth/safe_next'

const mocks = vi.hoisted(() => ({
  owned: vi.fn(), query: vi.fn(), consultation: vi.fn(), transcript: vi.fn(), archived: vi.fn(),
}))
vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))
vi.mock('../consultation', () => ({
  ownedConsultation: mocks.owned,
  consultationMessages: mocks.consultation,
  uuidLike: /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i,
}))
vi.mock('../historicalReading', () => ({ loadHistoricalConversationMessages: mocks.transcript }))
vi.mock('../readOnly', () => ({ isCorrectionArchived: mocks.archived }))

const chart = '10000000-0000-4000-8000-000000000001'
const reading = '10000000-0000-4000-8000-000000000002'
const part = '10000000-0000-4000-8000-000000000003'
const answer = '10000000-0000-4000-8000-000000000004'
const request = () => readReviewSource(chart, reading, part, 'fixture-owner')
const transcript = { id: answer, role: 'assistant', text: 'Fictional answer' }

describe('Prediction Review source reader', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mocks.owned.mockResolvedValue({ id: reading, chart_id: chart })
    mocks.query.mockResolvedValue({ rows: [{ id: answer }] })
    mocks.consultation.mockResolvedValue([{
      id: answer, role: 'assistant', metadata_json: { acharya_reading_receipt: {} },
    }])
    mocks.transcript.mockResolvedValue([transcript])
    mocks.archived.mockReturnValue(false)
  })

  it('maps the checked source part to the persisted assistant answer under the existing Consult URL', async () => {
    const bookmark = buildTurnDeepLink({
      chartId: chart, conversationId: reading, turnOrdinal: 1, sourcePartId: part,
    })
    expect(bookmark).toBe(`/clients/${chart}/consult/${reading}/source/${part}`)
    expect(safeNextPath(bookmark)).toBe(bookmark)
    expect(safeNextPath(`${bookmark}?sourcePart=${part}`)).toBeNull()
    expect(safeNextPath(`${bookmark}#pp-answer-${answer}`)).toBeNull()
    expect(await request()).toMatchObject({ answer: transcript, historical: false })
    expect(mocks.owned).toHaveBeenCalledWith(reading, 'fixture-owner')
    expect(mocks.query).toHaveBeenCalledWith(expect.stringContaining("m.role = 'assistant'"),
      [part, reading, chart, 'fixture-owner'])
  })

  it('does not read source data when ownership or current chart access is denied', async () => {
    mocks.owned.mockResolvedValue(null)
    expect(await request()).toBeNull()
    expect(mocks.query).not.toHaveBeenCalled()
    expect(mocks.transcript).not.toHaveBeenCalled()
  })

  it('rejects mismatched charts and duplicate or malformed source parts', async () => {
    mocks.owned.mockResolvedValue({ chart_id: reading })
    expect(await request()).toBeNull()
    expect(await readReviewSource(chart, reading, [part, part], 'fixture-owner')).toBeNull()
    expect(await readReviewSource(chart, reading, 'invalid', 'fixture-owner')).toBeNull()
    expect(mocks.query).not.toHaveBeenCalled()
  })

  it('keeps an unresolved part and a missing or unvalidated target answer unavailable', async () => {
    mocks.query.mockResolvedValueOnce({ rows: [] })
    expect(await request()).toBeNull()
    mocks.consultation.mockResolvedValueOnce([{ id: answer, role: 'assistant', metadata_json: {} }])
    expect(await request()).toBeNull()
    expect(mocks.transcript).not.toHaveBeenCalled()
    mocks.transcript.mockResolvedValueOnce([])
    expect(await request()).toBeNull()
  })

  it('keeps correction archives on their historical reader path', async () => {
    mocks.archived.mockReturnValue(true)
    expect(await request()).toMatchObject({ answer: transcript, historical: true })
    expect(mocks.consultation).not.toHaveBeenCalled()
  })
})
