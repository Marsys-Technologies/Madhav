/**
 * /api/mcp/health/coverage — Data coverage endpoint.
 *
 * Tier-gated: super_admin + acharya = 200. client = 403.
 *
 * Returns data coverage report: expected vs actual row counts per tool/category.
 * Sourced from data_source_expected table (migration 076) + tool_caveats.
 * actual_rows and updated_at are real DB values; graceful fallback when table is empty
 * (Phase 7a seed load not yet applied).
 *
 * MCPT v3.2 Phase 7c
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { query } from '@/lib/db/client'

const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

function extractPrincipal(req: NextRequest): { audience_tier: string } | null {
  const audience_tier = req.headers.get('X-MCP-Audience-Tier')
  if (!audience_tier) return null
  return { audience_tier }
}

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

  const principal = extractPrincipal(req)
  if (!principal) {
    return NextResponse.json({ error: 'Missing principal headers' }, { status: 401 })
  }

  if (principal.audience_tier === 'client' || principal.audience_tier === 'public_redacted') {
    return NextResponse.json(
      {
        error: 'Forbidden',
        message: 'data_coverage is available to super_admin and acharya tiers only.',
        house_rules_uri: 'marsys://house-rules',
      },
      { status: 403 }
    )
  }

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
        tier: principal.audience_tier,
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
      tier: principal.audience_tier,
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
        tier: principal.audience_tier,
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
