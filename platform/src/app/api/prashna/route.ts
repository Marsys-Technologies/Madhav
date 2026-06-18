/**
 * /api/prashna — Next.js API route that proxies the Python sidecar's
 * /api/compute/prashna/cast endpoint.
 *
 * Explicit-invoke Prashna (horary) path:
 *   1. Validate question (sidecar handles deterministic rules)
 *   2. Cast question-moment chart + run ga_prashna judgment
 *   3. Return structured judgment (namespace-isolated from natal stream)
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
    sidecarResponse = await fetch(`${sidecarUrl}/api/compute/prashna/cast`, {
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
    return res.internal('Prashna cast error')
  }

  const data = await sidecarResponse.json()
  return Response.json(data)
}
