import 'server-only'
import { query } from '@/lib/db/client'
import { deriveChartReadiness } from './model'
import type { ChartReadiness, ReadinessRunRow, ReadinessThroughputRow } from './types'

type ThroughputRow = ReadinessThroughputRow & {
  chart_id: string
  last_built_at: string | null
}

type LatestRunRow = ReadinessRunRow & {
  chart_id: string
  action: string
  created_at: string
  started_at: string | null
  ended_at: string | null
}

export async function getChartReadinessMap(chartIds: string[]): Promise<Map<string, ChartReadiness>> {
  if (chartIds.length === 0) return new Map()
  const [throughput, runs, failures] = await Promise.all([
    query<ThroughputRow>(
      `SELECT at.chart_id, at.asset_id, at.state, at.rows_written, at.last_built_at
         FROM asset_throughput at
         JOIN asset_registry ar ON ar.asset_id = at.asset_id AND ar.is_active = true
        WHERE at.chart_id = ANY($1::uuid[])`,
      [chartIds],
    ),
    // Latest run of any kind and any state (a failed dispatch must be visible),
    // with its planned assets for serving-impact classification — read once per
    // chart for the latest run only.
    query<LatestRunRow>(
      `SELECT l.*,
              ARRAY(SELECT bra.asset_id FROM build_run_assets bra WHERE bra.run_id = l.id ORDER BY bra.position) AS planned_assets
         FROM (
           SELECT DISTINCT ON (r.chart_id)
                  r.id, r.chart_id, r.state, r.scope, r.action, r.last_error, r.created_at, r.started_at, r.ended_at
             FROM build_runs r
            WHERE r.chart_id = ANY($1::uuid[])
            ORDER BY r.chart_id, r.created_at DESC, r.id DESC
         ) l`,
      [chartIds],
    ),
    // Failed/stopped runs of any age that still own broken active per-chart
    // assets. A full rebuild or a started preparation through both Gaṇita and
    // Bodha can leave mixed generations. An old lit marker cannot clear that failure.
    query<{ chart_id: string; assets: number; dispatch_failed: boolean; unsafe_preparation: boolean }>(
      `SELECT r.chart_id,
              COUNT(DISTINCT bra.asset_id)::int AS assets,
              COALESCE(bool_or(r.last_error LIKE 'JOB_DISPATCH_FAILED%'), false) AS dispatch_failed,
              bool_or(r.started_at IS NOT NULL AND ar.layer IN ('ganita', 'bodha')) AS unsafe_preparation
         FROM build_runs r
         JOIN build_run_assets bra ON bra.run_id = r.id
         JOIN asset_registry ar ON ar.asset_id = bra.asset_id AND ar.is_active = true AND ar.scope = 'per_chart'
         LEFT JOIN asset_throughput at ON at.chart_id = r.chart_id AND at.asset_id = bra.asset_id
        WHERE r.chart_id = ANY($1::uuid[])
          AND r.state IN ('failed', 'stopped')
          AND NOT COALESCE(
                at.state = 'lit'
                AND (NOT (r.scope = 'global' AND r.action = 'rebuild') OR at.last_built_at >= r.created_at)
                AND (
                  NOT (
                    r.scope = 'asset_set' AND r.started_at IS NOT NULL
                      AND COALESCE(r.scope_target ~ '(^|,)ga_positions(,|$)', false)
                      AND COALESCE(r.scope_target ~ '(^|,)bo_laksana(,|$)', false)
                  )
                  OR bra.state = 'complete'
                  OR EXISTS (
                    SELECT 1
                      FROM build_runs recovered
                      JOIN build_run_assets receipt ON receipt.run_id = recovered.id
                     WHERE recovered.chart_id = r.chart_id AND recovered.created_at > r.created_at
                       AND recovered.state = 'completed' AND receipt.state = 'complete'
                       AND receipt.asset_id = bra.asset_id
                  )
                ),
                false)
        GROUP BY r.chart_id`,
      [chartIds],
    ),
  ])
  return new Map(
    chartIds.map((id) => {
      const failure = failures.rows.find((row) => row.chart_id === id)
      return [
        id,
        deriveChartReadiness({
          throughput: throughput.rows.filter((row) => row.chart_id === id),
          latestRun: runs.rows.find((row) => row.chart_id === id) ?? null,
          unresolvedFailure: failure
            ? {
                assets: Number(failure.assets),
                dispatchFailed: Boolean(failure.dispatch_failed),
                unsafePreparation: Boolean(failure.unsafe_preparation),
              }
            : { assets: 0, dispatchFailed: false },
        }),
      ]
    }),
  )
}
