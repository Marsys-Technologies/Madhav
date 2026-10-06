import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { OPERATION_SECTIONS, readOperations, type OperationSection } from '@/lib/admin/operations'

export const dynamic = 'force-dynamic'
export async function GET(_request: Request, { params }: { params: Promise<{ section: string }> }) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth
  const { section } = await params
  if (!OPERATION_SECTIONS.includes(section as OperationSection))
    return NextResponse.json({ error: 'Unknown operational view' }, { status: 404 })
  return NextResponse.json(await readOperations(section as OperationSection), { headers: { 'Cache-Control': 'private, no-store' } })
}
