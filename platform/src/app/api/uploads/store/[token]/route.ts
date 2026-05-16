/**
 * PUT  /api/uploads/store/[token]  — store file bytes (dev/fake-gcs)
 * GET  /api/uploads/store/[token]  — retrieve file bytes (dev/fake-gcs)
 *
 * This route exists only for dev. In production the client uploads
 * directly to a real GCS signed URL and this route is never hit.
 *
 * The 16-byte header is inspected for magic-byte validation on PUT
 * so the server can catch polyglot files even before they land in storage.
 */

import { NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { getServerUser } from '@/lib/firebase/server'
import { validateUpload } from '@/lib/multimodal/upload_validator'
import { fakeGcsStore, fakeGcsRetrieve } from '@/lib/multimodal/fake_gcs_store'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

interface RouteContext {
  params: Promise<{ token: string }>
}

export async function PUT(request: Request, context: RouteContext): Promise<NextResponse> {
  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Unauthenticated' }, { status: 401 })
  }

  const { token } = await context.params
  if (!UUID_RE.test(token)) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 400 })
  }

  const contentType = request.headers.get('content-type') ?? 'application/octet-stream'
  const filename = decodeURIComponent(
    request.headers.get('x-filename') ?? `upload-${randomUUID()}`,
  )

  const arrayBuffer = await request.arrayBuffer()
  const bytes = Buffer.from(arrayBuffer)

  if (bytes.length === 0) {
    return NextResponse.json({ error: 'Empty body' }, { status: 400 })
  }

  // Magic-byte validation (polyglot detection) — use first 16 bytes as header
  const headerBytes = bytes.subarray(0, 16)
  const validation = validateUpload(filename, contentType, bytes.length, headerBytes)
  if (!validation.ok) {
    return NextResponse.json({ error: validation.error }, { status: 422 })
  }

  fakeGcsStore(token, validation.sanitizedFilename!, contentType, bytes)

  return NextResponse.json({ ok: true, token, size: bytes.length })
}

export async function GET(request: Request, context: RouteContext): Promise<NextResponse> {
  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Unauthenticated' }, { status: 401 })
  }

  const { token } = await context.params
  if (!UUID_RE.test(token)) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 400 })
  }

  const entry = fakeGcsRetrieve(token)
  if (!entry) {
    return NextResponse.json({ error: 'Not found or expired' }, { status: 404 })
  }

  return new NextResponse(entry.bytes.buffer as ArrayBuffer, {
    status: 200,
    headers: {
      'Content-Type': entry.contentType,
      'Content-Disposition': `inline; filename="${entry.filename}"`,
      'Cache-Control': 'private, max-age=3600',
    },
  })
}
