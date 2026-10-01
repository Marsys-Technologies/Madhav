// FAIL fixture (multi-formula rule): the word formula_id appears in the WHERE but only as `<>` and as a
// column-to-column comparison. Neither pins a formula; "any formula_id word in the WHERE" must not
// satisfy the rule.
export async function weak(chart_id: string) {
  const a = await query(
    `SELECT fact_value_num FROM chart_facts
      WHERE chart_id = $1 AND fact_category = 'esoteric_point_yogi' AND fact_key = 'k'
        AND formula_id <> 'alt_96_40' AND fact_id <> formula_id`,
    [chart_id],
  )
  return a
}
