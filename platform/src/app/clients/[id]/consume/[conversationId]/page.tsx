/**
 * Deprecation alias — unit 0a.1 (consume → consult rename).
 *
 * Permanent redirect (Next.js 308) to the new /consult/[conversationId] path.
 */
import { permanentRedirect } from 'next/navigation'

export default async function ConsumeConversationAliasPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string; conversationId: string }>
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const { id, conversationId } = await params
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(await searchParams)) {
    if (typeof value === 'string') query.append(key, value)
    else if (Array.isArray(value)) for (const item of value) query.append(key, item)
  }
  const suffix = query.size ? `?${query}` : ''
  permanentRedirect(`/clients/${id}/consult/${conversationId}${suffix}`)
}
