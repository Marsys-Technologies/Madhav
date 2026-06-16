import Link from 'next/link'
import { fetchBuildState } from '@/lib/build/dataSource'
import { CockpitGrid } from '@/components/build/CockpitGrid'
import { stalenessLabel } from '@/lib/build/format'

export const dynamic = 'force-dynamic'

export default async function BuildCockpitPage() {
  let state = null
  try {
    state = await fetchBuildState()
  } catch {
    // GCS bucket unavailable — render page in degraded mode
  }

  const stale = state ? stalenessLabel(state.staleness_seconds_since_last_close) : null

  // Health summary: any non-zero exit, overdue red-team, overdue quarterly = amber.
  const lastDrift = state?.governance.scripts_trend.drift_detector.at(-1)?.exit_code ?? 0
  const lastSchema = state?.governance.scripts_trend.schema_validator.at(-1)?.exit_code ?? 0
  const lastMirror = state?.governance.scripts_trend.mirror_enforcer.at(-1)?.exit_code ?? 0
  const healthy = lastDrift === 0 && lastSchema === 0 && lastMirror === 0
  const healthLabel = healthy ? 'System health ✓' : 'System health · attention'
  const healthClass = healthy ? 'text-muted-foreground' : 'text-amber-600 dark:text-amber-400'

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <div className="mb-6 flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="bt-display">Build Cockpit</h1>
        <div className="flex items-baseline gap-4">
          {stale && (
            <span className="bt-body text-muted-foreground">
              Last close · {stale}
            </span>
          )}
          {state && (
            <Link href="/build/health" className={`bt-body hover:underline ${healthClass}`}>
              {healthLabel}
            </Link>
          )}
        </div>
      </div>
      {state ? (
        <CockpitGrid state={state} />
      ) : (
        <div className="rounded-md border border-border bg-muted/40 px-4 py-8 text-center text-sm text-muted-foreground">
          Build tracker data unavailable — GCS bucket unreachable.
          Check <code className="font-mono text-xs">BUILD_STATE_GCS_BASE</code> env var.
        </div>
      )}
    </main>
  )
}
