/**
 * Stream C / Unit 2d — Cockpit > Command Center.
 *
 * Super-admin-only landing page that:
 *   - lists every gate in the registry grouped by class
 *   - shows current effective value + override status
 *   - renders an ayanamsha-registry block (read-only display)
 *   - exposes a chart-id dropdown for per_chart-scoped gates (MVP stub)
 *
 * Editing routes through `POST /cockpit/command-center/api/edit`.
 */

import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { readAllGatesGlobal } from '@/lib/config/configService'
import { AYANAMSHA_REGISTRY, type GateClass } from '@/lib/gates/gate_registry'

export const dynamic = 'force-dynamic'

const CLASS_LABELS: Record<GateClass, string> = {
  feature_flag: 'Feature flags',
  pipeline_threshold: 'Pipeline thresholds',
  model_routing: 'Model routing',
  access_capability: 'Access capability',
  data_source: 'Data sources',
}

// MVP chart-id dropdown source. Real chart list lands when 2c's chart-table
// wiring closes; for now the dropdown is a server-rendered stub.
const STUB_CHART_IDS = ['native_abhisek', 'guest']

export default async function CommandCenterPage({
  searchParams,
}: {
  searchParams?: Promise<{ chart?: string }>
}) {
  // Auth gate — page-level requireSuperAdmin equivalent.
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.status !== 'active') redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')

  const params = (await searchParams) ?? {}
  const selectedChart = params.chart ?? STUB_CHART_IDS[0]

  const gates = await readAllGatesGlobal()
  const grouped = new Map<GateClass, typeof gates>()
  for (const g of gates) {
    if (!grouped.has(g.spec.class)) grouped.set(g.spec.class, [])
    grouped.get(g.spec.class)!.push(g)
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-6" data-testid="command-center-page">
      <header className="mb-6 flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="bt-display">Command Center</h1>
        <form method="get" className="flex items-center gap-2">
          <label htmlFor="chart-select" className="bt-body text-muted-foreground">
            Chart
          </label>
          <select
            id="chart-select"
            name="chart"
            defaultValue={selectedChart}
            data-testid="chart-select"
            className="rounded border border-border bg-background px-2 py-1 text-sm"
          >
            {STUB_CHART_IDS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <button type="submit" className="text-sm underline">
            Apply
          </button>
        </form>
      </header>

      {(Object.keys(CLASS_LABELS) as GateClass[]).map((cls) => {
        const items = grouped.get(cls) ?? []
        if (items.length === 0) return null
        return (
          <section key={cls} className="mb-8" data-testid={`gate-class-${cls}`}>
            <h2 className="bt-heading mb-3">{CLASS_LABELS[cls]}</h2>
            <ul className="space-y-2">
              {items.map(({ spec, value, overridden }) => (
                <li
                  key={spec.key}
                  className="flex items-start justify-between gap-4 rounded border border-border p-3"
                  data-testid={`gate-row-${spec.key}`}
                  data-gate-key={spec.key}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-mono">{spec.key}</code>
                      {spec.danger && (
                        <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700 dark:bg-red-900/40 dark:text-red-300">
                          danger
                        </span>
                      )}
                      {!spec.hot_reload && (
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                          restart-required
                        </span>
                      )}
                      {overridden && (
                        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                          overridden
                        </span>
                      )}
                    </div>
                    <p className="bt-body text-muted-foreground">{spec.description}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="bt-body">
                      <span className="text-muted-foreground">value:</span>{' '}
                      <code className="font-mono">{JSON.stringify(value)}</code>
                    </div>
                    <div className="bt-body text-xs text-muted-foreground">
                      type: {spec.value_type} · scope: {spec.scope}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )
      })}

      <section className="mb-8" data-testid="ayanamsha-registry-block">
        <h2 className="bt-heading mb-3">Ayanamsha registry</h2>
        <p className="bt-body text-muted-foreground mb-2">
          Read-only display of the three ayanamsha roles. The canonical role
          cannot be disabled (guard enforced at write time).
        </p>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              <th className="py-1 pr-2">role</th>
              <th className="py-1 pr-2">source</th>
              <th className="py-1 pr-2">gate</th>
            </tr>
          </thead>
          <tbody>
            {AYANAMSHA_REGISTRY.map((row) => (
              <tr key={row.role} data-testid={`ayanamsha-row-${row.role}`}>
                <td className="py-1 pr-2 font-mono">{row.role}</td>
                <td className="py-1 pr-2">{row.source}</td>
                <td className="py-1 pr-2 font-mono">{row.gate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  )
}
