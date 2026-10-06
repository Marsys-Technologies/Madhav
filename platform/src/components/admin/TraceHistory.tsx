'use client'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { PageTitle } from '@/components/journey1/Titles'
import type { TraceHistoryRow } from '@/lib/trace/types'
export function TraceHistory() {
  const {userId} = useObservatoryScope()
  const state = useQuery({queryKey:['admin',userId,'trace-history'],queryFn:async () => {
    const response = await fetch('/api/trace/history?limit=50',{cache:'no-store'})
    if (!response.ok) throw Error('Trace history unavailable')
    return await response.json() as TraceHistoryRow[]
  }})
  return <div className="j6-evidence"><PageTitle name="queryTrace" /><p className="j1-note">Portal scope · last 50 recorded queries. Open a query to inspect its recorded steps. Missing traces do not prove that no activity occurred.</p>
    {state.isPending && <p role="status">Loading recorded queries…</p>}
    {state.isError && <div role="alert">Trace history could not be read. <button onClick={() => void state.refetch()}>Try again</button></div>}
    {!state.isError && state.data?.length === 0 && <div className="j5-panel">No recorded traces returned.</div>}
    {!state.isError && state.data?.map(row => <article key={row.query_id} className="j5-panel"><Link href={`/admin/trace/${encodeURIComponent(row.query_id)}`}>Open query trace</Link><p>{row.query_text ?? 'Query text not recorded'}</p><p className="j1-note">{row.created_at} · {row.step_count} steps · {row.total_latency_ms == null ? 'Latency not reported' : `${row.total_latency_ms} ms`}</p></article>)}
  </div>
}
