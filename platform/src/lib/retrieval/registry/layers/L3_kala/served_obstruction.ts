/**
 * Which partition of `kala_obstruction` a served surface reads (SR-K9-WRITE-SCOPE).
 *
 * The table holds, for one chart, the legacy partition (`generation IS NULL`, rewritten in place by an
 * ordinary ka_vighnakara rebuild), the published head's generation and the private `candidate:<build>`
 * generations a K9 build is still writing. A served reader consumes exactly ONE: the head generation when
 * it holds rows, otherwise the legacy partition. A candidate is never served and the head REPLACES the
 * legacy rows instead of adding to them. Same rule as
 * platform/python-sidecar/services/kala_core/served_generation.py (pinned against it by
 * tests/l3/kala_db/ka_vighnakara/test_obstruction_served_partition.py).
 */

/** SQL predicate over `alias` (a kala_obstruction row): true exactly for the served partition. */
export function servedObstructionPredicate(alias: string): string {
  if (!/^[a-z_][a-z0-9_]*$/i.test(alias)) throw new Error('alias must be a plain identifier')
  return `${alias}.generation IS NOT DISTINCT FROM (`
    + `SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = ${alias}.chart_id `
    + `AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))`
}
