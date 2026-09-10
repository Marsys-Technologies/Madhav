// PASS fixture (F-C14, issue #1750): the same reduction, done correctly.
//
// Identical shape to fail/ts_sql_reduction_without_fact_key.ts except that it
// pins `fact_key = 'rupa'`. With the key pinned the ORDER BY sorts a single
// commensurable population, so the extremum means what the field name says.
// This is CLAUDE.md §N.7 item 2's conjunction: pin fact_key AND carry a total
// order -- not one or the other.
export async function weakestGraha(chart_id: string, ayanamsha_id: string) {
  const res = await query(
    `SELECT fact_subject, fact_value_num
       FROM chart_facts
      WHERE chart_id = $1 AND ayanamsha_id = $2
        AND fact_category = 'graha_shadbala_total'
        AND fact_key = 'rupa'
      ORDER BY fact_value_num ASC
      LIMIT 1`,
    [chart_id, ayanamsha_id],
  )
  return res.rows[0]
}
