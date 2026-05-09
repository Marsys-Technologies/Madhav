// Cost per Quality — server component shell. AuthGate is enforced by the
// parent (super-admin) observatory layout; this page only assembles the
// 30-day default window and hands typed data to the client panel.

import {
  CostPerQualityPanel,
  type PanelStage,
} from '@/lib/components/observatory/analytics/CostPerQualityPanel'
import { getPool } from '@/lib/db/client'
import { queryCostPerQuality } from '@/lib/observatory/analytics/cost_per_quality'
import { ObsPageShell } from '@/lib/components/observatory/shared'

export const dynamic = 'force-dynamic'

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000

export default async function CostPerQualityPage() {
  const now = new Date()
  const dateEnd = now.toISOString()
  const dateStart = new Date(now.getTime() - THIRTY_DAYS_MS).toISOString()

  const pool = await getPool()
  const client = await pool.connect()
  let result
  try {
    result = await queryCostPerQuality(client, {
      date_start: dateStart,
      date_end: dateEnd,
    })
  } finally {
    client.release()
  }

  // bigint → string at the RSC/client boundary so the props are serializable.
  const stages: PanelStage[] = result.stages.map((s) => ({
    pipeline_stage: s.pipeline_stage,
    total_events: s.total_events,
    total_cost_usd: s.total_cost_usd,
    avg_cost_per_event_usd: s.avg_cost_per_event_usd,
    total_input_tokens: s.total_input_tokens.toString(),
    total_output_tokens: s.total_output_tokens.toString(),
    avg_latency_ms: s.avg_latency_ms,
    quality_score: s.quality_score,
  }))

  return (
    <ObsPageShell
      title="Cost per Quality"
      subtitle={`Pareto frontier across pipeline stages · ${result.date_start.slice(0, 10)} → ${result.date_end.slice(0, 10)}`}
      testId="cost-per-quality-page"
    >
      <CostPerQualityPanel
        date_start={result.date_start}
        date_end={result.date_end}
        quality_probe_wired={result.quality_probe_wired}
        stages={stages}
        totals={result.totals}
      />
    </ObsPageShell>
  )
}
