/**
 * lel_intake_checklist — unit tests (EL-54, Elevation Campaign v2.1 Lane γ.J)
 * ==============================================================================
 * DB is mocked — no live connection required.
 */
import { describe, it, expect, vi } from 'vitest'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

const FAKE_ONTOLOGY = [
  { event_class_id: 'major_gain', name_en: 'Major Financial Gain', domain: 'wealth', lel_category: 'finance', temporal_shape: 'interval', evidence_requirements: { verification_sources: ['bank credit record'], self_report_risk: 'low', externally_verifiable: true } },
  { event_class_id: 'major_loss', name_en: 'Major Financial Loss', domain: 'wealth', lel_category: 'loss', temporal_shape: 'interval', evidence_requirements: { verification_sources: ['loss documentation'], self_report_risk: 'low', externally_verifiable: true } },
  { event_class_id: 'marriage', name_en: 'Marriage', domain: 'relationship', lel_category: 'relationship', temporal_shape: 'point', evidence_requirements: { verification_sources: ['marriage certificate'], self_report_risk: 'low', externally_verifiable: true } },
  { event_class_id: 'spiritual_turn', name_en: 'Spiritual Turn', domain: 'spirituality', lel_category: 'spiritual', temporal_shape: 'interval', evidence_requirements: { verification_sources: [], self_report_risk: 'high', externally_verifiable: false } },
]

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('FROM brahma_event_ontology')) return { rows: FAKE_ONTOLOGY }
    if (sql.includes('FROM life_events')) return { rows: [{ domain: 'finance', total: '3' }] }
    return { rows: [] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'
import { lelIntakeChecklistCapability } from '../lel_intake_checklist'

describe('lel_intake_checklist — descriptor shape', () => {
  it('is per_chart, requires chart_id, lel_capable, NOT calibration_context_only', () => {
    expect(lelIntakeChecklistCapability.scope).toBe('per_chart')
    expect(lelIntakeChecklistCapability.required_inputs).toContain('chart_id')
    expect(lelIntakeChecklistCapability.lel_capable).toBe(true)
    // F-R7's calibration_context_only is for outcome/LEL-READ context-supply tools; this is an
    // LEL-WRITE-assistance tool, the opposite direction, so it deliberately does not carry the flag.
    expect(lelIntakeChecklistCapability.calibration_context_only).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(lelIntakeChecklistCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('lel_intake_checklist — mode=checklist', () => {
  it('errors when chart_id is absent', async () => {
    const result = await lelIntakeChecklistCapability.handler({}, {})
    expect(result.is_error).toBe(true)
  })

  it('groups event classes by domain, grounded in brahma_event_ontology (never invented)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({ chart_id: CHART_A }, {})
    expect(result.is_error).toBe(false)
    const content = result.content as { domains: Array<{ domain: string; event_classes: unknown[] }> }
    const wealthDomain = content.domains.find(d => d.domain === 'wealth')
    expect(wealthDomain).toBeDefined()
    expect(wealthDomain!.event_classes).toHaveLength(2)
  })

  it('flags domains under the 3-5 target honestly instead of padding', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({ chart_id: CHART_A }, {})
    const content = result.content as { domains: Array<{ domain: string; under_target_count_note: string | null }> }
    const marriageDomain = content.domains.find(d => d.domain === 'relationship')
    expect(marriageDomain!.under_target_count_note).toContain('Honest gap')
  })

  it('required_fields differ by temporal_shape (point vs interval)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({ chart_id: CHART_A }, {})
    const content = result.content as { domains: Array<{ domain: string; event_classes: Array<{ event_class_id: string; required_fields: string[] }> }> }
    const marriage = content.domains.find(d => d.domain === 'relationship')!.event_classes.find(c => c.event_class_id === 'marriage')!
    expect(marriage.required_fields).toContain('event_date')
    const gain = content.domains.find(d => d.domain === 'wealth')!.event_classes.find(c => c.event_class_id === 'major_gain')!
    expect(gain.required_fields).toContain('interval_start')
    expect(gain.required_fields).toContain('interval_end')
  })
})

describe('lel_intake_checklist — mode=validate (never invents content)', () => {
  it('rejects an entry missing description as an error, never fills it in', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({
      chart_id: CHART_A, mode: 'validate',
      entries: [{ event_class: 'marriage', event_date: '2013-12-11', category: 'relationship', source_citation: 'native-disclosed' }],
    }, {})
    expect(result.is_error).toBe(false)
    const content = result.content as { results: Array<{ valid: boolean; errors: string[] }> }
    expect(content.results[0]!.valid).toBe(false)
    expect(content.results[0]!.errors.some(e => e.includes('description'))).toBe(true)
  })

  it('rejects a placeholder description as invalid, not as a pass', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({
      chart_id: CHART_A, mode: 'validate',
      entries: [{ event_class: 'marriage', event_date: '2013-12-11', category: 'relationship', description: 'TBD', source_citation: 'native-disclosed' }],
    }, {})
    const content = result.content as { results: Array<{ valid: boolean; errors: string[] }> }
    expect(content.results[0]!.valid).toBe(false)
    expect(content.results[0]!.errors.some(e => e.includes('placeholder'))).toBe(true)
  })

  it('rejects an unknown event_class rather than accepting an invented one', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({
      chart_id: CHART_A, mode: 'validate',
      entries: [{ event_class: 'made_up_class', event_date: '2020-01-01', category: 'x', description: 'real content', source_citation: 'native-disclosed' }],
    }, {})
    const content = result.content as { results: Array<{ valid: boolean; errors: string[] }> }
    expect(content.results[0]!.valid).toBe(false)
    expect(content.results[0]!.errors.some(e => e.includes('not a known event class'))).toBe(true)
  })

  it('accepts a fully-specified, real entry', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({
      chart_id: CHART_A, mode: 'validate',
      entries: [{
        event_class: 'marriage', domain: 'relationship', event_date: '2013-12-11',
        category: 'relationship', description: 'Married childhood partner.',
        source_citation: 'native-disclosed, 2026-07-25',
      }],
    }, {})
    const content = result.content as { results: Array<{ valid: boolean; errors: string[] }>; entries_valid: number }
    expect(content.results[0]!.valid).toBe(true)
    expect(content.entries_valid).toBe(1)
  })

  it('errors when entries[] is missing in validate mode (no silent no-op)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await lelIntakeChecklistCapability.handler({ chart_id: CHART_A, mode: 'validate' }, {})
    expect(result.is_error).toBe(true)
  })

  it('never issues an INSERT/UPDATE against life_events — validate is read-only', async () => {
    vi.mocked(mockQuery).mockClear()
    await lelIntakeChecklistCapability.handler({
      chart_id: CHART_A, mode: 'validate',
      entries: [{ event_class: 'marriage', event_date: '2013-12-11', category: 'relationship', description: 'real', source_citation: 'x' }],
    }, {})
    const calls = vi.mocked(mockQuery).mock.calls
    expect(calls.every(c => !/INSERT|UPDATE|DELETE/i.test(String(c[0])))).toBe(true)
  })
})
