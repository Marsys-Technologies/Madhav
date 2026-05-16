/**
 * POST /api/uploads/sign
 *
 * Issues an upload token and upload URL.
 *
 * Dev (no GCS credentials): returns token + /api/uploads/store route URL.
 * Prod (GCS configured):     returns token + real GCS signed URL.
 *
 * Request body: { filename: string, contentType: string, size: number }
 * Response:     { token: string, uploadUrl: string, method: 'PUT' }
 */

import { NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { getServerUser } from '@/lib/firebase/server'
import { validateUpload } from '@/lib/multimodal/upload_validator'

function hasGcsCredentials(): boolean {
  return !!(process.env.GCS_BUCKET_NAME && process.env.GOOGLE_APPLICATION_CREDENTIALS)
}

export async function POST(request: Request): Promise<NextResponse> {
  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Unauthenticated' }, { status: 401 })
  }

  let body: { filename?: unknown; contentType?: unknown; size?: unknown }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const { filename, contentType, size } = body
  if (
    typeof filename !== 'string' ||
    typeof contentType !== 'string' ||
    typeof size !== 'number'
  ) {
    return NextResponse.json({ error: 'filename, contentType, size required' }, { status: 400 })
  }

  // Validate before issuing any token
  const validation = validateUpload(filename, contentType, size)
  if (!validation.ok) {
    return NextResponse.json({ error: validation.error }, { status: 422 })
  }

  const token = randomUUID()

  if (hasGcsCredentials()) {
    // TODO(§M.1): Generate a real GCS signed URL using the Storage client library.
    // Replace this stub with:
    //   const [signedUrl] = await storage.bucket(process.env.GCS_BUCKET_NAME!)
    //     .file(`uploads/${token}/${validation.sanitizedFilename}`)
    //     .getSignedUrl({ action: 'write', expires: Date.now() + 15 * 60 * 1000, contentType })
    // For now fall through to dev path even when env vars are set.
  }

  // Dev / fake-gcs path: client PUTs to /api/uploads/store/[token]
  const uploadUrl = `/api/uploads/store/${token}`
  return NextResponse.json({
    token,
    uploadUrl,
    method: 'PUT',
    filename: validation.sanitizedFilename,
    contentType,
    size,
  })
}
