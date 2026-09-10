import { applyAutoBudgetToEnvelope } from '../lib/response_budget.js'

function oversizedRows() {
  return Array.from({ length: 80 }, (_, index) => ({
    id: index,
    detail: `row-${index}-${'x'.repeat(240)}`,
  }))
}

describe('F-46: shared auto-budget envelope finalization', () => {
  it('reports the applied budget and exposes recovery pointers at the public envelope after trimming', () => {
    const envelope: Record<string, unknown> = {
      tool: 'ganita_planet_get',
      drill_pointers: [],
      content: { rows: oversizedRows() },
    }

    applyAutoBudgetToEnvelope(envelope, 'ganita_planet_get', 4)

    expect(((envelope['content'] as Record<string, unknown>)['rows'] as unknown[]).length).toBeLessThan(80)
    expect(envelope['budget_kb_applied']).toBe(4)
    expect(envelope['trim_report']).toEqual(expect.arrayContaining([
      expect.objectContaining({ path: 'content.rows' }),
    ]))
    expect(envelope['drill_pointers']).toEqual(expect.arrayContaining([
      expect.objectContaining({ instrument: 'ganita_planet_get' }),
    ]))
  })

  it('preserves a pre-existing outer trim report when it records newly trimmed content', () => {
    const existing = {
      path: 'upstream.rows', original_count: 20, kept_count: 10,
      reason: 'upstream trim',
      recover_via: { instrument: 'ganita_chart_facts_get', hint: 'retrieve the supporting chart facts with a narrower page' },
    }
    const envelope: Record<string, unknown> = {
      tool: 'ganita_planet_get',
      drill_pointers: [],
      trim_report: [existing],
      content: { rows: oversizedRows() },
    }

    applyAutoBudgetToEnvelope(envelope, 'ganita_planet_get', 4)

    expect(envelope['trim_report']).toEqual(expect.arrayContaining([
      expect.objectContaining({ path: 'upstream.rows' }),
      expect.objectContaining({ path: 'content.rows' }),
    ]))
    expect(envelope['drill_pointers']).toEqual(expect.arrayContaining([
      expect.objectContaining({ instrument: 'ganita_chart_facts_get' }),
    ]))
  })
})
