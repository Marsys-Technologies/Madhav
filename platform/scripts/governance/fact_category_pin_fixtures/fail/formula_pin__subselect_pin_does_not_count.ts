// FAIL fixture (multi-formula rule): `formula_id = ...` exists, but only inside a nested subselect.
// The OUTER read of the declared category is still unpinned.
export async function leaky(chart_id: string) {
  return query(
    `SELECT fact_value_num FROM chart_facts
      WHERE chart_id = $1 AND fact_category = 'esoteric_point_yogi' AND fact_key = 'longitude_sidereal'
        AND fact_subject IN (SELECT fact_subject FROM chart_facts WHERE formula_id = 'bphs_93_20')`,
    [chart_id],
  )
}
