import { EvalRunDetailClient } from '@/components/performance/EvalRunDetailClient'

export const dynamic = 'force-dynamic'

export default async function EvalRunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <EvalRunDetailClient id={id} />
}
