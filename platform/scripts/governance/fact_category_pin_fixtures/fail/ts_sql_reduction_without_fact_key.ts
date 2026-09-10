// FAIL fixture (F-C14, issue #1750): the ga_shadbala defect shape.
//
// A SQL template literal that reduces to ONE row with `ORDER BY ... LIMIT 1`
// but does NOT pin fact_key. Before F-C14 this was doubly invisible: TS SQL
// template literals were not scanned at all, and the rule accepted a bare
// reduction as independently sufficient.
//
// It must be flagged. `graha_shadbala_total` holds two incommensurable
// fact_keys -- every `ratio` (0.84-1.69) sorts below every `rupa` (4.64-8.47)
// -- so the MIN can never land in `rupa`, and the query reproducibly returns a
// ratio under a field named `shadbala_rupa`. Deterministic, stable, and wrong
// every single time: reproducibility is not correctness.
export async function weakestGraha(chart_id: string, ayanamsha_id: string) {
  const res = await query(
    `SELECT fact_subject, fact_value_num
       FROM chart_facts
      WHERE chart_id = $1 AND ayanamsha_id = $2
        AND fact_category = 'graha_shadbala_total'
      ORDER BY fact_value_num ASC
      LIMIT 1`,
    [chart_id, ayanamsha_id],
  )
  return res.rows[0]
}
