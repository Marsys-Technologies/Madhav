import 'server-only'
import { NextResponse } from 'next/server'
import type { DecodedIdToken } from 'firebase-admin/auth'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export interface ProfileAuth {
  id: string
  role: 'super_admin' | 'guest'
  status: 'pending' | 'active' | 'disabled'
}

export async function getServerUserWithProfile(): Promise<
  { user: DecodedIdToken; profile: ProfileAuth } | null
> {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<ProfileAuth>(
    'SELECT id, role, status FROM profiles WHERE id=$1',
    [user.uid]
  )
  const profile = rows[0] ?? null
  if (!profile) return null
  return { user, profile }
}

export async function requireSuperAdmin(): Promise<
  NextResponse | { user: DecodedIdToken; profile: ProfileAuth }
> {
  const ctx = await getServerUserWithProfile()
  if (!ctx) return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  if (ctx.profile.role !== 'super_admin') {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 })
  }
  if (ctx.profile.status !== 'active') {
    return NextResponse.json({ error: 'account_inactive' }, { status: 403 })
  }
  return ctx
}
