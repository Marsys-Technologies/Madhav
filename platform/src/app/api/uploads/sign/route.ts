import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { validateUpload } from '@/lib/multimodal/upload_validator'

const NO_STORE = { 'Cache-Control': 'private, no-store' }

function failure(error: string, status: number) {
  return NextResponse.json({ error }, { status, headers: NO_STORE })
}

export async function POST(request: Request): Promise<NextResponse> {
  const user = await getServerUser()
  if (!user) return failure('Unauthenticated', 401)

  let body: { filename?: unknown; contentType?: unknown; size?: unknown } | null
  try {
    body = await request.json()
  } catch {
    return failure('Invalid JSON', 400)
  }

  if (typeof body?.filename !== 'string' || typeof body.contentType !== 'string' || typeof body.size !== 'number') {
    return failure('filename, contentType, size required', 400)
  }

  const validation = validateUpload(body.filename, body.contentType, body.size)
  if (!validation.ok) return failure(validation.error ?? 'Invalid upload', 422)

  return failure('Attachment uploads are currently unavailable.', 503)
}
