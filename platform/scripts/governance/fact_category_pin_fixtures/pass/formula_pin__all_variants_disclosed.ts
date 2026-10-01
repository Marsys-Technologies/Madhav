// PASS fixture (multi-formula rule): explicit all-variants disclosure -- formula_id is SELECTED and the
// ORDER BY is total (canonical-first rank, formula_id, fact_id). Every variant is served, labelled.
export async function karakas(chart_id: string) {
  const res = await query(
    `SELECT fact_id, fact_subject, fact_value_text, formula_id
       FROM chart_facts
      WHERE chart_id = $1 AND fact_category = 'karaka_chara_position' AND fact_key = 'assigned_graha'
      ORDER BY fact_subject,
               CASE WHEN formula_id = 'kn_rao_rahu_included' THEN 0 ELSE 1 END,
               formula_id, fact_id`,
    [chart_id],
  )
  return res.rows
}
