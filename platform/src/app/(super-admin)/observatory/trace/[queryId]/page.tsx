import { notFound, redirect } from 'next/navigation'
import { requireSuperAdminPage } from '@/lib/auth/super-admin-page-guard'

const QUERY_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export default async function LegacyTracePage({
  params,
}: {
  params: Promise<{ queryId: string }>
}) {
  await requireSuperAdminPage()
  const { queryId } = await params
  if (!QUERY_ID_PATTERN.test(queryId)) notFound()
  redirect(`/admin/trace/${queryId}`)
}
