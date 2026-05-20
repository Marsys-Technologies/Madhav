/**
 * /api/panchanga — Next.js API route that proxies the Python sidecar's
 * /api/compute/panchanga endpoint for client-side fetches.
 *
 * Used by usePanchangDay (TanStack Query hook) in the /panchang UI.
 * Server-side SSR path calls queryPanchanga directly (no HTTP hop needed).
 *
 * Phase: 4C-4-S1
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
