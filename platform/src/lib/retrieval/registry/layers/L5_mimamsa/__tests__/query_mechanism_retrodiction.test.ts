/**
 * query_mechanism_retrodiction — unit tests
 * ===========================================
 * DOCTRINE-WAVES D-4b Lane B-5 (= BRIEF_D4.md v2.0 Lane C-6).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryMechanismRetrodictionCapability } from '../query_mechanism_retrodiction'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('mechanism_retrodiction_get — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryMechanismRetrodictionCapability.uri).toBe('marsys://tool/L5/mechanism_retrodiction_get')
    expect(queryMechanismRetrodictionCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryMechanismRetrodictionCapability.required_inputs).toContain('chart_id')
    const schema = queryMechanismRetrodictionCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('is flagged calibration_context_only + lel_capable (NO-LEAKAGE arms 2 & 4)', () => {
    expect(queryMechanismRetrodictionCapability.calibration_context_only).toBe(true)
    expect(queryMechanismRetrodictionCapability.lel_capable).toBe(true)
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryMechanismRetrodictionCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('mechanism_retrodiction_get — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryMechanismRetrodictionCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('rejects an out-of-range house filter without querying the DB', async () => {
    const result = await queryMechanismRetrodictionCapability.handler({ chart_id: CHART_A, house: 13 }, undefined)
    expect(result.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('errors honestly (not a silent empty) when the LAGNA fact is missing', async () => {
    vi.mocked(mockQuery).mockResolvedValueOnce({ rows: [] } as never)
    const result = await queryMechanismRetrodictionCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(true)
    expect(JSON.stringify(result.content)).toContain('LAGNA sign not resolvable')
  })

  it('sealed test split: SQL binds the 2020-01-01 cutoff as a parameter, not caller-settable', async () => {
    vi.mocked(mockQuery)
      .mockResolvedValueOnce({ rows: [{ lagna_sign: 'Aries', lagna_fact_id: 'FACT-LAGNA-1' }] } as never)
      .mockResolvedValueOnce({ rows: [] } as never)

    await queryMechanismRetrodictionCapability.handler(
      { chart_id: CHART_A, date_from: '2025-01-01', date_to: '2030-01-01' }, // caller cannot widen the split
      undefined,
    )

    const secondCall = vi.mocked(mockQuery).mock.calls[1]
    expect(String(secondCall?.[0])).toContain('event_date < $3::date')
    expect(secondCall?.[1]).toContain('2020-01-01')
  })

  it('confirms a house-2 (wealth) firing when the house lord is the active MD, honestly separates non-firing and unmapped events', async () => {
    // Aries Lagna: house 2 = Taurus (lord Venus), house 10 = Capricorn (lord Saturn).
    vi.mocked(mockQuery)
      .mockResolvedValueOnce({ rows: [{ lagna_sign: 'Aries', lagna_fact_id: 'FACT-LAGNA-1' }] } as never)
      .mockResolvedValueOnce({
        rows: [
          // Confirmed: wealth event during a Venus MD (house 2 lord).
          {
            event_id: 'EV-1', event_date: '1995-06-01', domain: 'finance/family_windfall',
            description: 'windfall', significance: 'major',
            lord_graha: 'Venus', level_n: 1, dasha_row_id: 'DASHA-1',
            dasha_start: '1991-08-17', dasha_end: '2010-08-17',
          },
          // Not confirmed: career event but NO active dasha row (lord_graha null from LEFT JOIN).
          {
            event_id: 'EV-2', event_date: '2005-01-01', domain: 'career/first_job_joined',
            description: 'job', significance: 'moderate',
            lord_graha: null, level_n: null, dasha_row_id: null,
            dasha_start: null, dasha_end: null,
          },
          // Unmapped domain prefix.
          {
            event_id: 'EV-3', event_date: '1984-02-05', domain: 'other/birth',
            description: 'birth', significance: 'major',
            lord_graha: null, level_n: null, dasha_row_id: null,
            dasha_start: null, dasha_end: null,
          },
        ],
      } as never)

    const result = await queryMechanismRetrodictionCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>

    const mechanisms = content['mechanisms'] as Array<Record<string, unknown>>
    expect(mechanisms).toHaveLength(1)
    expect(mechanisms[0]?.['house']).toBe(2)
    expect(mechanisms[0]?.['house_lord']).toBe('Venus')
    expect(mechanisms[0]?.['fired_count']).toBe(1)
    const firedEvents = mechanisms[0]?.['fired_events'] as Array<Record<string, unknown>>
    expect(firedEvents[0]?.['event_id']).toBe('EV-1')
    expect(firedEvents[0]?.['dasha_level']).toBe('MD')

    const notConfirmed = content['not_confirmed_events'] as Array<Record<string, unknown>>
    expect(notConfirmed.map((e) => e['event_id'])).toEqual(['EV-2'])

    const unmapped = content['unmapped_events'] as Array<Record<string, unknown>>
    expect(unmapped.map((e) => e['event_id'])).toEqual(['EV-3'])

    // Never prediction input — the usage note says so explicitly.
    expect(String(content['usage_note'])).toMatch(/CONFIRMATION ONLY/)
    expect(String(content['usage_note'])).toMatch(/never use as prediction input/i)
  })

  it('domain filter narrows to the requested prefix only', async () => {
    vi.mocked(mockQuery)
      .mockResolvedValueOnce({ rows: [{ lagna_sign: 'Aries', lagna_fact_id: 'FACT-LAGNA-1' }] } as never)
      .mockResolvedValueOnce({
        rows: [
          {
            event_id: 'EV-1', event_date: '1995-06-01', domain: 'finance/family_windfall',
            description: 'windfall', significance: 'major',
            lord_graha: 'Venus', level_n: 1, dasha_row_id: 'DASHA-1',
            dasha_start: '1991-08-17', dasha_end: '2010-08-17',
          },
          {
            event_id: 'EV-2', event_date: '2005-01-01', domain: 'career/first_job_joined',
            description: 'job', significance: 'moderate',
            lord_graha: 'Saturn', level_n: 1, dasha_row_id: 'DASHA-2',
            dasha_start: '1991-08-17', dasha_end: '2010-08-17',
          },
        ],
      } as never)

    const result = await queryMechanismRetrodictionCapability.handler({ chart_id: CHART_A, domain: 'career' }, undefined)
    const content = result.content as Record<string, unknown>
    const mechanisms = content['mechanisms'] as Array<Record<string, unknown>>
    expect(mechanisms).toHaveLength(1)
    expect(mechanisms[0]?.['house']).toBe(10)
    expect(mechanisms[0]?.['house_lord']).toBe('Saturn')
  })
})
