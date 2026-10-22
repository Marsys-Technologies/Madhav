import { expect, it, vi } from 'vitest'

const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))

// K9-WRITE-SCOPE F1 (migration 1405): kala_convergence now holds a K9 candidate's rows beside the served ones, so the
// served tool must restrict BOTH its page and its count to the served generation (the published head's, else legacy).
// Without that predicate it would serve a candidate's windows and double the family size.
it('kala_convergence_get restricts the page and the count to the served generation', async () => {
  db.mockResolvedValue({ rows: [{ total: '0' }] })
  const { queryConvergenceWindowsCapability } = await import('./query_convergence_windows')
  const result = await queryConvergenceWindowsCapability.handler!({ chart_id: 'chart' }, {})
  expect(result.is_error).toBe(false)
  expect(db).toHaveBeenCalledTimes(2)
  for (const [sql, params] of db.mock.calls as [string, unknown[]][]) {
    expect(sql).toContain('FROM kala_convergence')
    expect(sql).toContain("COALESCE(to_jsonb(kala_convergence)->>'generation', 'legacy') = COALESCE((SELECT generation FROM kala_layer_head WHERE chart_id = $1), 'legacy')")
    expect(params[0]).toBe('chart')
  }
})
