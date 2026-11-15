import 'server-only'
import { query } from '@/lib/db/client'
import type { Queryable } from '@/lib/build/runPreparation'

/** Private Build data ports for the existing Cockpit run request.
 * The authorized caller keeps transaction lifetime, decisions and error mapping.
 * SQL, binds and call order remain the existing run contract. No job is invoked here.
 */

export function readRequestedAssetScope(scope_target: string) {
  return query<{ scope: string }>(
      'SELECT scope FROM asset_registry WHERE asset_id=$1',
      [scope_target]
    )
}

export function readBodhaRunPreconditions(chart_id: string) {
  return Promise.all([
      query<{ count: string }>(
        'SELECT count(*)::text AS count FROM chart_facts WHERE chart_id=$1',
        [chart_id]
      ),
      query<{ state: string }>(
        `SELECT state FROM asset_throughput WHERE chart_id=$1 AND asset_id='ga_structural'`,
        [chart_id]
      ),
      query<{ count: string }>(
        'SELECT count(*)::text AS count FROM brahma_remedy_corpus'
      ),
    ])
}

export function resetClearedRunAssetState(db: Queryable, chart_id: string, clearedAssetIds: string[]) {
  return db.query(
          `UPDATE asset_throughput
           SET state='dormant', last_built_at=NULL, rows_written=NULL,
               built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
               last_error=NULL
           WHERE chart_id=$1 AND asset_id = ANY($2::text[])`,
          [chart_id, clearedAssetIds]
        )
}

export function markClearedRunDownstreamStale(db: Queryable, chart_id: string, downstreamAssets: string[]) {
  return db.query(
          `UPDATE asset_throughput SET state='stale'
           WHERE chart_id=$1 AND asset_id = ANY($2::text[]) AND state IN ('lit','building','error')`,
          [chart_id, downstreamAssets]
        )
}

export function readClearedRunAssetMarker(chart_id: string, plan: string[]) {
  return query<{ asset_id: string }>(
        `SELECT asset_id FROM asset_throughput
          WHERE chart_id=$1 AND asset_id = ANY($2::text[])
            AND state='dormant' AND last_built_at IS NULL
          LIMIT 1`,
        [chart_id, plan],
      )
}
