export type ClearOp = { sql: string }

/**
 * Transforms a simple single-table count_sql into the equivalent DELETE statement.
 * Returns null if the count_sql doesn't follow the simple pattern (e.g., subquery sums).
 *
 * Handles both single-line and multiline count_sqls. The regex matches:
 *   SELECT count(*) [AS <alias>] FROM <rest>
 * and replaces only the SELECT...FROM prefix, leaving the WHERE clause intact.
 */
export function deriveDeleteSqlFromCountSql(countSql: string): string | null {
  const sql = countSql?.trim()
  if (!sql) return null
  const transformed = sql.replace(
    /^SELECT\s+count\(\*\)\s*(?:AS\s+\w+\s+)?FROM\b/i,
    'DELETE FROM'
  )
  if (transformed === sql) return null
  if (!transformed.trimStart().startsWith('DELETE FROM')) return null
  return transformed
}

/**
 * Explicit clear operations for assets whose count_sql can't be auto-transformed.
 * null means the asset has no data rows to clear (skip cleanly, not an error).
 */
export const EXPLICIT_CLEAR_OPS: Record<string, ClearOp[] | null> = {
  ga_pyjhora_engine: null,
  ga_condition: [
    { sql: 'DELETE FROM ga_condition_composite WHERE chart_id = $1' },
    { sql: "DELETE FROM chart_facts WHERE chart_id = $1 AND fact_category LIKE 'graha_avastha_%_per_varga'" },
  ],
}
