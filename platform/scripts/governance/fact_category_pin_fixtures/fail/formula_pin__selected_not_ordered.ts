// FAIL fixture (multi-formula rule): formula_id is SELECTED but the ORDER BY does not include it, so
// the order of the variants within a (subject, key) is physical-order dependent: a half-disclosure.
// All-variants disclosure needs formula_id selected AND ordered by.
export async function karakas(chart_id: string) {
  const res = await query(
    `SELECT fact_subject, fact_value_text, formula_id
       FROM chart_facts
      WHERE chart_id = $1 AND fact_category = 'karaka_chara_position' AND fact_key = 'assigned_graha'
      ORDER BY fact_subject`,
    [chart_id],
  )
  return res.rows
}
