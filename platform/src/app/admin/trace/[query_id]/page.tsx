import { Suspense } from 'react'
import { TraceModal } from '@/components/trace/TraceModal'

export default async function TracePage({ params }: { params: Promise<{ query_id: string }> }) {
  const { query_id } = await params
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <Suspense fallback={
        <div className="flex items-center gap-2 text-[rgba(212,175,55,0.6)] text-sm">
          <span className="animate-spin">◎</span> Loading trace…
        </div>
      }>
        <TraceModal queryId={query_id} />
      </Suspense>
    </div>
  )
}
