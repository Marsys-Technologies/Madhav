import { NextRequest, NextResponse } from 'next/server'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getStorageClient } from '@/lib/storage'
import { assembleTraceFull } from '@/lib/admin/trace_assembler'
import type { TraceEnvelope } from '@/lib/admin/trace_client'

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
  const envelope = (await assembleTraceFull(query_id, db)) satisfies TraceEnvelope
  return NextResponse.json(envelope)
}
