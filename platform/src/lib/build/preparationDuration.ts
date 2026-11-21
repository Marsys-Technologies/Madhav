import 'server-only'
import { query } from '@/lib/db/client'
import type { BuildAction, BuildScope, RegistryEntry } from './plan'

export interface PreparationDurationSummary {
  sample_count: number
  last_seconds: number | null
  lower_seconds: number | null
  upper_seconds: number | null
}

export interface PreparationDurationHistory extends PreparationDurationSummary {
  separate_layers?: { ganita: number | null; bodha: number | null }
}

export async function readPreparationDuration({
  chartId, action, scope, target, assets, registry,
}: {
  chartId: string
  action: BuildAction
  scope: BuildScope
  target: string | null
  assets: string[]
  registry: RegistryEntry[]
}): Promise<PreparationDurationHistory | undefined> {
  async function read(runScope: BuildScope, runTarget: string | null, plan: string[]) {
    if (plan.length === 0) return undefined
    const { rows } = await query<PreparationDurationSummary>(
      `SELECT count(*)::int AS sample_count,
              (array_agg(elapsed ORDER BY ended_at DESC, id DESC))[1] AS last_seconds,
              PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY elapsed) AS lower_seconds,
              PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY elapsed) AS upper_seconds
         FROM (
           SELECT r.id, r.ended_at, EXTRACT(EPOCH FROM (r.ended_at - r.created_at))::float8 AS elapsed
             FROM build_runs r
            WHERE r.chart_id = $1 AND r.state = 'completed' AND r.action = $2
              AND r.scope = $3 AND ($3 <> 'layer' OR r.scope_target = $4)
              AND r.plan @> to_jsonb($5::text[]) AND jsonb_array_length(r.plan) = cardinality($5::text[])
              AND r.ended_at > r.created_at AND r.resume_requested_at IS NULL
              AND (SELECT count(*) FROM build_run_assets a WHERE a.run_id = r.id
                      AND a.asset_id = ANY($5::text[]) AND a.state = 'complete'
                      AND a.disposition IS DISTINCT FROM 'skip_no_delta') = cardinality($5::text[])
            ORDER BY r.ended_at DESC, r.id DESC LIMIT 20
         ) recent`,
      [chartId, action, runScope, runTarget, plan],
    )
    return rows[0]
  }

  const history = await read(scope, target, assets)
  if (!history || history.sample_count > 0 || scope !== 'asset_set' || action !== 'rebuild') return history

  const planned = new Set(assets)
  const layerAssets = (layer: string) => registry
    .filter(asset => asset.layer === layer && planned.has(asset.asset_id))
    .map(asset => asset.asset_id)
  const [ganita, bodha] = await Promise.all([
    read('layer', 'ganita', layerAssets('ganita')),
    read('layer', 'bodha', layerAssets('bodha')),
  ])
  return { ...history, separate_layers: { ganita: ganita?.last_seconds ?? null, bodha: bodha?.last_seconds ?? null } }
}
