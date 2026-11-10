// GET /api/admin/observatory/reconciliation/history
//
// Paginated list of past reconciliation runs. Gated by `MARSYS_FLAG_OBSERVATORY_ENABLED`
// flag + `requireSuperAdmin()`.
//
// Query params:
//   provider? — filter to one provider name
//   limit?    — default 50, max 200
//   offset?   — default 0
//
// Schema mapping (frozen migration 038):
//   reconciliation_date  → period_start (YYYY-MM-DD)
//   computed_total_usd   → computed_cost_usd
//   authoritative_total_usd → authoritative_cost_usd
//   reconciled_at        → created_at  (the row's wall-clock creation time)
// Multi-day periods echo the full span in `notes`; for now period_end mirrors
// period_start (S2.x sub-sessions reconcile daily by default).

import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { query } from '@/lib/db/client'
import { guardObservatoryRoute } from '../../_guard'
import type {
  ReconciliationHistoryResponse,
  ReconciliationHistoryRow,
} from '@/lib/observatory/reconciliation/types'

const DEFAULT_LIMIT = 50
const MAX_LIMIT = 200

const VALID_PROVIDERS = new Set([
  'anthropic',
  'openai',
  'gemini',
  'deepseek',
  'nim',
])

interface RawHistoryRow {
  reconciliation_id: string
  provider: string
  reconciliation_date: string
  status: string
  variance_pct: number | null
  computed_total_usd: number
  authoritative_total_usd: number | null
  reconciled_at: string
  notes: string | null
}

function parsePeriodEnd(row: RawHistoryRow): string {
  // notes carries `period=YYYY-MM-DD..YYYY-MM-DD` for multi-day spans; single-day
  // periods omit it. Returning period_start when no span is recorded matches
  // the per-day default from S2.2–S2.5.
  if (row.notes) {
    const m = row.notes.match(/period=(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})/)
    if (m) return m[2]
  }
  return row.reconciliation_date
}

export async function GET(request: Request) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  const url = new URL(request.url)
  const sp = url.searchParams

  const providerParam = sp.get('provider')
  if (providerParam !== null && !VALID_PROVIDERS.has(providerParam)) {
    return res.badRequest(
      `provider must be one of: ${Array.from(VALID_PROVIDERS).join('|')}`,
    )
  }

  const limitRaw = sp.get('limit')
  let limit = DEFAULT_LIMIT
  if (limitRaw !== null) {
    const n = Number(limitRaw)
    if (!Number.isInteger(n) || n < 1) return res.badRequest('limit must be a positive integer')
    limit = Math.min(n, MAX_LIMIT)
  }

  const offsetRaw = sp.get('offset')
  let offset = 0
  if (offsetRaw !== null) {
    const n = Number(offsetRaw)
    if (!Number.isInteger(n) || n < 0) return res.badRequest('offset must be a non-negative integer')
    offset = n
  }

  const params: unknown[] = []
  let where = ''
  if (providerParam !== null) {
    params.push(providerParam)
    where = ' WHERE provider = $1'
  }

  try {
    const countSql = `SELECT COUNT(*)::text AS n FROM llm_cost_reconciliation${where}`
    const countResult = await query<{ n: string }>(countSql, params)
    const total = Number(countResult.rows[0]?.n ?? 0)

    const pageParams = [...params, limit, offset]
    const limitIdx = params.length + 1
    const offsetIdx = params.length + 2
    const pageSql = `
      SELECT
        reconciliation_id,
        provider,
        reconciliation_date::text   AS reconciliation_date,
        status,
        variance_pct,
        computed_total_usd,
        authoritative_total_usd,
        reconciled_at,
        notes
      FROM llm_cost_reconciliation${where}
      ORDER BY reconciliation_date DESC, reconciled_at DESC
      LIMIT $${limitIdx} OFFSET $${offsetIdx}
    `
    const { rows } = await query<RawHistoryRow>(pageSql, pageParams)

    const out: ReconciliationHistoryRow[] = rows.map(r => ({
      reconciliation_id: r.reconciliation_id,
      provider: r.provider,
      period_start: r.reconciliation_date,
      period_end: parsePeriodEnd(r),
      status: r.status,
      variance_pct: r.variance_pct != null ? Number(r.variance_pct) : null,
      computed_cost_usd: Number(r.computed_total_usd),
      authoritative_cost_usd:
        r.authoritative_total_usd != null
          ? Number(r.authoritative_total_usd)
          : null,
      created_at: r.reconciled_at,
    }))

    const body: ReconciliationHistoryResponse = { rows: out, total }
    return NextResponse.json(body)
  } catch (err) {
    console.error('[admin/observatory/reconciliation/history] failed', err)
    return res.internal('Failed to list reconciliation history.')
  }
}
