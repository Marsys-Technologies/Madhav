import { redirect } from 'next/navigation'
export default async function MeteringPage({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const raw = await searchParams
  const params = new URLSearchParams()
  for (const key of ['from', 'to', 'channel', 'purpose', 'provider', 'model']) {
    const value = raw[key]
    if (typeof value === 'string') params.set(key, value)
  }
  redirect(`/observatory/consumption${params.size ? '?' + params : ''}`)
}
