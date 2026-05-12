import type { AssembledTrace, TraceStep } from '@/lib/trace/types'
import type { TraceDocument } from './trace_assembler'

/**
 * The /api/admin/trace/[query_id] endpoint returns this envelope post-Gate II
 * (2026-05-12): the new AssembledTrace + the raw step list + the legacy
 * TraceDocument projection (for consumers not yet migrated).
 */
export interface TraceEnvelope {
  assembled: AssembledTrace
  legacy: TraceDocument
  steps: TraceStep[]
}

export async function fetchTraceEnvelope(queryId: string): Promise<TraceEnvelope> {
  const res = await fetch(`/api/admin/trace/${queryId}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Trace fetch failed: ${res.status}`)
  return res.json() as Promise<TraceEnvelope>
}

/** @deprecated since Gate II (2026-05-12). Use `fetchTraceEnvelope` and read `.legacy`. */
export async function fetchTrace(queryId: string): Promise<TraceDocument> {
  const env = await fetchTraceEnvelope(queryId)
  return env.legacy
}
