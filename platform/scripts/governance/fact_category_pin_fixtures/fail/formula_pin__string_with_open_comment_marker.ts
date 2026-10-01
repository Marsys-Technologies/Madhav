// FAIL fixture (multi-formula rule): a string containing `/*` must not start a "comment" that erases the
// SQL below it up to the next real `*/`. (The previous blanker was not string-aware and hid this query.)
const hint = 'use /* here'
export async function hidden(chart_id: string) {
  return query(
    `SELECT fact_value_text FROM chart_facts WHERE chart_id = $1 AND fact_category = 'karaka_chara_position' AND fact_key = 'assigned_graha'`,
    [chart_id],
  )
}
/* a real comment, closed here */
