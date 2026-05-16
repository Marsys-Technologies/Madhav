import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export async function POST(request: Request) {
  const expected = process.env.MARSYS_CRON_SECRET
  const auth = request.headers.get('Authorization')

  if (!expected || auth !== `Bearer ${expected}`) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const result = await query(
    'DELETE FROM pending_streams WHERE expires_at < now() RETURNING query_id',
    [],
  )

  const count = result.rows.length
  return NextResponse.json({ reaped: count })
}
