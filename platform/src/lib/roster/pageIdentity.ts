import 'server-only'
import { query } from '@/lib/db/client'
import type { Chart } from '@/lib/db/types'

/**
 * Identity-owned page projections. Callers retain their existing admission guards,
 * sequencing, null handling and error policy. These reads grant no access.
 * Legacy listings intentionally include client_id; canonical chart admission
 * remains independently governed by authorizeChartAccess. Preserve query order/limits.
 */

export function readAdminSwitcherCharts() {
  return query<{ id: string; name: string | null }>('SELECT id, name FROM charts ORDER BY name NULLS LAST, created_at DESC LIMIT 100', [])
}

export function readLegacyGuestSwitcherCharts(uid: string) {
  return query<{ id: string; name: string | null }>(`SELECT c.id, c.name FROM charts c
           WHERE c.owner_id = $1
              OR c.client_id = $1
              OR EXISTS (SELECT 1 FROM chart_grants g WHERE g.chart_id = c.id AND g.principal_id = $1)
           ORDER BY c.name NULLS LAST, c.created_at DESC LIMIT 100`, [uid])
}

export function readAdminDashboardCharts() {
  return query<Chart>('SELECT * FROM charts ORDER BY created_at DESC', [])
}

export function readLegacyGuestDashboardCharts(uid: string) {
  return query<Chart>(`SELECT c.* FROM charts c
         WHERE c.owner_id = $1
            OR c.client_id = $1
            OR EXISTS (
              SELECT 1 FROM chart_grants g
              WHERE g.chart_id = c.id AND g.principal_id = $1
            )
         ORDER BY c.created_at DESC`, [uid])
}
