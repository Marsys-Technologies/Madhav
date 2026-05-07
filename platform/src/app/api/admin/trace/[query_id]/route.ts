import { NextRequest, NextResponse } from 'next/server'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getStorageClient } from '@/lib/storage'
import { assembleTrace } from '@/lib/admin/trace_assembler'

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ query_id: string }> },
) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (ctx.profile.role !== 'super_admin') return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  if (ctx.profile.status !== 'active') return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const { query_id } = await params
  const db = getStorageClient()
  const trace = await assembleTrace(query_id, db)
  return NextResponse.json(trace)
}
