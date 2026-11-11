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

  const args = body && typeof body === 'object' ? body as Record<string, unknown> : {}
  const { chart_id: rawChartId, date, lat, lon, tz_offset_minutes, fields } = args
  if (rawChartId !== undefined && rawChartId !== null) {
    if (typeof rawChartId !== 'string' || rawChartId.trim() === '') {
      return res.badRequest('chart_id must be a non-empty string')
    }
  }

  // Calendar parameters can be scalars or a field-name list. Refuse nested
  // request objects even under an allowed calendar key.
  if ([date, lat, lon, tz_offset_minutes].some((value) => value !== null && typeof value === 'object')
    || (fields != null && (!Array.isArray(fields) || fields.some((field) => typeof field !== 'string')))) {
    return res.internal('Panchang compute error')
  }

  let sidecarResponse: Response
  try {
    sidecarResponse = await fetch(`${sidecarUrl}/api/compute/panchanga`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': SIDECAR_KEY,
      },
      body: JSON.stringify({ date, lat, lon, tz_offset_minutes, fields }),
    })
  } catch {
    return res.sidecarDown()
  }

  if (!sidecarResponse.ok) {
    if (sidecarResponse.status >= 500) return res.sidecarDown()
    return res.internal('Panchang compute error')
  }

  let data: unknown
  try {
    data = await sidecarResponse.json()
  } catch {
    return res.internal('Panchang compute error')
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) return Response.json(data)

  const calendar = data as Record<string, unknown>
  // Calendar responses may still come from a sidecar that includes legacy context.
  if ('native_context' in calendar) calendar.native_context = null
  if ('native_context_error' in calendar) calendar.native_context_error = null
  const panchang = calendar.panchang
  if (typeof rawChartId !== 'string' || calendar.ok !== true
    || !panchang || typeof panchang !== 'object' || Array.isArray(panchang)) {
    return Response.json(calendar)
  }

  return Response.json({
    ...calendar,
    native_context: null,
    native_context_error: 'Chart overlay unavailable',
  })
}
