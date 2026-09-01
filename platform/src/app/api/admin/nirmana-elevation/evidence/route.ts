import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { handleNirmanaEvidenceCommand, nirmanaEvidenceCommand } from '@/lib/nirmana-elevation/evidence-command'

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) {
    auth.headers.set('Cache-Control', 'no-store')
    return auth
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }
  const parsed = nirmanaEvidenceCommand.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: 'invalid Nirmana evidence command', issues: parsed.error.issues }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }

  return handleNirmanaEvidenceCommand(parsed.data, auth.user.uid)
}
