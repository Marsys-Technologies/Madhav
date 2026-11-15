import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { readBuildRunAssets } from '@/lib/build/runAssets'

export const maxDuration = 8

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const user = await requireSuperAdmin()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const { id } = await params

  try {
    const rows = await readBuildRunAssets(id)

    return NextResponse.json({ data: { run_assets: rows } })
  } catch (err) {
    console.error('[cockpit/runs/assets]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}
