import { redirect } from 'next/navigation'
export default async function LegacyReadings({ searchParams }: { searchParams: Promise<{ conversationId?: string; id?: string }> }) {
  const params = await searchParams
  const id = params.conversationId ?? params.id
  redirect(id ? `/readings/${encodeURIComponent(id)}` : '/dashboard')
}
