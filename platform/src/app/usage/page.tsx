import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
export const dynamic = 'force-dynamic'
export default async function UsagePage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const ctx = await getServerUserWithProfile()
  if (!ctx || ctx.profile.status !== 'active') redirect('/login')
  const incoming = await searchParams
  const params = new URLSearchParams()
  for (const key of ['from', 'to', 'channel', 'purpose', 'provider', 'model']) {
    const value = incoming[key]
    if (typeof value === 'string') params.set(key, value)
  }
  redirect(`/observatory/consumption${params.size ? '?' + params : ''}`)
}
