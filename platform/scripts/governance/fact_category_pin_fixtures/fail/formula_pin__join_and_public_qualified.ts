// FAIL fixture (multi-formula rule): chart_facts reached through a JOIN and through a `public.`-qualified
// FROM -- neither is a bare `FROM chart_facts`, and both read a declared category with no formula pin.
export async function viaJoin(chart_id: string) {
  const a = await query(
    `SELECT cf.fact_value_num FROM chart_registry r
       JOIN chart_facts cf ON cf.chart_id = r.chart_id
      WHERE r.chart_id = $1 AND cf.fact_category = 'esoteric_point_yogi' AND cf.fact_key = 'k'`,
    [chart_id],
  )
  const b = await query(
    `SELECT fact_value_num FROM public.chart_facts
      WHERE chart_id = $1 AND fact_category = 'esoteric_point_mrityu' AND fact_key = 'k'`,
    [chart_id],
  )
  return [a, b]
}
