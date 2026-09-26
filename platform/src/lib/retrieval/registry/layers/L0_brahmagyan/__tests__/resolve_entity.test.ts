import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { resolveEntityCapability, AmbiguousEntityError } from '../resolve_entity'

type ResolveResult = { is_error: boolean; content: unknown }
const handler = resolveEntityCapability.handler as (
  args: Record<string, unknown>,
  ctx?: Record<string, unknown>
) => Promise<ResolveResult>

const ROW_SCHOOL = {
  canonical_id: 'phaladeepika',
  entity_class: 'school',
  canonical_name_en: 'Phaladeepika',
  canonical_name_sa: 'Phaladīpikā',
  synonyms: ['phaladeepika', 'phala deepika', 'mantreswara'],
  description: 'Mantreswara school',
  source_citation: 'test',
}
const ROW_TEXT = { ...ROW_SCHOOL, entity_class: 'text', synonyms: ['phaladeepika'] }
const ROW_VARGA_D9 = {
  canonical_id: 'd9',
  entity_class: 'varga',
  canonical_name_en: 'Navamsha',
  canonical_name_sa: 'Navamsha',
  synonyms: ['navamsa_chart', 'D9'],
  description: 'D-9 chart',
  source_citation: 'test',
}
const ROW_CONCEPT_NAVAMSA = {
  canonical_id: 'navamsa',
  entity_class: 'concept',
  canonical_name_en: 'Navamsa',
  canonical_name_sa: 'Navāṃśa',
  synonyms: ['navamsa', 'D9', 'navamsha'],
  description: 'D-9 concept',
  source_citation: 'test',
}

describe('resolveEntityCapability (W-L0-9 fail-closed polysemy)', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('declares the composite identity and the optional entity_class input', () => {
    expect(resolveEntityCapability.description).toContain('(entity_class, canonical_id)')
    expect(resolveEntityCapability.input_schema).toHaveProperty('entity_class')
    expect(resolveEntityCapability.required_inputs).toEqual(['name'])
  })

  it('single-row path is unchanged: returns the row, is_error false', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ canonical_id: 'saturn', entity_class: 'planet' }] })
    const result = await handler({ name: 'Shani' }, undefined)
    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ canonical_id: 'saturn', entity_class: 'planet' })
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params).toEqual(['Shani', null])
  })

  it('not-found path is unchanged: null-row shape with not_found flag', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await handler({ name: 'uranus' }, undefined)
    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ canonical_id: null, not_found: true, input: 'uranus' })
  })

  it('bare resolution of a multi-class name refuses loudly, naming both candidates', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ROW_SCHOOL, ROW_TEXT] })
    const result = await handler({ name: 'phaladeepika' }, undefined)
    expect(result.is_error).toBe(true)
    const msg = String(result.content)
    expect(msg).toContain('AmbiguousEntityError')
    expect(msg).toContain('school.phaladeepika')
    expect(msg).toContain('text.phaladeepika')
    expect(msg).toContain('entity_class')
  })

  it('class-qualified resolution succeeds within the class', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ROW_TEXT] })
    const result = await handler({ name: 'phaladeepika', entity_class: 'text' }, undefined)
    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ canonical_id: 'phaladeepika', entity_class: 'text' })
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('entity_class = $2')
    expect(mockQuery.mock.calls[0][1]).toEqual(['phaladeepika', 'text'])
  })

  it('multi-row within a supplied class still refuses (synonym collision inside one class)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ROW_SCHOOL, { ...ROW_SCHOOL, canonical_id: 'other' }] })
    const result = await handler({ name: 'x', entity_class: 'school' }, undefined)
    expect(result.is_error).toBe(true)
    expect(String(result.content)).toContain('AmbiguousEntityError')
  })

  it('Lane-A3 named exception: exactly one varga row in the match set wins (D9)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ROW_VARGA_D9, ROW_CONCEPT_NAVAMSA] })
    const result = await handler({ name: 'D9' }, undefined)
    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ canonical_id: 'd9', entity_class: 'varga' })
  })

  it('AmbiguousEntityError message carries the polysemy-registry pointer', () => {
    const err = new AmbiguousEntityError('kp', [ROW_SCHOOL, ROW_TEXT], null)
    expect(err.name).toBe('AmbiguousEntityError')
    expect(err.message).toContain('brahma_polysemy_registry')
    expect(err.message).toContain('Decision 16')
  })

  it('empty name stays a plain error', async () => {
    const result = await handler({ name: '  ' }, undefined)
    expect(result.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })
})
