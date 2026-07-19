/**
 * /api/mcp/health/coverage — Data coverage endpoint.
 *
 * Returns data coverage report: expected vs actual row counts per tool/category.
 * Sourced from data_source_expected table (migration 076) + tool_caveats.
 * actual_rows and updated_at are real DB values; graceful fallback when table is empty
 * (Phase 7a seed load not yet applied).
 *
 * MCPT v3.2 Phase 7c; tier hard-403 removed (Stream A 3.tier_excision 2026-05-28).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

// extractPrincipal removed (Stream A 3.tier_excision 2026-05-28); audience_tier excised from the auth surface.

interface DataSourceExpectedRow {
  tool_name: string
  category: string
  expected_rows: number
  actual_rows: number | null
  backfill_phase: string | null
  notes: string | null
  updated_at: string
}

interface ToolCaveatRow {
  tool_name: string
  caveat_text: string
  severity: string
}

export async function GET(req: NextRequest): Promise<Response> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Tier hard-403 gate removed (Stream A 3.tier_excision 2026-05-28).

  const now = new Date().toISOString()

  try {
    // data_source_expected + tool_caveats dropped in WS-0; always return empty.
    // TODO(ws-2): restore once coverage tables are recreated.
    return NextResponse.json({
      ok: true,
      generated_at: now,
      coverage: [],
      caveats: [],
      note: 'data_source_expected / tool_caveats retired in WS-0 — WS-2 pending',
    })

  } catch (err) {
    // DB unavailable or table doesn't exist yet — graceful degradation
    const message = err instanceof Error ? err.message : String(err)
    const isTableMissing = message.includes('does not exist') || message.includes('relation')

    if (isTableMissing) {
      return NextResponse.json({
        ok: true,
        generated_at: now,
        // tier removed (Stream A 3.tier_excision 2026-05-28).
        coverage: [],
        caveats: [],
        note: 'data_source_expected table not yet seeded — run Phase 7a seed load',
      })
    }

    return NextResponse.json(
      { ok: false, error: 'coverage_query_failed', message },
      { status: 500 }
    )
  }
}

export async function POST(req: NextRequest): Promise<Response> {
  return GET(req)
}
