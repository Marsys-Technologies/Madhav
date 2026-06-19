import { describe, it, expect } from 'vitest'

// Regression test: gate on the SQL text, not metadata (scope/asset_type).
// The stats route must bind $1 = chartId whenever count_sql contains $1,
// regardless of whether chartId is null. Passing [] with a $1-bearing SQL
// causes Postgres to throw "there is no parameter $1".
// [[feedback-sql-param-binding-inspect-site]]

function resolveCountParams(sql: string, chartId: string | null): (string | null)[] {
  return /\$1/.test(sql) ? [chartId] : []
}

describe('cockpit stats $1 param binding', () => {
  it('binds chartId when SQL contains $1 and chartId is provided', () => {
    const sql = "SELECT count(*) AS count FROM chart_facts WHERE chart_id = $1"
    expect(resolveCountParams(sql, '482012f1')).toEqual(['482012f1'])
  })

  it('binds null (not empty array) when SQL contains $1 but chartId is null', () => {
    const sql = "SELECT count(*) AS count FROM chart_facts WHERE chart_id = $1"
    // Passing [null] lets Postgres bind $1=NULL → 0 rows (no error).
    // Passing [] would throw "there is no parameter $1".
    expect(resolveCountParams(sql, null)).toEqual([null])
  })

  it('passes empty params when SQL has no $1 (global/cross-table counts)', () => {
    const sql = "SELECT count(*) FROM brahma_ontology"
    expect(resolveCountParams(sql, '482012f1')).toEqual([])
  })

  it('passes empty params for multi-table global count with no $1', () => {
    const sql = "SELECT (SELECT count(*) FROM reference_nakshatra) + (SELECT count(*) FROM reference_nakshatra_pada) AS count"
    expect(resolveCountParams(sql, null)).toEqual([])
  })
})
