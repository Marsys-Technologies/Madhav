/**
 * INF7-S2: cross_ayanamsha_consensus tests
 * [BUILD-ORCH-J-07]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('server-only', () => ({}))

import { query } from '@/lib/db/client'
import { cross_ayanamsha_consensus } from '../cross_ayanamsha_consensus'

const mockQuery = query as ReturnType<typeof vi.fn>

const CHART_ID = 'bbbbbbbb-0000-0000-0000-000000000001'

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
})

describe('cross_ayanamsha_consensus', () => {
  it('returns empty result when fewer than 2 ayanamshas available', async () => {
    const result = await cross_ayanamsha_consensus(CHART_ID, 'planets', ['lahiri'])
    expect(result.consensus_points).toEqual([])
    expect(result.divergence_points).toEqual([])
    expect(result.ayanamshas_queried).toEqual(['lahiri'])
  })

  it('returns consensus when all ayanamshas agree on a value', async () => {
    const rows = [
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'sign', ayanamsha_id: 'lahiri', fact_value_text: 'Capricorn', fact_value_num: null },
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'sign', ayanamsha_id: 'true_chitra', fact_value_text: 'Capricorn', fact_value_num: null },
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'sign', ayanamsha_id: 'raman', fact_value_text: 'Capricorn', fact_value_num: null },
    ]
    mockQuery
      .mockResolvedValueOnce({ rows, rowCount: 3 })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const result = await cross_ayanamsha_consensus(CHART_ID, 'planets', ['lahiri', 'true_chitra', 'raman'])
    const sunSign = result.consensus_points.find(
      (c) => c.fact_subject === 'SUN' && c.fact_key === 'sign',
    )
    expect(sunSign).toBeDefined()
    expect(sunSign?.agreed_value).toBe('Capricorn')
    expect(sunSign?.ayanamsha_count).toBe(3)
  })

  it('classifies divergent numeric facts (>= 1 deg threshold)', async () => {
    const rows = [
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'longitude', ayanamsha_id: 'lahiri', fact_value_text: null, fact_value_num: 280.5 },
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'longitude', ayanamsha_id: 'raman', fact_value_text: null, fact_value_num: 282.1 },
    ]
    mockQuery
      .mockResolvedValueOnce({ rows, rowCount: 2 })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const result = await cross_ayanamsha_consensus(CHART_ID, 'planets', ['lahiri', 'raman'])
    const divLon = result.divergence_points.find(
      (d) => d.fact_subject === 'SUN' && d.fact_key === 'longitude',
    )
    expect(divLon).toBeDefined()
    expect(divLon?.max_delta_deg).toBeCloseTo(1.6, 1)
  })

  it('ignores minor numeric drift below threshold (< 1 deg)', async () => {
    const rows = [
      { fact_category: 'planet_positions', fact_subject: 'MOON', fact_key: 'longitude', ayanamsha_id: 'lahiri', fact_value_text: null, fact_value_num: 100.1 },
      { fact_category: 'planet_positions', fact_subject: 'MOON', fact_key: 'longitude', ayanamsha_id: 'raman', fact_value_text: null, fact_value_num: 100.5 },
    ]
    mockQuery
      .mockResolvedValueOnce({ rows, rowCount: 2 })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const result = await cross_ayanamsha_consensus(CHART_ID, 'planets', ['lahiri', 'raman'])
    const moonDiv = result.divergence_points.find((d) => d.fact_subject === 'MOON' && d.fact_key === 'longitude')
    expect(moonDiv).toBeUndefined()
  })

  it('includes overall_divergence_score from chart_ayanamsha_reports', async () => {
    const reportRows = [
      { ayanamsha_id_1: 'lahiri', ayanamsha_id_2: 'raman', divergence_score: 0.3 },
      { ayanamsha_id_1: 'lahiri', ayanamsha_id_2: 'true_chitra', divergence_score: 0.1 },
    ]
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: reportRows, rowCount: 2 })

    const result = await cross_ayanamsha_consensus(CHART_ID, 'all', ['lahiri', 'raman', 'true_chitra'])
    expect(result.overall_divergence_score).toBeCloseTo(0.2, 2)
  })

  it('handles missing chart_ayanamsha_reports table gracefully', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockRejectedValueOnce(new Error('relation does not exist'))

    const result = await cross_ayanamsha_consensus(CHART_ID, 'all', ['lahiri', 'raman'])
    expect(result.overall_divergence_score).toBeNull()
  })

  it('builds ayanamsha_breakdown per requested ayanamsha', async () => {
    const rows = [
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'sign', ayanamsha_id: 'lahiri', fact_value_text: 'Capricorn', fact_value_num: null },
      { fact_category: 'planet_positions', fact_subject: 'SUN', fact_key: 'sign', ayanamsha_id: 'raman', fact_value_text: 'Capricorn', fact_value_num: null },
    ]
    mockQuery
      .mockResolvedValueOnce({ rows, rowCount: 2 })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const result = await cross_ayanamsha_consensus(CHART_ID, 'planets', ['lahiri', 'raman'])
    expect(result.ayanamsha_breakdown).toHaveLength(2)
    const lahiri = result.ayanamsha_breakdown.find((b) => b.ayanamsha_id === 'lahiri')
    expect(lahiri?.total_facts).toBe(1)
    expect(lahiri?.facts_in_consensus).toBe(1)
  })
})
