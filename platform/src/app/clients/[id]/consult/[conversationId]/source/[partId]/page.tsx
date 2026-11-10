import { redirect } from 'next/navigation'
import { ReviewSourceReading } from '@/components/consume/ReviewSourceReading'
import { safeNextPath } from '@/lib/auth/safe_next'
import { getServerUser } from '@/lib/firebase/server'
import { buildReviewSourcePath } from '@/lib/pariprashna/samiksha/deepLink'
import '@/components/profile/jataka-workspace.css'

export default async function ReviewSourcePage({
  params,
}: {
  params: Promise<{ id: string; conversationId: string; partId: string }>
}) {
  const { id, conversationId, partId } = await params
  const user = await getServerUser()
  if (!user) {
    const next = safeNextPath(buildReviewSourcePath(id, conversationId, partId))
    redirect(next ? `/login?next=${encodeURIComponent(next)}` : '/login')
  }
  return <ReviewSourceReading chartId={id} conversationId={conversationId} partId={partId} userId={user.uid} focusAnswer />
}
