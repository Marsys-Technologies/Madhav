'use client'

import * as React from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { fetchEvalRunDetail, fetchQueryLog, type QueryLogRow } from '@/lib/performance/api_client'
import { QueryLogTable } from './QueryLogTable'
import { TracePanelLauncher } from './TracePanelLauncher'

function pct(v: number | null | undefined) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(1)}%`
}

export function EvalRunDetailClient({ id }: { id: string }) {
  const detailQ = useQuery({
    queryKey: ['perf-eval-run', id],
    queryFn: () => fetchEvalRunDetail(id),
  })
  const [page, setPage] = React.useState(1)
  const queriesQ = useQuery({
    queryKey: ['perf-eval-run-queries', id, page],
    queryFn: () =>
      fetchQueryLog({
        window_start: '2020-01-01T00:00:00.000Z',
        window_end: new Date().toISOString(),
        source: 'eval',
        eval_run_id: id,
        page,
        page_size: 50,
      }),
  })
  const [traceQueryId, setTraceQueryId] = React.useState<string | null>(null)
  const [traceOpen, setTraceOpen] = React.useState(false)

  const run = detailQ.data?.run

  return (
    <div className="space-y-4 p-4">
      <header className="flex items-baseline justify-between border-b pb-2">
        <h1 className="text-xl font-semibold tracking-tight">
          Eval run · {run?.golden_set_version ?? id.slice(0, 8)}
        </h1>
        <Link href="/performance/eval-runs" className="text-xs underline">
          ← back to eval runs
        </Link>
      </header>
      <section className="grid grid-cols-2 gap-3 rounded-lg border bg-card p-4 text-xs sm:grid-cols-4">
        <Stat label="created" value={run ? new Date(run.created_at).toLocaleString() : '—'} />
        <Stat label="finished" value={run?.finished_at ? new Date(run.finished_at).toLocaleString() : '—'} />
        <Stat label="triggered_by" value={run?.triggered_by ?? '—'} />
        <Stat label="query_count" value={run?.query_count?.toString() ?? '—'} />
        <Stat label="recall" value={pct(run?.plan_accuracy_recall)} />
        <Stat label="precision" value={pct(run?.plan_accuracy_precision)} />
        <Stat label="citation_rate" value={pct(run?.citation_rate)} />
        <Stat label="synthesis_pass" value={pct(run?.synthesis_pass_rate)} />
        <Stat label="retrieval_hit" value={pct(run?.retrieval_hit_rate)} />
        <Stat label="B.10 compliance" value={pct(run?.b10_compliance_rate)} />
        <Stat label="B.11 compliance" value={pct(run?.b11_compliance_rate)} />
        <Stat
          label="avg latency"
          value={run?.avg_latency_total_ms == null ? '—' : `${run.avg_latency_total_ms} ms`}
        />
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold">Constituent queries</h2>
        <QueryLogTable
          rows={queriesQ.data?.rows ?? []}
          total={queriesQ.data?.total ?? 0}
          page={page}
          pageSize={50}
          onPageChange={setPage}
          onRowClick={(row: QueryLogRow) => {
            setTraceQueryId(row.audit_event_id ?? row.id)
            setTraceOpen(true)
          }}
        />
      </section>

      <TracePanelLauncher open={traceOpen} queryId={traceQueryId} onOpenChange={setTraceOpen} />
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="font-mono text-sm">{value}</div>
    </div>
  )
}
