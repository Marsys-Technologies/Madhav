'use client'

import * as React from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter, useSearchParams } from 'next/navigation'

import {
  fetchKpis,
  fetchQueryLog,
  type QueryLogRow,
} from '@/lib/performance/api_client'
import type { Source } from '@/lib/performance/kpi_aggregator'
import { TimeWindowPicker, resolveWindow, type WindowPreset } from './TimeWindowPicker'
import { KpiTile } from './KpiTile'
import { QueryLogTable } from './QueryLogTable'
import { JudgeRunModal } from './JudgeRunModal'
import { TracePanelLauncher } from './TracePanelLauncher'
import { AssetCatalogSection } from './AssetCatalogSection'
import { RetrievalUtilizationSection } from './RetrievalUtilizationSection'
import { PlannerRoutingSection } from './PlannerRoutingSection'
import { FreshnessSection } from './FreshnessSection'
import { DiagnosticsSection } from './DiagnosticsSection'
import { ManifestDriftSection } from './ManifestDriftSection'
import { ConflictPanel } from './ConflictPanel'

function pct(v: number | null | undefined, digits = 1): string {
  if (v == null) return '—'
  return `${(v * 100).toFixed(digits)}%`
}

function num(v: number | null | undefined): string {
  if (v == null) return '—'
  return v.toLocaleString()
}

