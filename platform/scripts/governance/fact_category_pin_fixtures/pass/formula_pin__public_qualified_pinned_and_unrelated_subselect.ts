// PASS fixture (multi-formula rule): a `public.`-qualified read pinned to the canonical formula, with an
// unrelated nested subselect (it reads no declared category, so it needs no pin of its own).
export async function ok(chart_id: string) {
  return query(
    `SELECT fact_value_num FROM public.chart_facts
      WHERE chart_id = $1 AND fact_category = 'esoteric_point_yogi' AND fact_key = 'longitude_sidereal'
        AND formula_id = 'bphs_93_20'
        AND fact_subject IN (SELECT fact_subject FROM chart_facts WHERE fact_key = 'sign')`,
    [chart_id],
  )
}
