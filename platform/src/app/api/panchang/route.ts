/**
 * /api/panchang — Next.js API route that proxies the Python sidecar's
 * /api/compute/panchanga endpoint for client-side fetches.
 *
 * Used by usePanchangDay (TanStack Query hook) in the /panchang UI.
 * Server-side SSR path calls queryPanchanga directly (no HTTP hop needed).
 *
 * Phase: 4C-4-S1 (renamed from /api/panchanga to /api/panchang in 0a.1.2 —
 * the duplicate /api/panchanga tree was merged into the canonical /api/panchang
 * tree; a 308 alias is preserved at the old path for one release.)
 */
import { getServerUser } from '@/lib/firebase/server'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'
import { res } from '@/lib/errors'

const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const sidecarUrl = process.env.PYTHON_SIDECAR_URL
  if (!sidecarUrl) return res.sidecarDown()

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid request body')
  }

  // Cross-tenant native_context disclosure guard.
  //
  // This route forwards the request body VERBATIM to the sidecar and returns
  // the sidecar's response VERBATIM. When the body carries a `chart_id`, the
  // sidecar's `_fetch_native_context` reads
  //   SELECT name, birth_date, birth_time, birth_lat, birth_lng FROM charts WHERE id = %s
  // and attaches a `native_context` containing `native_name`,
  // `birth_nakshatra_name`, `moon_sign_name` and `active_dasha_lord`. That
  // function's own docstring states: "caller must already have confirmed chart
  // access (auth is enforced at the Next.js proxy layer; the sidecar trusts the
  // proxy's chart_id)." THIS ROUTE IS THAT PROXY — and it previously enforced
  // only "is anyone logged in", so any authenticated caller could post any
  // chart_id and read that chart's birth data. Confirmed LIVE in production
  // before this fix.
  //
  // 'read' level (permission !== 'deny'): this is read-only disclosure of
  // chart-scoped data, so a chart_grants 'view' grantee legitimately passes —
  // the same bar the sibling asset/cockpit read routes use.
  //
  // `chart_id` is OPTIONAL here. Without one the sidecar returns a
  // location-only panchang with no native_context, which is public-safe; that
  // path must keep working for any authenticated caller and is not gated.
  const chartId =
    body && typeof body === 'object' && typeof (body as { chart_id?: unknown }).chart_id === 'string'
      ? (body as { chart_id: string }).chart_id
      : null
  if (chartId) {
    const denied = await requireChartPermission({ uid: user.uid, chartId, access: 'read' })
    if (denied) return denied
  }

  let sidecarResponse: Response
  try {
    sidecarResponse = await fetch(`${sidecarUrl}/api/compute/panchanga`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': SIDECAR_KEY,
      },
      body: JSON.stringify(body),
    })
  } catch {
    return res.sidecarDown()
  }

  if (!sidecarResponse.ok) {
    if (sidecarResponse.status >= 500) return res.sidecarDown()
    return res.internal('Panchang compute error')
  }

  const data = await sidecarResponse.json()
  return Response.json(data)
}
