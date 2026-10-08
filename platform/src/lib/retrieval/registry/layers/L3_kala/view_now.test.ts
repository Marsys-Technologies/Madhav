import { existsSync } from 'node:fs'
import { expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
it('NOW reads stored stages and manifest, preserves nulls/roots and separate density', async () => {
  expect(existsSync(new URL('./view_now.ts', import.meta.url))).toBe(true)
  const { nowViewCapability } = await import('./view_now')
  db.mockResolvedValue({ rows: [{ manifest: { manifest_id: 'build', generation: '4.1' }, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', assertion: {
      assertion_id: 'a1', operator_role: 'scored', role: 'corroborates',
      roots: { fact_ids: ['f1'], contact_ids: ['c1'], record_ids: [] },
      payload: { effective_state: 'obstruction_cancelled', release: { kind: 'unknown', instant: null } },
    } }] },
  ] }] })
  const result = await nowViewCapability.handler!({ chart_id: 'chart', at: '2026-10-09T10:00:00Z' }, {})
  expect(result.content).toMatchObject({ view: 'now', manifest_id: 'build', empty_reason: null,
    density: { confirmed: 1, testimony: 0, catalog_only: 0 },
    rows: [{ data: { assertion: { roots: { contact_ids: ['c1'] }, payload: { release: { instant: null } } } },
      drill: { args: { assertion_id: 'a1' } } }],
  })
  const [sql, params] = db.mock.calls[0]
  for (const table of ['kala_darshana', 'kala_obstruction']) expect(sql).toContain(table)
  expect(sql).toContain('kala_layer_head')
  expect(sql).toContain("c.state = 'published'")
  expect(params[0]).toBe('chart')
  expect(nowViewCapability.density_contract).toMatchObject({ paginated: true, empty_reason: true,
    facets: ['confirmed', 'testimony', 'catalog_only', 'context_only'] })
})
