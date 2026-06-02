/**
 * chart_facts_query.ts — TYPE STUB
 *
 * Implementation removed as part of legacy-teardown (feature/legacy-teardown).
 * Type preserved because router/types.ts uses ChartFactsQueryInput inline.
 * Rebuild during Layer-0 arc.
 */

export interface ChartFactsQueryInput {
  category?: string | string[]
  planet?: string
  house?: number
  sign?: string
  nakshatra?: string
  divisional_chart?: string
  keyword?: string
  limit?: number
  as_of_date?: string
  from_date?: string
  to_date?: string
  [key: string]: unknown
}
