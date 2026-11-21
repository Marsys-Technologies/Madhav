import 'server-only'
import { query } from '@/lib/db/client'
import * as columnPresence from '@/lib/db/columnPresence'
import type { BuildAction, BuildScope, RegistryEntry } from './plan'

export interface PreparationDurationSummary {
  sample_count: number
  last_seconds: number | null
  lower_seconds: number | null
  upper_seconds: number | null
}

export interface PhaseDurationBreakdown {
  compute_ms: number | null
  write_ms: number | null
  verify_ms: number | null
  publish_ms: number | null
  total_ms: number | null
  sample_runs: number
}

export interface PreparationDurationHistory extends PreparationDurationSummary {
  separate_layers?: { ganita: number | null; bodha: number | null }
  phase_breakdown?: PhaseDurationBreakdown
}

function sumNullable(a: number | null, b: number | null): number | null {
  if (a == null && b == null) return null
  return (a ?? 0) + (b ?? 0)
}

function combineBreakdowns(
  a: PhaseDurationBreakdown | undefined,
  b: PhaseDurationBreakdown | undefined,
): PhaseDurationBreakdown | undefined {
  if (!a && !b) return undefined
  if (!a) return b
  if (!b) return a
  const compute_ms = sumNullable(a.compute_ms, b.compute_ms)
  const write_ms = sumNullable(a.write_ms, b.write_ms)
  const verify_ms = sumNullable(a.verify_ms, b.verify_ms)
  const publish_ms = sumNullable(a.publish_ms, b.publish_ms)
  const total_ms = sumNullable(a.total_ms, b.total_ms)
  return {
    compute_ms,
    write_ms,
    verify_ms,
    publish_ms,
    total_ms,
    sample_runs: Math.min(a.sample_runs, b.sample_runs),
  }
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

  const hasPhaseProbe = Object.prototype.hasOwnProperty.call(columnPresence, 'phaseTelemetryColumnsPresent')
    && typeof columnPresence.phaseTelemetryColumnsPresent === 'function'
  const includePhaseTelemetry = hasPhaseProbe
    ? await columnPresence.phaseTelemetryColumnsPresent()
    : false

  async function readPhaseBreakdown(
    runScope: BuildScope,
    runTarget: string | null,
    plan: string[],
  ): Promise<PhaseDurationBreakdown | undefined> {
    if (!includePhaseTelemetry || plan.length === 0) return undefined
    const { rows } = await query<{
      sample_runs: number
      compute_ms: number | null
      write_ms: number | null
      verify_ms: number | null
      publish_ms: number | null
    }>(
      `SELECT count(*)::int AS sample_runs,
              ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY compute_ms))::int AS compute_ms,
              ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY write_ms))::int AS write_ms,
              ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY verify_ms))::int AS verify_ms,
              ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY publish_ms))::int AS publish_ms
         FROM (
           SELECT r.id,
                  SUM(a.compute_ms)::float8 AS compute_ms,
                  SUM(a.write_ms)::float8 AS write_ms,
                  SUM(a.verify_ms)::float8 AS verify_ms,
                  SUM(a.publish_ms)::float8 AS publish_ms
             FROM build_runs r
             JOIN build_run_assets a ON a.run_id = r.id
            WHERE r.chart_id = $1 AND r.state = 'completed' AND r.action = $2
              AND r.scope = $3 AND ($3 <> 'layer' OR r.scope_target = $4)
              AND r.plan @> to_jsonb($5::text[]) AND jsonb_array_length(r.plan) = cardinality($5::text[])
              AND r.ended_at > r.created_at AND r.resume_requested_at IS NULL
              AND a.asset_id = ANY($5::text[]) AND a.state = 'complete'
              AND a.disposition IS DISTINCT FROM 'skip_no_delta'
              AND (a.compute_ms IS NOT NULL OR a.write_ms IS NOT NULL OR a.verify_ms IS NOT NULL OR a.publish_ms IS NOT NULL)
            GROUP BY r.id, r.ended_at
            HAVING count(*) = cardinality($5::text[])
            ORDER BY r.ended_at DESC, r.id DESC LIMIT 20
         ) phase_runs`,
      [chartId, action, runScope, runTarget, plan],
    )
    const row = rows[0]
    if (!row || row.sample_runs <= 0) return undefined
    const phases = [row.compute_ms, row.write_ms, row.verify_ms, row.publish_ms].filter(
      (v): v is number => v != null,
    )
    if (phases.length === 0) return undefined
    return {
      compute_ms: row.compute_ms,
      write_ms: row.write_ms,
      verify_ms: row.verify_ms,
      publish_ms: row.publish_ms,
      total_ms: phases.reduce((acc, v) => acc + v, 0),
      sample_runs: row.sample_runs,
    }
  }

  const history = await read(scope, target, assets)
  if (!history) return undefined

  if (history.sample_count > 0) {
    const phase_breakdown = await readPhaseBreakdown(scope, target, assets)
    return phase_breakdown ? { ...history, phase_breakdown } : history
  }

  if (scope !== 'asset_set' || action !== 'rebuild') return history

  const planned = new Set(assets)
  const layerAssets = (layer: string) => registry
    .filter(asset => asset.layer === layer && planned.has(asset.asset_id))
    .map(asset => asset.asset_id)
  const ganitaAssets = layerAssets('ganita')
  const bodhaAssets = layerAssets('bodha')
  const [ganita, bodha, ganitaPhases, bodhaPhases] = await Promise.all([
    read('layer', 'ganita', ganitaAssets),
    read('layer', 'bodha', bodhaAssets),
    readPhaseBreakdown('layer', 'ganita', ganitaAssets),
    readPhaseBreakdown('layer', 'bodha', bodhaAssets),
  ])
  const phase_breakdown = combineBreakdowns(ganitaPhases, bodhaPhases)
  return {
    ...history,
    separate_layers: { ganita: ganita?.last_seconds ?? null, bodha: bodha?.last_seconds ?? null },
    ...(phase_breakdown ? { phase_breakdown } : {}),
  }
}
