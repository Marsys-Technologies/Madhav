// AIOps backend API — shared guard for admin endpoints.
//
// Two-stage gate:
//   1. Feature-flag gate: MARSYS_FLAG_OBSERVATORY_ENABLED must be 'true'
//      (AIOps reuses the same env-var gate as the Observatory super-admin area).
//   2. Auth gate: requireSuperAdmin() — returns 401 (no user), 403 (wrong role).
//
// On success, returns the resolved auth context.

import 'server-only'
import { NextResponse } from 'next/server'
import type { DecodedIdToken } from 'firebase-admin/auth'
import { requireSuperAdmin, type ProfileAuth } from '@/lib/auth/access-control'

export interface AiopsAuthContext {
  user:    DecodedIdToken
  profile: ProfileAuth
}

export async function guardAiopsRoute(): Promise<NextResponse | AiopsAuthContext> {
  if (process.env.MARSYS_FLAG_OBSERVATORY_ENABLED !== 'true') {
    return NextResponse.json(
      { error: { code: 'AUTH_FORBIDDEN', message: 'AIOps is not enabled.', retry: false } },
      { status: 403 },
    )
  }
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth
  return auth
}
