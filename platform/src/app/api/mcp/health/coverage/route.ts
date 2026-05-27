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

const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// extractPrincipal removed (Stream A 3.tier_excision 2026-05-28); audience_tier excised from the auth surface.

function validateToken(req: NextRequest): boolean {
  const token = req.headers.get('X-MCP-Internal-Token')
  return !!token && token === MCP_INTERNAL_TOKEN
}

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
  if (!validateToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Tier hard-403 gate removed (Stream A 3.tier_excision 2026-05-28).

  const now = new Date().toISOString()

  try {
    // Query data_source_expected for all rows
    const coverageResult = await query<DataSourceExpectedRow>(
      `SELECT tool_name, category, expected_rows, actual_rows, backfill_phase, notes, updated_at
       FROM data_source_expected
       ORDER BY tool_name, category`
    )

    // If table is empty (Phase 7a seed not yet applied), return graceful empty response
    if (coverageResult.rows.length === 0) {
      return NextResponse.json({
        ok: true,
        generated_at: now,
        // tier removed (Stream A 3.tier_excision 2026-05-28).
        coverage: [],
        caveats: [],
        note: 'data_source_expected table not yet seeded — run Phase 7a seed load',
      })
    }

    // Build coverage array from real DB rows
    const coverage = coverageResult.rows.map(row => ({
      tool: row.tool_name,
      category: row.category,
      expected_rows: row.expected_rows,
      actual_rows: row.actual_rows,
      last_updated_at: row.updated_at,
      backfill_phase: row.backfill_phase,
      notes: row.notes ?? undefined,
      status: row.actual_rows !== null && row.actual_rows >= row.expected_rows ? 'ok' : 'low',
    }))

    // Query active caveats from tool_caveats
    let caveats: Array<{ tool: string; caveat: string; severity: string }> = []
    try {
      const caveatResult = await query<ToolCaveatRow>(
        `SELECT tool_name, caveat_text, severity
         FROM tool_caveats
         WHERE active = true
         ORDER BY tool_name, severity`
      )
      caveats = caveatResult.rows.map(row => ({
        tool: row.tool_name,
        caveat: row.caveat_text,
        severity: row.severity,
      }))
    } catch {
      // tool_caveats query failure is non-fatal — return coverage without caveats
      caveats = []
    }

    return NextResponse.json({
      ok: true,
      generated_at: now,
      // tier removed (Stream A 3.tier_excision 2026-05-28).
      coverage,
      caveats,
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
