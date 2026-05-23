import { describe, test, expect } from 'vitest'
import { buildTraceSummary } from '../trace_summary'

describe('buildTraceSummary', () => {
  test('formats params canonically', () => {
    expect(
      buildTraceSummary('query_chart_facts', {
        category: 'planet',
        divisional_chart: 'D9',
        limit: 50,
      })
    ).toBe('query_chart_facts(category=planet, divisional_chart=D9, limit=50)')
  })

  test('truncates long values', () => {
    const longVal = 'a'.repeat(60)
    const result = buildTraceSummary('tool', { key: longVal })
    expect(result).toContain('...')
    expect(result.length).toBeLessThan(100)
    // value portion is capped at 50 chars (47 + '...')
    const match = result.match(/key=(.+)\)/)
    expect(match).not.toBeNull()
    expect(match![1].length).toBe(50)
  })

  test('handles empty params', () => {
    expect(buildTraceSummary('tool_health', {})).toBe('tool_health')
  })

  test('handles array params', () => {
    expect(
      buildTraceSummary('chart_summary', {
        divisional_charts: ['D1', 'D9', 'D10'],
      })
    ).toBe('chart_summary(divisional_charts=D1,D9,D10)')
  })

  test('filters out null and undefined params', () => {
    const result = buildTraceSummary('query_chart_facts', {
      category: 'planet',
      divisional_chart: null,
      limit: undefined,
    })
    expect(result).toBe('query_chart_facts(category=planet)')
  })

  test('handles multiple params in order', () => {
    const result = buildTraceSummary('vector_search', {
      query: 'Mars strength',
      top_k: 5,
    })
    expect(result).toBe('vector_search(query=Mars strength, top_k=5)')
  })
})
