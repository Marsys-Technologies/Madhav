// Phase O.4 — Cache Effectiveness page (USTAD_S4_1).
// Server component shell. AuthGate is enforced by the parent observatory
// layout; this page fetches the last-30-days cache analytics on the server
// and hands the JSON-serialized payload to the client-side panel.

import { getPool } from '@/lib/db/client'
import {
  queryCacheEffectiveness,
  toJson,
} from '@/lib/observatory/analytics/cache_effectiveness'
import { CacheEffectivenessPanel } from '@/lib/components/observatory/analytics/CacheEffectivenessPanel'
import { ObsPageShell } from '@/lib/components/observatory/shared'

export const dynamic = 'force-dynamic'

export default async function CacheEffectivenessPage() {
  const now = new Date()
  const start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  const date_start = start.toISOString()
  const date_end = now.toISOString()

  let dataJson = null
  let errorMessage: string | null = null
  try {
    const pool = await getPool()
    const result = await queryCacheEffectiveness(pool, { date_start, date_end })
    dataJson = toJson(result)
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : 'Failed to load cache analytics'
  }

  return (
    <ObsPageShell
      title="Cache Effectiveness"
      subtitle={`Last 30 days · ${date_start.slice(0, 10)} → ${date_end.slice(0, 10)}`}
    >
      <CacheEffectivenessPanel
        data={dataJson}
        error={errorMessage ? new Error(errorMessage) : null}
      />
    </ObsPageShell>
  )
}
