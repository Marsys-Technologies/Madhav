import { query } from '@/lib/db/client'
import type { QueryResultRow } from 'pg'

/**
 * Read a keyed collection or a parameterized page. Keep fact identity in the
 * projection and reject scalar selection before executing the assembled SQL.
 * Callers supply trusted SQL fragments and bind user inputs as parameters.
 */
export function queryFactCollection<T extends QueryResultRow>(sql: string, params: unknown[]) {
  const structure = sql.replace(/'(?:[^']|'')*'/g, '?').trim()
  const projection = /^SELECT\s+([^]*?)\s+FROM\s+chart_facts\s+WHERE\b/i.exec(structure)?.[1]
  const columns = projection?.split(/,(?![^()]*\))/).map((column) => column.trim().toLowerCase())
  if (!columns?.includes('fact_id') || !columns.includes('fact_key')
    || structure.match(/\bSELECT\b/gi)?.length !== 1
    || /[;"'\\]|--|\/\*|\$(?:[a-z_][a-z_0-9]*)?\$|\b(?:distinct|group\s+by|fetch|union|intersect|except|having|over|into|for\s+update)\b/i.test(structure)
    || (/\b(?:limit|offset)\b/i.test(structure)
      && !/\bORDER\s+BY\s+(?:(?!\b(?:limit|offset)\b)[^])+\s+LIMIT\s+\$\d+\s+OFFSET\s+\$\d+$/i.test(structure))) {
    throw new Error('Expected a chart-fact collection with fact_id and fact_key')
  }

  return query<T>(sql, params)
}
