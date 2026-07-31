'use client'

import { useState, useEffect, useMemo } from 'react'
import type { AssetRow } from '@/app/api/cockpit/registry/route'

export type AtlasAsset = AssetRow & { clear_tables: string[] | null }

type AssetStat = {
  asset_id: string
  actual_rows: number | null
  error: string | null
  // Mirrors AssetState in src/app/api/cockpit/stats/deriveState.ts — keep in step.
  // 'incomplete': migration 474 / SAMĀPTI B-COCKPIT-INCOMPLETE (DVA Ruling 24).
  state: 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'partial' | 'incomplete' | 'not_migrated' | 'service_ok'
  last_built_at: string | null
  // Badge-honesty (pre-D-4b readiness pass): real progress from the substep-resumption
  // ledger, populated when state === 'partial' or 'incomplete'. `total` is honestly null
  // unless the asset declares a computable expected count — never fabricated.
  substep_progress?: { committed: number; total: number | null }
}

type SampleData = {
  columns: string[]
  rows: Record<string, unknown>[]
  table: string | null
  note?: string
  fetched_at: string
  error?: string
}

const LAYER_ORDER = ['brahmagyan', 'ganita', 'bodha', 'kala', 'phala', 'mimamsa']

// Extract all physical tables for display: clear_tables > target_table > count_sql parse
function getDisplayTables(asset: AtlasAsset): string[] {
  if (asset.clear_tables && asset.clear_tables.length > 0) return asset.clear_tables
  if (asset.target_table) return [asset.target_table]
  if (asset.count_sql) {
    const m = asset.count_sql.match(/FROM\s+(\w+)/i)
    if (m?.[1]) return [`${m[1]} (partitioned)`]
  }
  return []
}

function stateBadgeClass(state: AssetStat['state'] | undefined, loading: boolean): string {
  if (loading || !state) return 'bg-muted text-muted-foreground'
  switch (state) {
    case 'lit':
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'
    case 'service_ok':
      return 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200'
    case 'building':
    case 'stale':
    case 'dormant':
      return 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200'
    case 'error':
      return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200'
    // Distinct from 'error': a resumable, in-progress materialization (real committed
    // substeps exist), not a broken writer. Amber-adjacent (blue) so it never reads as
    // either "done" (lit) or "broken" (error) at a glance.
    case 'partial':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200'
    // 'incomplete' (migration 474): the writer ran and committed real substeps, but its
    // own plan says work remains. Shares the 'partial' treatment because it is the same
    // operator situation — resumable, not broken, and emphatically NOT done. The one
    // thing it must never be is emerald.
    case 'incomplete':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200'
    case 'not_migrated':
      return 'bg-muted text-muted-foreground'
  }
}

function stateBadgeLabel(
  state: AssetStat['state'] | undefined,
  loading: boolean,
  actualRows: number | null,
  substepProgress?: { committed: number; total: number | null }
): string {
  if (loading) return '…'
  if (!state) return '—'
  switch (state) {
    case 'lit':
      return actualRows !== null ? `${actualRows.toLocaleString()} rows` : 'lit'
    case 'dormant':
      return '0 rows'
    case 'building':
      return actualRows !== null ? `${actualRows.toLocaleString()} rows (building)` : 'building'
    case 'stale':
      return 'stale'
    case 'error':
      return 'error'
    case 'partial':
      if (!substepProgress) return 'in progress'
      return substepProgress.total != null
        ? `${substepProgress.committed}/${substepProgress.total} — in progress, resumable`
        : `${substepProgress.committed} substeps committed — in progress, resumable`
    // Never renders a row count: a row count next to an unfinished asset is exactly the
    // "looks done" signal this state exists to deny. The rebuild prompt is the point.
    case 'incomplete':
      return substepProgress
        ? `${substepProgress.committed} substeps committed — incomplete, rebuild to finish`
        : 'incomplete — rebuild to finish'
    case 'not_migrated':
      return 'not built'
    case 'service_ok':
      return 'service ✓'
  }
}

function reconciliationDot(state: AssetStat['state'] | undefined, loading: boolean): string {
  if (loading || !state) return 'bg-muted-foreground/30'
  switch (state) {
    case 'lit':
    case 'service_ok':
    case 'building':
      return 'bg-emerald-500'
    case 'dormant':
    case 'stale':
      return 'bg-amber-500'
    case 'error':
      return 'bg-red-500'
    case 'partial':
    case 'incomplete':
      return 'bg-blue-500'
    case 'not_migrated':
      return 'bg-muted-foreground/30'
  }
}

// ─── Per-asset collapsible card ────────────────────────────────────────────

