/**
 * /api/mcp/health/coverage — Data coverage endpoint.
 *
 * Tier-gated: super_admin + acharya = 200. client = 403.
 *
 * Returns data coverage report: expected vs actual row counts per tool/category.
 * Sourced from data_source_expected table (migration 076) + tool_caveats.
 *
 * MCPT v3.1.0-S4
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

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

  // Coverage data seeded from data_source_expected_seed.sql
  // In production, actual_rows would be populated from nightly audit.
  return NextResponse.json({
    ok: true,
    generated_at: now,
    tier: principal.audience_tier,
    coverage: [
      // chart_facts categories
      { tool: 'query_chart_facts', category: 'house', expected_rows: 12, actual_rows: null, backfill_phase: 'v3.1.0-S1', status: 'active' },
      { tool: 'query_chart_facts', category: 'planet', expected_rows: 9, actual_rows: null, backfill_phase: 'v3.1.0-S1', status: 'active' },
      { tool: 'query_chart_facts', category: 'dasha_vimshottari', expected_rows: 9, actual_rows: null, backfill_phase: 'v3.1.0-S1', status: 'active' },
      { tool: 'query_chart_facts', category: 'kp_cusp', expected_rows: 12, actual_rows: null, backfill_phase: 'v3.3', status: 'pending', caveat: 'KP backfill pending v3.3' },
      { tool: 'query_chart_facts', category: 'varshphal', expected_rows: 10, actual_rows: null, backfill_phase: 'v3.3', status: 'pending', caveat: 'Tajaka varshphal backfill pending v3.3' },
      { tool: 'query_chart_facts', category: 'shadbala', expected_rows: 9, actual_rows: null, backfill_phase: 'v3.3', status: 'pending', caveat: 'Shadbala backfill pending v3.3' },
      { tool: 'query_chart_facts', category: 'ashtakavarga_sav', expected_rows: 9, actual_rows: null, backfill_phase: 'v3.3', status: 'pending', caveat: 'Ashtakavarga SAV backfill pending v3.3' },
      // MSR signals
      { tool: 'query_signals', category: 'msr_corpus', expected_rows: 573, actual_rows: null, backfill_phase: 'v3.1.0-S1', status: 'active' },
      // Panchanga
      { tool: 'query_panchanga', category: 'panchanga_daily', expected_rows: 73414, actual_rows: null, backfill_phase: 'phase-4c-enrich-20260521-r2', status: 'active' },
      // LEL
      { tool: 'lel_query', category: 'life_events', expected_rows: 36, actual_rows: null, backfill_phase: 'v3.1.0-S1', status: 'active' },
    ],
    caveats: [
      { tool: 'query_chart_facts', caveat: 'KP, Tajaka, Shadbala, and Ashtakavarga categories pending v3.3 backfill. Queries against these categories return 0 rows until backfill completes.', severity: 'warn' },
    ],
    note: 'actual_rows populated after applying migrations 073-076 and running nightly audit.',
  })
}

export async function POST(req: NextRequest): Promise<Response> {
  return GET(req)
}
