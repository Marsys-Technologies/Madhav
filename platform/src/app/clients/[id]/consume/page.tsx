/**
 * Deprecation alias — unit 0a.1 (consume → consult rename).
 *
 * Permanent redirect (Next.js 308) to the new /consult path. Preserves the
 * chart id segment and any query string. Remove after one release cycle.
 */
import { permanentRedirect } from 'next/navigation'

export default async function ConsumeAliasPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  const { id } = await params
  const sp = await searchParams

  const qs = new URLSearchParams()
  for (const [key, value] of Object.entries(sp)) {
    if (typeof value === 'string') qs.append(key, value)
    else if (Array.isArray(value)) for (const v of value) qs.append(key, v)
  }
  const qsStr = qs.toString()
  const target = `/clients/${id}/consult${qsStr ? `?${qsStr}` : ''}`

  permanentRedirect(target)
}