function AssetCard({
  asset,
  stat,
  statsLoading,
  chartId,
}: {
  asset: AtlasAsset
  stat: AssetStat | undefined
  statsLoading: boolean
  chartId: string
}) {
  const [open, setOpen] = useState(false)
  const [sample, setSample] = useState<SampleData | null>(null)
  const [sampleLoading, setSampleLoading] = useState(false)

  const tables = getDisplayTables(asset)
  const canShowSample = asset.asset_type !== 'service' && asset.storage_type !== 'postgres_view'

  async function loadSample() {
    setSampleLoading(true)
    try {
      const url =
        `/api/cockpit/atlas/sample?asset=${encodeURIComponent(asset.asset_id)}` +
        (chartId ? `&chart_id=${encodeURIComponent(chartId)}` : '') +
        `&limit=10`
      const r = await fetch(url)
      const d = await r.json()
      if (d.errors?.length) {
        setSample({ columns: [], rows: [], table: null, fetched_at: new Date().toISOString(), error: d.errors[0] })
      } else {
        setSample(d.data)
      }
    } catch (e) {
      setSample({
        columns: [],
        rows: [],
        table: null,
        fetched_at: new Date().toISOString(),
        error: (e as Error).message,
      })
    } finally {
      setSampleLoading(false)
    }
  }

  return (
    <article className="border-b border-border last:border-b-0">
      {/* Always-visible header row */}
      <button
        className="w-full p-4 flex items-start justify-between gap-3 text-left hover:bg-muted/30 transition-colors"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="bt-mono text-xs text-muted-foreground shrink-0">{asset.asset_id}</span>
            <span className="bt-body font-medium">{asset.english_name}</span>
            <span className="bt-label text-muted-foreground">/{asset.sanskrit_name}</span>
          </div>
          <p className="bt-body text-muted-foreground mt-0.5 text-sm line-clamp-1">
            {asset.english_description}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`bt-label inline-flex items-center rounded px-2 py-0.5 text-xs ${stateBadgeClass(stat?.state, statsLoading)}`}
          >
            {stateBadgeLabel(stat?.state, statsLoading, stat?.actual_rows ?? null, stat?.substep_progress)}
          </span>
          <span className="text-muted-foreground text-xs">{open ? '▴' : '▾'}</span>
        </div>
      </button>

      {/* Expanded detail */}
      {open && (
        <div className="border-t border-border/50 px-4 pb-5 pt-3 space-y-4">
          {/* Identity grid */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
            {[
              ['asset_id', asset.asset_id],
              ['layer', `${asset.layer_index ?? ''} ${asset.layer_name ?? asset.layer}`.trim()],
              ['scope', asset.scope],
              ['storage', asset.storage_type],
              ['status', asset.catalog_status ?? '—'],
              ['is_active', asset.is_active ? 'yes' : 'no'],
              ...(asset.asset_type === 'service' ? [['asset_type', 'service'] as [string, string]] : []),
            ].map(([label, value]) => (
              <div key={label}>
                <p className="bt-label text-muted-foreground">{label}</p>
                <p className="bt-mono mt-0.5 break-all">{value}</p>
              </div>
            ))}
          </div>

          {/* Tables */}
          {tables.length > 0 && (
            <div>
              <p className="bt-label text-muted-foreground mb-1">
                Tables ({tables.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {tables.map((t) => (
                  <span
                    key={t}
                    className="bt-mono text-xs rounded border border-border bg-muted px-2 py-0.5"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Live count + reconciliation */}
          <div className="flex flex-wrap items-start gap-6">
            <div>
              <p className="bt-label text-muted-foreground mb-1">Live count</p>
              {statsLoading ? (
                <span className="bt-body text-muted-foreground text-sm">Loading…</span>
              ) : stat ? (
                <div className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full shrink-0 ${reconciliationDot(stat.state, false)}`}
                  />
                  <span className="bt-body font-medium">
                    {stat.actual_rows !== null ? stat.actual_rows.toLocaleString() : '—'}
                  </span>
                  {stat.error && (
                    <span className="bt-label text-red-600 dark:text-red-400">{stat.error}</span>
                  )}
                  {stat.last_built_at && (
                    <span className="bt-label text-muted-foreground">
                      built {new Date(stat.last_built_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              ) : (
                <span className="bt-body text-muted-foreground text-sm">—</span>
              )}
            </div>
            {asset.target_floor != null && (
              <div>
                <p className="bt-label text-muted-foreground mb-1">Target floor</p>
                <span className="bt-body">{asset.target_floor.toLocaleString()}</span>
              </div>
            )}
          </div>

          {/* Dependencies */}
          {asset.depends_on && asset.depends_on.length > 0 && (
            <div>
              <p className="bt-label text-muted-foreground mb-1">
                Depends on ({asset.depends_on.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {asset.depends_on.map((d) => (
                  <span
                    key={d}
                    className="bt-mono text-xs rounded border border-border bg-muted px-2 py-0.5"
                  >
                    {d}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Astrological content note */}
          <div>
            <p className="bt-label text-muted-foreground mb-1">Astrological content</p>
            <p className="bt-body text-sm">{asset.english_description}</p>
          </div>

          {/* Sample data */}
          {canShowSample && (
            <div>
              <div className="flex items-center gap-3 mb-2">
                <p className="bt-label text-muted-foreground">Sample data</p>
                <button
                  onClick={loadSample}
                  disabled={sampleLoading}
                  className="bt-label rounded border border-border bg-card px-2 py-0.5 hover:bg-muted transition-colors disabled:opacity-50 text-xs"
                >
                  {sampleLoading ? 'Loading…' : sample ? 'Refresh rows' : 'Show 10 rows'}
                </button>
                {sample && !sample.error && (
                  <span className="bt-label text-muted-foreground">
                    as of {new Date(sample.fetched_at).toLocaleTimeString()}
                  </span>
                )}
              </div>

              {sample?.note && !sample.error && (
                <p className="bt-body text-muted-foreground text-sm">{sample.note}</p>
              )}
              {sample?.error && (
                <p className="bt-body text-red-600 dark:text-red-400 text-sm">{sample.error}</p>
              )}
              {sample && !sample.error && !sample.note && sample.rows.length === 0 && (
                <p className="bt-body text-muted-foreground text-sm">
                  No rows for this chart (or asset not yet built).
                </p>
              )}
              {sample && !sample.error && sample.rows.length > 0 && (
                <div className="overflow-x-auto rounded border border-border">
                  <table className="w-full text-xs">
                    <thead className="bg-muted/50">
                      <tr>
                        {sample.columns.map((col) => (
                          <th
                            key={col}
                            className="px-2 py-1.5 text-left bt-mono font-medium whitespace-nowrap border-r border-border last:border-r-0"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {sample.rows.map((row, i) => (
                        <tr key={i} className="hover:bg-muted/30">
                          {sample.columns.map((col) => {
                            const raw = row[col]
                            const display =
                              raw === null ? null : typeof raw === 'object' ? JSON.stringify(raw) : String(raw)
                            return (
                              <td
                                key={col}
                                className="px-2 py-1 bt-mono text-xs max-w-[220px] truncate border-r border-border/50 last:border-r-0"
                                title={display ?? ''}
                              >
                                {raw === null ? (
                                  <span className="text-muted-foreground/40">null</span>
                                ) : (
                                  display
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          {!canShowSample && (
            <p className="bt-label text-muted-foreground">
              {asset.asset_type === 'service' ? 'Service asset — no table rows.' : 'View asset — no stored rows.'}
            </p>
          )}
        </div>
      )}
    </article>
  )
}

// ─── Main Atlas view ────────────────────────────────────────────────────────

type ClientOption = { chart_id: string; display_name: string }

export function AtlasView({
  assets,
  defaultChartId,
}: {
  assets: AtlasAsset[]
  defaultChartId: string
}) {
  const [chartId, setChartId] = useState(defaultChartId)
  const [clients, setClients] = useState<ClientOption[]>([])
  const [clientsLoading, setClientsLoading] = useState(true)
  const [stats, setStats] = useState<Map<string, AssetStat>>(new Map())
  const [statsLoading, setStatsLoading] = useState(true)
  const [statsFetchedAt, setStatsFetchedAt] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/clients')
      .then((r) => r.json())
      .then((rows: Record<string, unknown>[]) => {
        if (!Array.isArray(rows)) return
        const nameCounts = new Map<string, number>()
        for (const r of rows) {
          const base = String(r.subject_name || r.name || 'Unknown')
          nameCounts.set(base, (nameCounts.get(base) ?? 0) + 1)
        }
        setClients(
          rows
            .filter((r) => typeof r.chart_id === 'string' && r.chart_id)
            .map((r) => {
              const base = String(r.subject_name || r.name || 'Unknown')
              const display =
                (nameCounts.get(base) ?? 1) > 1
                  ? `${base} (${String(r.birth_date ?? (r.chart_id as string).slice(0, 8))})`
                  : base
              return { chart_id: r.chart_id as string, display_name: display }
            })
        )
      })
      .catch(() => {})
      .finally(() => setClientsLoading(false))
  }, [])

  useEffect(() => {
    setStatsLoading(true)
    fetch(`/api/cockpit/stats?chart_id=${encodeURIComponent(chartId)}`)
      .then((r) => r.json())
      .then((d) => {
        const map = new Map<string, AssetStat>()
        for (const s of d.data?.assets ?? []) map.set(s.asset_id, s)
        setStats(map)
        setStatsFetchedAt(d.fetched_at ?? null)
        setStatsLoading(false)
      })
      .catch(() => setStatsLoading(false))
  }, [chartId])

  const grouped = useMemo(() => {
    const map = new Map<string, AtlasAsset[]>()
    for (const a of assets) {
      if (!map.has(a.layer)) map.set(a.layer, [])
      map.get(a.layer)!.push(a)
    }
    return LAYER_ORDER.map((layer) => ({ layer, assets: map.get(layer) ?? [] })).filter(
      (g) => g.assets.length > 0
    )
  }, [assets])

  const summary = useMemo(() => {
    let lit = 0, amber = 0, red = 0, grey = 0
    for (const a of assets) {
      const s = stats.get(a.asset_id)
      if (!s) { grey++; continue }
      // 'incomplete' is counted with the amber (unfinished) group, never with lit —
      // the summary bar is the one number an operator reads at a glance.
      if (s.state === 'lit' || s.state === 'service_ok') lit++
      else if (s.state === 'dormant' || s.state === 'stale' || s.state === 'building' || s.state === 'partial' || s.state === 'incomplete') amber++
      else if (s.state === 'error') red++
      else grey++
    }
    return { lit, amber, red, grey }
  }, [assets, stats])

  return (
    <div>
      {/* Chart selector */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="bt-label text-muted-foreground shrink-0">Chart</label>
        <select
          value={chartId}
          onChange={(e) => setChartId(e.target.value)}
          disabled={clientsLoading}
          className="bt-body text-sm rounded-md border border-border bg-card px-3 py-1.5 outline-none focus:border-foreground disabled:opacity-50 min-w-[200px]"
        >
          {clientsLoading ? (
            <option value={chartId}>Loading…</option>
          ) : clients.length === 0 ? (
            <option value={chartId}>{chartId}</option>
          ) : (
            clients.map((c) => (
              <option key={c.chart_id} value={c.chart_id}>
                {c.display_name}
              </option>
            ))
          )}
        </select>
        {statsLoading && <span className="bt-label text-muted-foreground">fetching counts…</span>}
        {!statsLoading && statsFetchedAt && (
          <span className="bt-label text-muted-foreground">
            as of {new Date(statsFetchedAt).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Summary bar */}
      <div className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-border bg-card px-4 py-2.5">
        <span className="bt-body text-muted-foreground">{assets.length} assets</span>
        <span className="text-border">·</span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="bt-body">{statsLoading ? '…' : summary.lit} lit</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          <span className="bt-body">{statsLoading ? '…' : summary.amber} empty / building</span>
        </span>
        {(statsLoading || summary.red > 0) && (
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500" />
            <span className={`bt-body ${!statsLoading && summary.red > 0 ? 'text-red-700 dark:text-red-400' : ''}`}>
              {statsLoading ? '…' : summary.red} error
            </span>
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />
          <span className="bt-body">{statsLoading ? '…' : summary.grey} not built</span>
        </span>
      </div>

      {/* Layer sections */}
      <div className="space-y-6">
        {grouped.map(({ layer, assets: layerAssets }) => {
          const layerIndex = layerAssets[0]?.layer_index ?? ''
          const layerName = layerAssets[0]?.layer_name ?? layer
          const label = `${layerIndex} · ${layerName}`.replace(/^·\s*/, '')
          const litCount = layerAssets.filter((a) => {
            const s = stats.get(a.asset_id)
            return s?.state === 'lit' || s?.state === 'service_ok'
          }).length

          return (
            <section key={layer}>
              <div className="mb-2 flex items-baseline justify-between">
                <h2 className="bt-heading">{label}</h2>
                <span className="bt-label text-muted-foreground">
                  {statsLoading
                    ? `${layerAssets.length} assets`
                    : `${litCount}/${layerAssets.length} lit`}
                </span>
              </div>
              <div className="rounded-lg border border-border bg-card divide-y divide-border">
                {layerAssets.map((asset) => (
                  // Key includes chartId so asset cards reset sample state on chart switch
                  <AssetCard
                    key={`${asset.asset_id}__${chartId}`}
                    asset={asset}
                    stat={stats.get(asset.asset_id)}
                    statsLoading={statsLoading}
                    chartId={chartId}
                  />
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </div>
  )
}
