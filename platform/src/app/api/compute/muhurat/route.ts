/**
 * /api/compute/muhurat — Next.js API route proxying the Python sidecar's
 * POST /api/compute/muhurat endpoint for client-side Muhurat Finder fetches.
 *
 * Used by useMuhuratFinder hook in the /panchang UI (4C-6-S3).
 * Pattern mirrors /api/panchanga/route.ts (4C-4-S1).
 *
 * Phase: 4C-6-S3 (Item 2 — proxy route enabling useMuhuratFinder)
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
    sidecarResponse = await fetch(`${sidecarUrl}/api/compute/muhurat`, {
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
    // Pass through 422 validation errors with their detail field
    const errData = await sidecarResponse.json().catch(() => ({}))
    return Response.json(errData, { status: sidecarResponse.status })
  }

  const data = await sidecarResponse.json()
  return Response.json(data)
}
