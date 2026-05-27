/**
 * auth_and_chart — shared stage 1: resolve principal + chart + permission.
 *
 * Extracted from consult/route.ts lines 218–319. The original inline body is
 * preserved verbatim (no behaviour change); this module is the seam so the
 * two pipelines (single_pass + agentic) call exactly the same code.
 *
 * Flow:
 *   1. Validate chart_id shape (UUID).
 *   2. SELECT charts row + profiles.role.
 *   3. authorizeChartAccess (Unit 2c, G2 GREEN) — 'deny' rejects.
 *
 * Returns a discriminated union so the caller can map to HTTP without throwing.
 */

import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import type {
  ResolveContextInput,
  ResolveContextResult,
  ResolvedRequestContext,
} from './types'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

type ChartRow = {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
  client_id: string
}

type ProfileRow = { role: string }

export async function resolveAuthAndChart(
  input: ResolveContextInput,
): Promise<ResolveContextResult> {
  const { userUid, chartId, db } = input

  if (!UUID_RE.test(chartId)) {
    return { ok: false, reason: 'invalid_chart_id', detail: 'chartId must be a valid UUID' }
  }

  let chartResult: { rows: ChartRow[] }
  let profileResult: { rows: ProfileRow[] }
  try {
    ;[chartResult, profileResult] = await Promise.all([
      db.query<ChartRow>(
        'SELECT id, name, birth_date, birth_time, birth_place, client_id FROM charts WHERE id=$1',
        [chartId],
      ),
      db.query<ProfileRow>('SELECT role FROM profiles WHERE id=$1', [userUid]),
    ])
  } catch (err) {
    return { ok: false, reason: 'db_error', detail: String(err) }
  }

  if (!chartResult.rows[0]) return { ok: false, reason: 'chart_not_found' }
  const chart = chartResult.rows[0]
  const role = profileResult.rows[0]?.role
  const isSuperAdmin = role === 'super_admin'

  const principalRole: 'guest' | 'super_admin' = isSuperAdmin ? 'super_admin' : 'guest'
  const permission = await authorizeChartAccess({
    principal: { uid: userUid, role: principalRole },
    chartId,
    db,
  })
  if (permission === 'deny') return { ok: false, reason: 'forbidden' }

  const ctx: ResolvedRequestContext = {
    auth: {
      principal: { uid: userUid, role: principalRole },
      isSuperAdmin,
      permission,
    },
    chart: {
      chartId,
      chart,
    },
  }
  return { ok: true, ctx }
}
