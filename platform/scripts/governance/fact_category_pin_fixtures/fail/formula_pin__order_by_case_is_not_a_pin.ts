// FAIL fixture (multi-formula rule): `formula_id` appears ONLY inside an ORDER BY CASE (a
// canonical-first rank). That orders the variants but neither pins one nor selects formula_id, so the
// reader cannot label the rows it serves: it is not a pin and not a disclosure. The scanner must not
// mistake the `formula_id = '...'` inside the CASE for a WHERE pin.
export async function mrityu(chart_id: string, ayanamsha_id: string) {
  const res = await query(
    `SELECT fact_subject, fact_value_num
       FROM chart_facts
      WHERE chart_id = $1 AND ayanamsha_id = $2
        AND fact_category = 'esoteric_point_mrityu'
        AND fact_key = 'longitude_sidereal'
      ORDER BY CASE WHEN formula_id = 'bphs_ch39' THEN 0 ELSE 1 END, fact_id`,
    [chart_id, ayanamsha_id],
  )
  return res.rows[0]
}
