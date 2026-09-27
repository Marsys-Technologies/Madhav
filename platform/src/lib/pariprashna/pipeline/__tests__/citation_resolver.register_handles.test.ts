/**
 * Register-citation handle resolution in the live citation stream (Pūrṇa R2C.3b).
 *
 * REGISTER_CITATION_INSTRUCTION teaches the model to cite a fact register handle (F7) inline,
 * but the Portal's own citation grammar (citations/grammar.ts) deliberately treats a bare
 * `[[F7]]` as plain text, not a citation — it requires the `cite:` keyword. Before this fix a
 * register-cited handle therefore either rendered as a raw, unresolved bracket in reader prose
 * (bare form) or resolved `unverified` (cite: form, no source shaped to match an "Fn" ref at
 * all) even though the model cited a real, admitted finding. mergeRegisterHandleLabels closes
 * the second half: once the marker is recognized, the finding it names must resolve to a real
 * citation.
 */
import { describe, expect, it } from 'vitest'
import { buildTurnCitationResolver, mergeRegisterHandleLabels } from '../citation_resolver'

describe('mergeRegisterHandleLabels', () => {
  it('resolves a register handle to the finding it named, graded by materiality', () => {
    const labels = new Map<string, { reader_label: string; grade: 'primary' | 'supporting'; source_table: string; source_column: string }>()
    const registerHandleLabels = new Map([
      ['F1', { reader_label: 'Evidence finding for Wealth outlook', rationale: 'Semantic row at reviewed collection content.rows.', materiality: 'required' as const }],
      ['F2', { reader_label: 'Evidence finding for Career context', rationale: 'Opaque adapter item.', materiality: 'supporting' as const }],
    ])
    mergeRegisterHandleLabels(labels, registerHandleLabels)

    const resolver = buildTurnCitationResolver(labels)
    const required = resolver.resolve('F1')
    expect(required).toMatchObject({ ref: 'F1', reader_label: 'Evidence finding for Wealth outlook', grade: 'primary' })
    expect(required!.audit_detail).toContain('inquiry_fact_register')

    const supporting = resolver.resolve('F2')
    expect(supporting).toMatchObject({ ref: 'F2', grade: 'supporting' })
  })

  it('never overwrites a label the DB prefetch already resolved', () => {
    const labels = new Map([
      ['F1', { reader_label: 'DB-resolved label', grade: 'primary' as const, source_table: 'chart_facts', source_column: 'fact_id' }],
    ])
    mergeRegisterHandleLabels(labels, new Map([
      ['F1', { reader_label: 'Register label', rationale: 'x', materiality: 'required' as const }],
    ]))
    expect(labels.get('F1')?.source_table).toBe('chart_facts')
    expect(labels.get('F1')?.reader_label).toBe('DB-resolved label')
  })

  it('leaves an uncited or absent handle unresolved (honest null, never fabricated)', () => {
    const labels = new Map<string, { reader_label: string; grade: 'primary' | 'supporting'; source_table: string; source_column: string }>()
    mergeRegisterHandleLabels(labels, new Map([['F1', { reader_label: 'x', rationale: 'y', materiality: 'required' as const }]]))
    expect(buildTurnCitationResolver(labels).resolve('F99')).toBeNull()
  })

  it('is a no-op when the turn had no admitted evidence', () => {
    const labels = new Map<string, { reader_label: string; grade: 'primary' | 'supporting'; source_table: string; source_column: string }>()
    mergeRegisterHandleLabels(labels, null)
    expect(labels.size).toBe(0)
  })
})
