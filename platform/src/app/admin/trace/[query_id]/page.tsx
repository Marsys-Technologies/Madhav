import Link from 'next/link'
import { TraceModal } from '@/components/trace/TraceModal'
import { requireSuperAdminPage } from '@/lib/auth/super-admin-page-guard'

export default async function TracePage({ params }: { params: Promise<{ query_id: string }> }) {
  await requireSuperAdminPage()
  const { query_id } = await params
  return (
    <div className="min-w-0 space-y-4">
      <div className="rounded-lg bg-[var(--folio-panel)] px-4 py-3 text-[var(--folio-ink)]">
        <Link href="/admin/trace" className="inline-flex min-h-11 items-center underline underline-offset-4 text-[var(--folio-action)]">
          Back to query sessions
        </Link>
        <h1 className="text-2xl font-semibold">Query Trace</h1>
      </div>
      <TraceModal key={query_id} queryId={query_id} />
    </div>
  )
}