export function PerformanceClient() {
  const router = useRouter()
  const params = useSearchParams()
  const qc = useQueryClient()

  const initialPreset = (params.get('window') as WindowPreset) ?? '7d'
  const initialSource = (params.get('source') as Source) ?? 'all'
  const initialCustomStart = params.get('start') ?? undefined
  const initialCustomEnd = params.get('end') ?? undefined

  const [preset, setPreset] = React.useState<WindowPreset>(initialPreset)
  const [customRange, setCustomRange] = React.useState<{ start: string; end: string } | undefined>(
    initialCustomStart && initialCustomEnd ? { start: initialCustomStart, end: initialCustomEnd } : undefined
  )
  const [source, setSource] = React.useState<Source>(initialSource)
  const [page, setPage] = React.useState(1)
  const [judgeOpen, setJudgeOpen] = React.useState(false)
  const [traceQueryId, setTraceQueryId] = React.useState<string | null>(null)
  const [traceOpen, setTraceOpen] = React.useState(false)
  const [proposedCount, setProposedCount] = React.useState(0)

  // ICR-S5: fetch proposed conflict patch count for ConflictPanel
  React.useEffect(() => {
    fetch('/api/icr/patches')
      .then((r) => r.json())
      .then((data: { proposed?: string[] }) => {
        setProposedCount(data.proposed?.length ?? 0)
      })
      .catch(() => {
        // Non-fatal — panel renders with 0 if fetch fails
      })
  }, [])

  // PERF-S1 fix (f): track when data was last successfully fetched.
  const lastFetchedAtRef = React.useRef<number | null>(null)
  const [fetchedAgoLabel, setFetchedAgoLabel] = React.useState<string>('never')

  const window = React.useMemo(() => resolveWindow(preset, customRange), [preset, customRange])

  React.useEffect(() => {
    const sp = new URLSearchParams()
    sp.set('window', preset)
    sp.set('source', source)
    if (preset === 'custom' && customRange) {
      sp.set('start', customRange.start)
      sp.set('end', customRange.end)
    }
    router.replace(`?${sp.toString()}`)
  }, [preset, source, customRange, router])

  const kpisQ = useQuery({
    queryKey: ['perf-kpis', window.start, window.end, source],
    queryFn: () => fetchKpis({ window_start: window.start, window_end: window.end, source }),
    refetchInterval: 45_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  })

  // PERF-S1 fix (f): update lastFetchedAtRef when kpisQ data arrives.
  React.useEffect(() => {
    if (kpisQ.data != null) {
      lastFetchedAtRef.current = Date.now()
    }
  }, [kpisQ.data])

  // Tick every 10s to update the "Updated Xs ago" label.
  React.useEffect(() => {
    function computeLabel(): string {
      const ts = lastFetchedAtRef.current
      if (ts == null) return 'never'
      const diffS = Math.floor((Date.now() - ts) / 1000)
      if (diffS < 5) return 'just now'
      if (diffS < 60) return `${diffS}s ago`
      return `${Math.floor(diffS / 60)}m ago`
    }
    setFetchedAgoLabel(computeLabel())
    const id = setInterval(() => setFetchedAgoLabel(computeLabel()), 10_000)
    return () => clearInterval(id)
  }, [kpisQ.data])

  const queriesQ = useQuery({
    queryKey: ['perf-queries', window.start, window.end, source, page],
    queryFn: () =>
      fetchQueryLog({
        window_start: window.start,
        window_end: window.end,
        source,
        page,
        page_size: 50,
      }),
    refetchInterval: 45_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  })

  const onRefresh = () => {
    void qc.invalidateQueries({ queryKey: ['perf-kpis'] })
    void qc.invalidateQueries({ queryKey: ['perf-queries'] })
  }

  const k = kpisQ.data?.bundles
  const sparks = kpisQ.data?.sparklines
  const unjudgedN = k?.pipeline_correctness.plan_accuracy_consume_unjudged_n ?? 0

  return (
    <div className="aiops-shell min-h-full space-y-6 p-6">
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b pb-4" style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.15)' }}>
        <div>
          <h1 className="bt-display" style={{ color: 'var(--brand-gold-cream)' }}>Performance Command Center</h1>
          <p className="bt-label mt-1">
            Super-admin · Gate I ·{' '}
            {kpisQ.isFetching
              ? 'updating…'
              : (
                <span style={{ color: 'var(--status-success)' }}>
                  Updated {fetchedAgoLabel}
                </span>
              )}
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="rounded border px-3 py-1.5 text-xs font-medium transition-colors"
          style={{ borderColor: 'rgba(212,175,55,0.35)', color: 'var(--brand-gold)' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(212,175,55,0.08)')}
          onMouseLeave={e => (e.currentTarget.style.background = '')}
        >
          Refresh now
        </button>
      </header>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <TimeWindowPicker
          value={preset}
          customRange={customRange}
          onChange={(p, c) => {
            setPreset(p)
            setCustomRange(c)
            setPage(1)
          }}
        />
        <div className="flex items-center gap-1">
          <span className="bt-label mr-1">Source:</span>
          {(['all', 'consume', 'eval'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSource(s)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                source === s
                  ? 'border-[rgba(212,175,55,0.35)] bg-[rgba(212,175,55,0.12)] text-[var(--brand-gold)]'
                  : 'border-transparent text-muted-foreground hover:bg-[rgba(212,175,55,0.06)] hover:text-[var(--brand-gold)]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <KpiTile
          bundle="pipeline_correctness"
          title="Pipeline correctness"
          description="Plan accuracy (recall/precision) + citation rate."
          headline={{ label: 'plan accuracy (recall)', value: pct(k?.pipeline_correctness.plan_accuracy_recall) }}
          secondary={[
            { label: 'precision', value: pct(k?.pipeline_correctness.plan_accuracy_precision) },
            { label: 'cite rate', value: pct(k?.pipeline_correctness.citation_rate) },
            { label: 'n', value: num(k?.pipeline_correctness.plan_accuracy_n) },
            { label: 'unjudged', value: num(unjudgedN) },
          ]}
          delta={null}
          sparkline={sparks?.pipeline_correctness ?? []}
          extra={
            unjudgedN > 0 ? (
              <button
                onClick={() => setJudgeOpen(true)}
                className="rounded border px-2 py-1 text-xs transition-colors"
                style={{ borderColor: 'rgba(212,175,55,0.30)', color: 'var(--brand-gold)' }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(212,175,55,0.08)')}
                onMouseLeave={e => (e.currentTarget.style.background = '')}
              >
                Run judge on {unjudgedN} unjudged →
              </button>
            ) : null
          }
        />
        <KpiTile
          bundle="answer_quality"
          title="Answer quality"
          description="Calibration (Brier, lower=better) + B.10/B.11 compliance."
          headline={{ label: 'B.10 compliance', value: pct(k?.answer_quality.b10_compliance_rate) }}
          secondary={[
            { label: 'B.11 compliance', value: pct(k?.answer_quality.b11_compliance_rate) },
            {
              label: 'Brier',
              value: k?.answer_quality.calibration_brier == null
                ? '—'
                : k.answer_quality.calibration_brier.toFixed(3),
            },
            { label: 'cal n', value: num(k?.answer_quality.calibration_n) },
          ]}
          delta={null}
          sparkline={sparks?.answer_quality ?? []}
        />
        <KpiTile
          bundle="performance_health"
          title="Performance health"
          description="Latency p50/p95 by class + synthesis pass rate."
          headline={{ label: 'p95 latency', value: k?.performance_health.latency_p95_ms == null ? '—' : `${num(k.performance_health.latency_p95_ms)} ms` }}
          secondary={[
            {
              label: 'p50',
              value:
                k?.performance_health.latency_p50_ms == null
                  ? '—'
                  : `${num(k.performance_health.latency_p50_ms)} ms`,
            },
            { label: 'synth pass', value: pct(k?.performance_health.synthesis_pass_rate) },
            { label: 'n', value: num(k?.performance_health.synthesis_n) },
          ]}
          delta={null}
          sparkline={sparks?.performance_health ?? []}
        />
        <KpiTile
          bundle="retrieval_health"
          title="Retrieval health"
          description="Fraction of queries with at least one retrieval hit."
          headline={{ label: 'hit rate', value: pct(k?.retrieval_health.retrieval_hit_rate) }}
          secondary={[{ label: 'n', value: num(k?.retrieval_health.retrieval_n) }]}
          delta={null}
          sparkline={sparks?.retrieval_health ?? []}
        />
      </section>

      <AssetCatalogSection />

      {/* PERF-S3: Retrieval Utilization — real data wiring is PERF-S4 */}
      <RetrievalUtilizationSection
        tools={[]}
        callData={{}}
      />

      {/* PERF-S3: Planner Routing — real data wiring is PERF-S4 */}
      <PlannerRoutingSection
        routingData={{}}
        coverageStats={{ totalAssets: 0, assetsWithTool: 0, toolsWithManifest: 0, plannerVisibleTools: 0 }}
      />

      {/* PERF-S4: Freshness panel — real data wiring via computeFreshnessFromManifest() server-side */}
      <FreshnessSection assets={[]} />

      {/* PERF-S4: Diagnostics panel — real data wiring is PERF-S5 */}
      <DiagnosticsSection toolDiagnostics={[]} recentFailures={[]} />

      {/* PERF-S4: Manifest Drift — real data wiring is PERF-S5 */}
      <ManifestDriftSection driftReport={null} />

      {/* ICR-S5: Conflict Resolution stub — full panel ships in PERF-S5 */}
      <ConflictPanel proposedCount={proposedCount} />

      <section className="space-y-3">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>Query log</h2>
        <QueryLogTable
          rows={queriesQ.data?.rows ?? []}
          total={queriesQ.data?.total ?? 0}
          page={page}
          pageSize={50}
          onPageChange={setPage}
          onRowClick={(row: QueryLogRow) => {
            const qid = row.audit_event_id ?? row.id
            setTraceQueryId(qid)
            setTraceOpen(true)
          }}
        />
      </section>

      <JudgeRunModal
        open={judgeOpen}
        onOpenChange={setJudgeOpen}
        window={{ start: window.start, end: window.end }}
        onCompleted={onRefresh}
      />
      <TracePanelLauncher open={traceOpen} queryId={traceQueryId} onOpenChange={setTraceOpen} />
    </div>
  )
}
