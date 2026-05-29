import { redirect } from 'next/navigation'

// TODO(H-09): When ConstellationCanvas SSE consumer is wired (session H-09),
// this page will deep-link into a specific build run via conversationId.
// For now, redirect to the main Constellation page to avoid a dead route.
// BuildChat (which previously handled this sub-route) was deleted in H-01.

export default async function BuildConversationPage({
  params,
}: {
  params: Promise<{ id: string; conversationId: string }>
}) {
  const { id } = await params
  redirect(`/clients/${id}/build`)
}
