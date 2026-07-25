/**
 * /api/mcp/db/query — whitelisted read-only DB proxy for MCP synthesis tools.
 *
 * R5 W0a punch-list fix (P6 — "dissent organ" 404). Root cause per
 * RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §20: four MCP tools
 * (synth_tail_divergence_get, bodha_discoveries_get, synth_chart_brief_get,
 * prashna_undertaking_get — platform-mcp/src/tools/register_p1_synthesis.ts)
 * call POST /api/mcp/db/query, but the route never existed in the repo.
 *
 * This is deliberately NOT a general-purpose SQL executor. It is auth-gated
 * (same two-layer model as /api/mcp/primitives/[tool]) AND whitelisted:
 *   - only a single SELECT / WITH-...-SELECT statement is accepted;
 *   - the statement may reference ONLY tables in ALLOWED_TABLES;
 *   - write/DDL keywords and statement-separator characters are rejected
 *     outright, defense-in-depth against the (already-parameterized,
 *     server-authored) call sites ever drifting toward unsafe SQL.
 *
 * Auth model (two-layer, same as /api/mcp/primitives/[tool]):
 *   Layer 1: X-MCP-Internal-Token — service-to-service secret.
 *   Layer 2: X-MCP-User + X-MCP-Key-Id — resolved principal (proves an
 *     authenticated MCP caller, not just the internal-token secret).
 *
 * This route does NOT perform per-chart entitlement checks (the query text
 * is server-authored, not user-authored, and spans multiple tables per call
 * in some tools — table-level whitelisting is the tractable gate here).
 * Callers that read chart-scoped data MUST perform their own
 * remoteAuthorize()/authorizeChartAccess() gate before calling this route
 * (see register_p1_synthesis.ts call sites, which now do this for every
 * chart_id-scoped query per the R5 W0a fix).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

export const maxDuration = 20

// ── Whitelist: tables the four synthesis tools are known to read ───────────

const ALLOWED_TABLES = new Set([
  'bodha_discoveries',
  'bodha_msr_signals',
  'mimamsa_insight_units',
  'ga_prashna_judgment',
  'phala_muhurta',
  'phala_anchors',
  'brahma_activity_ontology',
  // W4-loop-1 (E-5 group1): ref_transit_rules_get (register_p1_reference.ts) reads this
  // L0 Brahmagyan reference table via this route; its absence from the whitelist was the
  // "platform DB query failed: 400" the re-audit saw. Read-only global reference data.
  'bg_transit_rules',
  // SARVA-SIDDHI W-1 T-1 (2026-07-24): the three gochara serving tools
  // (gochara_activation_get / gochara_forecast_get / gochara_election_avoidance_get,
  // platform-mcp/src/tools/retrieval/register_gochara_windows.ts) were re-pointed OFF a
  // self-contained pg.Pool (which read DATABASE_URL — never set on the amjis-mcp Cloud Run
  // service, so every call returned backing_data_reachable:false; register CR-131) ONTO this
  // read-only proxy — the same invariant every other MCP tool honors ("the MCP server does
  // not hold a direct DB connection"). kala_gochara_windows = G-4's signed-intensity standing
  // table (chart-scoped; each tool remoteAuthorize()s the chart before querying, matching the
  // register_p1_synthesis.ts call-site discipline this route's docstring requires).
  // brahma_remedy_corpus = the BPHS-cited remedy table election-avoidance pairs its DR-16
  // mitigation from (global read-only reference). Read-only; no write path added.
  'kala_gochara_windows',
  'brahma_remedy_corpus',
  // SATYA-ŚEṢA W2 (2026-07-25): gochara_forecast_get/activation_get/election_avoidance_get's
  // new category-coverage attestation (`coverage` block, S4-05 fix) computes, mechanically per
  // call, which event_class values the D-5 G-1 sweep actually looked at for THIS chart
  // (gochara_resonance_map — the writer's own docstring: "one substep per populated
  // gochara_resonance_map event_class x decade" — the true "did the sweep even look at this
  // category" source, since kala_gochara_windows can under-report a class that was swept but
  // produced zero rows) and resolves each to a life domain + the full domain universe via
  // brahma_event_ontology (domain column, migration 456). build_substep_progress backs the
  // coverage block's sweep_completeness (execution-axis) disclosure — the same table migration
  // 436 introduced for cross-attempt substep resumption; read-only here, no write path added.
  // Chart-scoped or global read-only reference tables; no write path added by any of the three.
  'gochara_resonance_map',
  'brahma_event_ontology',
  'build_substep_progress',
])

// Forbidden anywhere in the statement: write/DDL verbs and statement separators.
const FORBIDDEN_PATTERN =
  /\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|COPY|EXECUTE|CALL|VACUUM|MERGE)\b|;|--/i

// Matches identifiers following FROM/JOIN (schema-unqualified; this DB has no
// cross-schema tables in the whitelist so unqualified matching is sufficient).
const TABLE_REF_PATTERN = /\b(?:FROM|JOIN)\s+"?([a-zA-Z_][a-zA-Z0-9_]*)"?/gi

function validateSql(sql: string): { ok: true } | { ok: false; reason: string } {
  const trimmed = sql.trim()
  if (!/^(WITH|SELECT)\b/i.test(trimmed)) {
    return { ok: false, reason: 'Only SELECT (optionally WITH ... SELECT) statements are permitted.' }
  }
  if (FORBIDDEN_PATTERN.test(trimmed)) {
    return { ok: false, reason: 'Statement contains a forbidden keyword or separator.' }
  }
  const referenced = new Set<string>()
  let m: RegExpExecArray | null
  TABLE_REF_PATTERN.lastIndex = 0
  while ((m = TABLE_REF_PATTERN.exec(trimmed)) !== null) {
    referenced.add(m[1].toLowerCase())
  }
  if (referenced.size === 0) {
    return { ok: false, reason: 'Could not identify any referenced table (FROM/JOIN clause required).' }
  }
  for (const t of referenced) {
    // CTE names (declared in WITH ... AS (...)) are legitimate self-references
    // that will not appear in ALLOWED_TABLES; only reject real table names.
    if (!ALLOWED_TABLES.has(t) && !trimmed.match(new RegExp(`\\b${t}\\s+AS\\s*\\(`, 'i'))) {
      return { ok: false, reason: `Table '${t}' is not in the read-only whitelist for this route.` }
    }
  }
  return { ok: true }
}

// ── POST handler ─────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json(
      { ok: false, error: { class: 'auth', message: 'Invalid service token' } },
      { status: 401 }
    )
  }

  const userUid = request.headers.get('x-mcp-user')
  const keyId = request.headers.get('x-mcp-key-id')
  if (!userUid || !keyId) {
    return NextResponse.json(
      {
        ok: false,
        error: {
          class: 'auth',
          message: 'Missing principal headers (X-MCP-User, X-MCP-Key-Id)',
        },
      },
      { status: 401 }
    )
  }

  let body: { sql?: string; params?: unknown[] }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      { ok: false, error: { class: 'validation', message: 'Request body must be JSON: { sql, params }' } },
      { status: 400 }
    )
  }

  const sql = body.sql
  const params = body.params ?? []
  if (typeof sql !== 'string' || !sql.trim()) {
    return NextResponse.json(
      { ok: false, error: { class: 'validation', message: 'sql (string) is required' } },
      { status: 400 }
    )
  }

  const validation = validateSql(sql)
  if (!validation.ok) {
    return NextResponse.json(
      { ok: false, error: { class: 'validation', message: `Rejected by whitelist: ${validation.reason}` } },
      { status: 400 }
    )
  }

  try {
    const result = await query<Record<string, unknown>>(sql, params)
    return NextResponse.json({ rows: result.rows ?? [] })
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[mcp:db:query] query failed', msg)
    return NextResponse.json(
      { ok: false, error: { class: 'internal', message: `Query failed: ${msg}` } },
      { status: 500 }
    )
  }
}
