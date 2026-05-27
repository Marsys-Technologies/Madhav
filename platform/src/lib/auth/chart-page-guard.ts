import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { authorizeChartAccess, type Permission } from '@/lib/auth/authorizeChartAccess'
import type { DecodedIdToken } from 'firebase-admin/auth'

export interface ChartPageGuardResult {
  user: DecodedIdToken
  role: 'super_admin' | 'guest'
  permission: Permission
  /** Convenience: true when permission === 'all'. Drives Build button visibility. */
  canBuild: boolean
}

/**
 * Resolve the current user + their permission on a specific chart, in one
 * round-trip per call (one profile read + the rules-engine reads inside
 * authorizeChartAccess). Returns null when the user is unauthenticated; the
 * caller redirects to /login.
 *
 * permission semantics (from Unit 2c):
 *   - 'all'  → owner or super_admin: Profile/Build/Consult/Panchang all permitted
 *   - 'view' → grantee via chart_grants: Profile/Consult/Panchang only (no Build)
 *   - 'deny' → no access: caller redirects to /dashboard (3.consult_nav AC.1)
 */
export async function resolveChartPageAccess(
  chartId: string
): Promise<ChartPageGuardResult | null> {
  const user = await getServerUser()
  if (!user) return null

  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid]
  )
  const rawRole = profileResult.rows[0]?.role ?? ''
  const role: 'super_admin' | 'guest' =
    rawRole === 'super_admin' ? 'super_admin' : 'guest'

  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role },
    chartId,
    db: { query },
  })

  return {
    user,
    role,
    permission,
    canBuild: permission === 'all',
  }
}
