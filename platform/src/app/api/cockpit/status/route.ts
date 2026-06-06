import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export async function GET() {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const [writersRes, queueRes, activeRunRes] = await Promise.all([
    query<{ count: string }>('SELECT count(*)::text FROM asset_registry WHERE is_active = true'),
    query<{ count: string }>("SELECT count(*)::text FROM build_runs WHERE state IN ('running','paused')"),
    query<{ id: string }>("SELECT id FROM build_runs WHERE state = 'running' LIMIT 1"),
  ])

  return NextResponse.json({
    data: {
      writers: writersRes.rows[0]?.count ?? '0',
      queue:   queueRes.rows[0]?.count ?? '0',
      build:   activeRunRes.rows[0] ? 'running' : 'idle',
    },
  })
}
