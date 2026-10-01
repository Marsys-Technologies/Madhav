// FAIL fixture (multi-formula rule): SQL held in a single-quoted TS string (not a backtick template).
export async function quoted(chart_id: string) {
  return query('SELECT fact_value_num FROM chart_facts WHERE chart_id = $1 AND fact_category = \'esoteric_point_yogi\' AND fact_key = \'k\'', [chart_id])
}
