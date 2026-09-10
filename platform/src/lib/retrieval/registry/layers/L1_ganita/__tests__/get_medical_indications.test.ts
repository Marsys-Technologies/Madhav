/**
 * get_medical_indications.test.ts — F-E8 (L1_W1_ANALYSIS_BATCH_E.md, NOW, §N.6 items 3
 * and 4) unit tests. No live DB required — `query` is mocked.
 *
 * Before this fix: a 0-row response returned a populated-looking envelope (medical
 * disclaimer + provenance block) over an empty `rows` with no empty_reason field at all;
 * no density_contract; provenance.tables named only ga_medical, not the two upstream
 * authorities (chart_facts, bg_medical_mappings) the writer actually derives from.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getMedicalIndicationsCapability } from '../get_medical_indications'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getMedicalIndicationsCapability (ganita_medical_get)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('declares a density_contract with a genuine empty_reason claim (F-E8)', () => {
    expect(getMedicalIndicationsCapability.density_contract).toBeDefined()
    expect(getMedicalIndicationsCapability.density_contract?.empty_reason).toBe(true)
  })

  it('reports empty_reason with the applied filters named when genuinely zero rows match', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    const result = await getMedicalIndicationsCapability.handler({ chart_id: CHART_ID, graha: 'Mars', ayanamsha_id: 'raman' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(String(content['empty_reason'])).toMatch(/Mars/)
    expect(String(content['empty_reason'])).toMatch(/raman/)
  })

  it('omits empty_reason when rows are present', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ id: '1', graha: 'Sun' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })
    const result = await getMedicalIndicationsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['empty_reason']).toBeUndefined()
  })

  it('names both upstream authorities in provenance.tables, not just ga_medical (F-E8)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    const result = await getMedicalIndicationsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    const provenance = content['provenance'] as Record<string, unknown>
    expect(provenance['tables']).toEqual(['ga_medical', 'chart_facts', 'bg_medical_mappings'])
  })
})
