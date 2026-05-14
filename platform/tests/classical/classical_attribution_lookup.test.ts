import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => mockQuery(...args),
}))

function makeAttrRow(overrides: Record<string, unknown> = {}) {
  return {
    attribution_id: 'attr-uuid-1',
    msr_signal_id: 'SIG.MSR.042',
    text_key: 'bphs',
    title: 'Brihat Parashara Hora Shastra',
    author: 'Parashara',
    chapter: '7',
    verse_range: '7.1',
    content: 'Rahu in the 7th causes partnership disruption.',
    attribution_type: 'confirms',
    confidence: 0.82,
    confidence_tier: 'HIGH',
    derivation_notes: 'Direct verse reference.',
    translation_cross_checked: true,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockResolvedValue({ rows: [] })
})

import { classical_attribution_lookup } from '@/lib/tools/classical_attribution_lookup'

describe('classical_attribution_lookup', () => {
  it('returns empty output for empty signal_ids', async () => {
    const result = await classical_attribution_lookup({ signal_ids: [] })
    expect(result.attributions).toHaveLength(0)
    expect(result.signal_ids_queried).toHaveLength(0)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns attributions with correct field mapping', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeAttrRow()] })
    const result = await classical_attribution_lookup({ signal_ids: ['SIG.MSR.042'] })
    const attr = result.attributions[0]
    expect(attr.msr_signal_id).toBe('SIG.MSR.042')
    expect(attr.text_key).toBe('bphs')
    expect(attr.attribution_type).toBe('confirms')
    expect(attr.confidence).toBeCloseTo(0.82)
    expect(attr.confidence_tier).toBe('HIGH')
    expect(attr.translation_cross_checked).toBe(true)
  })

  it('correctly partitions signal_ids_with_attributions and signal_ids_silent', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeAttrRow()] })
    const result = await classical_attribution_lookup({
      signal_ids: ['SIG.MSR.042', 'SIG.MSR.999'],
    })
    expect(result.signal_ids_with_attributions).toContain('SIG.MSR.042')
    expect(result.signal_ids_silent).toContain('SIG.MSR.999')
    expect(result.signal_ids_silent).not.toContain('SIG.MSR.042')
  })

  it('applies attribution_type filter in SQL when provided', async () => {
    await classical_attribution_lookup({
      signal_ids: ['SIG.MSR.042'],
      attribution_type: 'confirms',
    })
    const [sql, params] = mockQuery.mock.calls[0]
    expect(sql).toContain('ca.attribution_type =')
    expect(params).toContain('confirms')
  })

  it('applies confidence_tier filter in SQL when provided', async () => {
    await classical_attribution_lookup({
      signal_ids: ['SIG.MSR.042'],
      confidence_tier: 'HIGH',
    })
    const [sql, params] = mockQuery.mock.calls[0]
    expect(sql).toContain('ca.confidence_tier =')
    expect(params).toContain('HIGH')
  })

  it('passes all signal_ids as array param', async () => {
    const ids = ['SIG.MSR.001', 'SIG.MSR.002', 'SIG.MSR.003']
    await classical_attribution_lookup({ signal_ids: ids })
    const [, params] = mockQuery.mock.calls[0]
    expect(params[0]).toEqual(ids)
  })

  it('returns all queried signal_ids in signal_ids_queried', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeAttrRow()] })
    const result = await classical_attribution_lookup({
      signal_ids: ['SIG.MSR.042', 'SIG.MSR.100'],
    })
    expect(result.signal_ids_queried).toEqual(['SIG.MSR.042', 'SIG.MSR.100'])
  })
})
