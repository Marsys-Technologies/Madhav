// PASS fixture (multi-formula rule): the two shapes the rule deliberately exempts -- a zero-row
// availability probe (LIMIT 0 selects no fact row) and an aggregate-only COUNT (selects no value) --
// plus a read of an UNDECLARED category, which needs no formula pin at all.
export async function probes(chart_id: string) {
  const probe = await query(
    `SELECT fact_id, fact_category, fact_key FROM chart_facts
      WHERE chart_id = $1 AND fact_category = ANY(ARRAY['karaka_chara_position', 'arudha_pada']::text[])
      ORDER BY fact_category LIMIT 0`,
    [chart_id],
  )
  const count = await query(
    `SELECT COUNT(*)::int AS total FROM chart_facts
      WHERE chart_id = $1 AND fact_category = 'esoteric_point_mrityu'`,
    [chart_id],
  )
  const plain = await query(
    `SELECT fact_value_text FROM chart_facts
      WHERE chart_id = $1 AND fact_category = 'graha_position' AND fact_key = 'sign'
      ORDER BY fact_subject`,
    [chart_id],
  )
  return { probe, count, plain }
}
