'use client'

import * as React from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { fetchEvalRuns } from '@/lib/performance/api_client'

function pct(v: number | null | undefined) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(1)}%`
}

export function EvalRunsClient() {
  const [page, setPage] = React.useState(1)
  const { data, isFetching } = useQuery({
    queryKey: ['perf-eval-runs', page],
    queryFn: () => fetchEvalRuns(page, 20),
    refetchOnWindowFocus: true,
  })

  const rows = data?.rows ?? []
  const total = data?.total ?? 0
  const maxPage = Math.max(1, Math.ceil(total / 20))

  return (
    <div className="space-y-4 p-4">
      <header className="flex items-baseline justify-between border-b pb-2">
        <h1 className="text-xl font-semibold tracking-tight">Eval runs</h1>
        <span className="text-xs text-muted-foreground">
          <Link href="/performance" className="underline">
            ← back to performance
          </Link>
          {isFetching && ' · updating…'}
        </span>
      </header>
      <div className="rounded-lg border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="border-b bg-muted/40">
              <tr className="text-left">
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Golden set</th>
                <th className="px-3 py-2">Planner prompt</th>
                <th className="px-3 py-2">Query count</th>
                <th className="px-3 py-2">Recall</th>
                <th className="px-3 py-2">Precision</th>
                <th className="px-3 py-2">Cite rate</th>
                <th className="px-3 py-2">Synth pass</th>
                <th className="px-3 py-2">Hit rate</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-3 py-6 text-center text-muted-foreground">
                    No eval runs recorded yet.
                  </td>
                </tr>
              )}
              {rows.map((r) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-muted/40">
                  <td className="px-3 py-1.5 font-mono text-[10px]">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-1.5">{r.golden_set_version}</td>
                  <td className="px-3 py-1.5">{r.planner_prompt_version ?? '—'}</td>
                  <td className="px-3 py-1.5">{r.query_count ?? '—'}</td>
                  <td className="px-3 py-1.5">{pct(r.plan_accuracy_recall)}</td>
                  <td className="px-3 py-1.5">{pct(r.plan_accuracy_precision)}</td>
                  <td className="px-3 py-1.5">{pct(r.citation_rate)}</td>
                  <td className="px-3 py-1.5">{pct(r.synthesis_pass_rate)}</td>
                  <td className="px-3 py-1.5">{pct(r.retrieval_hit_rate)}</td>
                  <td className="px-3 py-1.5">
                    <Link
                      href={`/performance/eval-runs/${r.id}`}
                      className="text-foreground underline"
                    >
                      View detail →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
          <span>
            Page {page} of {maxPage} · {total} total
          </span>
          <span className="flex gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="rounded border px-2 py-0.5 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              disabled={page >= maxPage}
              onClick={() => setPage(page + 1)}
              className="rounded border px-2 py-0.5 disabled:opacity-40"
            >
              Next
            </button>
          </span>
        </div>
      </div>
    </div>
  )
}
