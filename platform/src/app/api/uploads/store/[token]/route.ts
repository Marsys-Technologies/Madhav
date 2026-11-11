import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const NO_STORE = { 'Cache-Control': 'private, no-store' }

interface RouteContext {
  params: Promise<{ token: string }>
}

async function attachmentUnavailable(_request: Request, { params }: RouteContext): Promise<NextResponse> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Unauthenticated' }, { status: 401, headers: NO_STORE })

  const { token } = await params
  if (!UUID_RE.test(token)) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 400, headers: NO_STORE })
  }

  return NextResponse.json({ error: 'Attachment storage is currently unavailable.' }, {
    status: 503, headers: NO_STORE,
  })
}

export async function PUT(request: Request, context: RouteContext): Promise<NextResponse> {
  return attachmentUnavailable(request, context)
}

export async function GET(request: Request, context: RouteContext): Promise<NextResponse> {
  return attachmentUnavailable(request, context)
}
