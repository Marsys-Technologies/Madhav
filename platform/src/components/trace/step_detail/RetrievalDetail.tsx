'use client'

/**
 * RetrievalDetail — Gate II W4 (2026-05-12).
 *
 * Replaces FetchSqlDetail / FetchGcsDetail / FetchVectorDetail with a single
 * generalized variant that renders all sub-tools that fired under the
 * Retrieval group per D5. Per-sub-tool metadata blocks: rows-fetched,
 * latency, top-score (vector), token estimate.
 */

import type { RetrievalSubToolRun } from '@/lib/trace/types'
import { Section } from './Section'

interface Props {
  retrieval: RetrievalSubToolRun[]
  /** Optional: focus on a single sub-tool (when the user clicked a specific row). */
  focusedTool?: string | null
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function fmtCount(n: number | null | undefined): string {
  if (n == null) return '—'
  return n.toLocaleString()
}

function StatusPill({ status }: { status: RetrievalSubToolRun['status'] }) {
  const map: Record<RetrievalSubToolRun['status'], string> = {
    done: 'bg-emerald-400/10 text-emerald-400',
    running: 'bg-zinc-700/30 text-zinc-300',
    pending: 'bg-zinc-700/20 text-zinc-500',
    error: 'bg-amber-400/10 text-amber-400',
    cancelled: 'bg-zinc-700/20 text-zinc-600',
  }
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide ${map[status]}`}>
      {status}
    </span>
  )
}

function ToolRow({ run }: { run: RetrievalSubToolRun }) {
  const ds = run.data_summary as {
    rows_returned?: number
    chunks_returned?: number
    token_estimate?: number
    top_score?: number
    tool_name?: string
  }
  const rows = ds?.rows_returned ?? ds?.chunks_returned ?? null

  return (
    <div
      className="rounded border border-[rgba(212,175,55,0.10)] bg-[oklch(0.10_0.005_70)] p-3"
      data-testid={`retrieval-detail-${run.tool_name}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[11px] font-mono text-foreground">{run.tool_name}</span>
        <span className="text-[10px] text-muted-foreground">[{run.step_type}]</span>
        <StatusPill status={run.status} />
        <span className="ml-auto text-[10px] text-muted-foreground">
          {fmtMs(run.latency_ms)}
        </span>
      </div>
      <dl className="grid grid-cols-3 gap-2 text-[11px]">
        <div>
          <dt className="text-muted-foreground">rows</dt>
          <dd className="font-mono text-foreground">{fmtCount(rows)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">tokens (est)</dt>
          <dd className="font-mono text-foreground">{fmtCount(ds?.token_estimate ?? null)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">top score</dt>
          <dd className="font-mono text-foreground">
            {typeof ds?.top_score === 'number' ? ds.top_score.toFixed(3) : '—'}
          </dd>
        </div>
      </dl>
    </div>
  )
}

export function RetrievalDetail({ retrieval, focusedTool = null }: Props) {
  const visible = focusedTool
    ? retrieval.filter(r => r.tool_name === focusedTool)
    : retrieval

  if (visible.length === 0) {
    return (
      <div data-testid="retrieval-detail">
        <p className="text-xs text-zinc-500">No retrieval data for this query.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="retrieval-detail">
      <Section title={focusedTool ? `Sub-tool · ${focusedTool}` : `Retrieval (${visible.length} tools)`}>
        <div className="space-y-2">
          {visible.map(r => (
            <ToolRow key={r.step_seq + ':' + r.tool_name} run={r} />
          ))}
        </div>
      </Section>
    </div>
  )
}
