/**
 * Deprecation alias — unit 0a.1 (consume → consult rename).
 *
 * Permanent redirect (Next.js 308) to the new /consult/[conversationId] path.
 */
import { permanentRedirect } from 'next/navigation'

export default async function ConsumeConversationAliasPage({
  params,
}: {
  params: Promise<{ id: string; conversationId: string }>
}) {
  const { id, conversationId } = await params
  permanentRedirect(`/clients/${id}/consult/${conversationId}`)
}
