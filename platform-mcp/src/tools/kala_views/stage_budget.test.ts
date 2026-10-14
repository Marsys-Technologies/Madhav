import { existsSync } from 'node:fs'
import { expect, it, vi } from 'vitest'
import { applyResponseBudget, finalizeMcpBudget } from '../../lib/response_budget.js'
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
it.each(['now','ahead','priority','elect','story','ritual','explain'] as const)(
  '%s actual stage response keeps its confirmed floor under an oversized budget', async view => {
    expect(existsSync(new URL('./stage_budget.ts', import.meta.url)), 'stage budget declaration missing').toBe(true)
    const { stageDensityBudgetSections } = await import('./stage_budget.js')
    const { composeView } = await import('../../../../platform/src/lib/retrieval/registry/layers/L3_kala/view_common')
    const result = composeView(view, 'fixture-chart', { manifest: { manifest_id: 'fixture-build', generation: '4.1' }, coverage: [], sources: [
      { table: 'kala_darshana', total: 30, rows: Array.from({ length: 30 }, (_, i) => ({ id: String(i), generation: '4.1',
        verification_pass_status: i < 3 ? 'two_pass_verified' : 'single', source_citation: `fixture:${i}`, narrative: 'x'.repeat(200) })) },
    ] })
    const content = { ...result, padding: 'x'.repeat(12000) }
    const sections = stageDensityBudgetSections(content)
    expect(sections).toEqual([expect.objectContaining({ minKeep: 3, hardFloor: true })])
    const budgeted = applyResponseBudget(content, 1, sections)
    expect(budgeted.content.rows).toHaveLength(3)
    expect(budgeted.content.rows.every(row => row.density === 'confirmed')).toBe(true)
    expect(budgeted.content).toMatchObject({ catalog_only_rows_in_page: 0, density: { confirmed: 3, catalog_only: 0 }, pagination: { returned: 3, more_available: true } })
    expect(budgeted.trim_report?.some(entry => entry.path === '(whole response)')).toBe(true)
    const finalized = finalizeMcpBudget(budgeted.content, { maxKb: 1, sections })
    expect(finalized.rows).toHaveLength(3)
    expect(finalized.rows.every(row => row.density === 'confirmed')).toBe(true)
  },
)
