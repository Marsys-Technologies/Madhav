import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export async function GET() {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Unauthenticated' }, { status: 401 })

  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  const role = rows[0]?.role ?? 'client'

  const response = NextResponse.json({ role })
  response.headers.set('Cache-Control', 'private, max-age=300')
  return response
}
