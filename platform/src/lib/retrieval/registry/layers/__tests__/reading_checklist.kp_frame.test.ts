/**
 * SS N-356 — fetchKpCuspChain reads the KP chain in the KRISHNAMURTI frame WHATEVER id the caller
 * passes (KP stays on Krishnamurti by doctrine, SS N-342 item 3), and labels it.
 * The query layer is mocked; the real get_kp_cusps handler runs over the mock.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { fetchKpCuspChain } from '../reading_checklist'
import { KP_FRAME_AYANAMSHA, KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import { isKpChainRead, kpReadAyanamsha, kpRowsForHouses, recordedCalls, KP_CATEGORIES } from './kp_chain_fixture'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockImplementation(async () => ({ rows: kpRowsForHouses([2, 11]) }))
})

describe('fetchKpCuspChain: KP frame is unconditional', () => {
  const callerIds: Array<[string, string | null | undefined]> = [
    ['the Lahiri primary id', LAHIRI],
    ['no id (undefined)', undefined],
    ['null', null],
    ['the empty string', ''],
    ['"all"', 'all'],
    ['a nonsense alias', 'not_an_ayanamsha_xyz'],
    ['another stored id (raman)', 'raman'],
  ]

  it.each(callerIds)('reads the chain at krishnamurti when the caller passes %s', async (_name, id) => {
    const result = await fetchKpCuspChain(CHART_ID, id as string, [2, 11])
    const calls = recordedCalls(queryMock)
    expect(calls).toHaveLength(1)
    expect(isKpChainRead(calls[0]!)).toBe(true)
    expect(calls[0]!.params[2]).toEqual(KP_CATEGORIES)
    expect(kpReadAyanamsha(calls[0]!)).toBe('krishnamurti')
    expect(kpReadAyanamsha(calls[0]!)).toBe(KP_FRAME_AYANAMSHA)
    expect(calls.some(c => c.params.includes(LAHIRI))).toBe(false)
    expect(result.ayanamsha_id).toBe('krishnamurti')
    expect(result.available).toBe(true)
    expect(result.cusps.map(c => c.house)).toEqual([2, 11])
  })

  it('an empty chain (no KP rows) is still read at krishnamurti and still labelled', async () => {
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
    const result = await fetchKpCuspChain(CHART_ID, LAHIRI, [2, 11])
    expect(kpReadAyanamsha(recordedCalls(queryMock)[0]!)).toBe('krishnamurti')
    expect(result.cusps).toEqual([])
    expect(result.frame_label).toBe(KP_FRAME_LABEL)
    expect(result.note).toContain(KP_FRAME_LABEL)
  })
})

describe('fetchKpCuspChain: the frame label', () => {
  it('carries "KP frame (Krishnamurti ayanamsha)" in the chain text and the structured fields', async () => {
    const result = await fetchKpCuspChain(CHART_ID, LAHIRI, [2, 11])
    expect(KP_FRAME_LABEL).toBe('KP frame (Krishnamurti ayanamsha)')
    expect(result.frame_label).toBe('KP frame (Krishnamurti ayanamsha)')
    expect(result.ayanamsha_id).toBe('krishnamurti')
    expect(result.note.startsWith('KP frame (Krishnamurti ayanamsha). ')).toBe(true)
    // the labelled chain content is the served one, not a placeholder
    expect(result.cusps[0]).toMatchObject({ house: 2, star_lord: 'Mercury', sub_lord: 'Venus', significators: [2, 6, 10, 11] })
  })
})
