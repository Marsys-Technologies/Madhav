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
  // ADJUDICATION-6 (migration 527, w2g-generation-schema): the per-chart
  // authority pointer register_gochara_windows.ts's three serving queries
  // now correlate against (COALESCE((SELECT authoritative_generation FROM
  // kala_gochara_authority WHERE chart_id=...), 'v1')) to resolve which
  // generation is currently served. Read-only; the table itself is written
  // only by a future cutover flip, never by any MCP-served query.
  'kala_gochara_authority',
  // WP7 packet P-1 §4 (2026-09-24, WP0 E-004 item 1): the gochara serving tools'
  // manifest-driven provenance/coverage (N-10) reads these two relations through
  // this proxy. kala_gochara_publication = one manifest row per (chart_id,
  // generation) written by the candidate pipeline and by the release authority's
  // WP10 flip — never by any MCP-served query. kala_gochara_coverage = the
  // ka_gochara writer's own search-coverage manifest (chart-scoped, read-only).
  'kala_gochara_publication',
  'kala_gochara_coverage',
  // WP7 packet P-4 §4 (2026-09-24): the contact-ledger read capability
  // (gochara_contact_ledger_get) reads the per-contact episode grain through
  // this proxy. kala_gochara_contacts is written only by the ka_gochara
  // candidate pipeline (migration 1081) — read-only here, same contract as
  // the two relations above.
  'kala_gochara_contacts',
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
  // PARISHODHANA B1 (newly-discovered regression, distinct from CR-42): the D-1.6 S-1
  // CR-42 fix rewrote ref_dignity_reference_get (register_p1_reference.ts) to query this
  // structured L0 table directly by graha instead of routing `planet` through the
  // classical-text hybrid search — but the corresponding whitelist entry was never added
  // here, so every live call 400'd with "Table 'bg_dignity_reference' is not in the
  // read-only whitelist for this route." (same failure class e2fe0bdd already fixed once
  // for bg_transit_rules). Read-only L0 Brahmagyan reference table (migration 250); no
  // write path added.
  'bg_dignity_reference',
  // F04: ref_nakshatra_get reads the canonical global catalog and its correlated
  // pada-lord rows through this SELECT-only proxy. Both tables are reference data
  // (migration 238), and the MCP handler has no write capability.
  'reference_nakshatra',
  'reference_nakshatra_pada',
  // ṢAḌ-DARŚANA W2 (E5 follow-up to PR #1033): resolveFieldSnapshot
  // (platform-mcp/src/lib/kala_envelope.ts) reads the chart's newest field-snapshot row
  // (`SELECT field_snapshot_id, field_content_hash ... ORDER BY built_at DESC, field_snapshot_id
  // DESC LIMIT 1`) through this route for every kala_* facade's envelope — until this entry
  // landed, the route 400'd the query and production served the honest
  // `field_snapshot_unreachable` marker (the disclosed KNOWN HONEST GAP in that function's
  // docstring). Chart-scoped, written only by the ka_kshetra sidecar writer; read-only here,
  // no write path added.
  'kala_field_snapshots',
  // ṢAḌ-DARŚANA W2.7 (lane w2fin, 2026-08-06): kala_priority_get reads kala_field_salience
  // to serve the real five-axis salience vector (item 25: Informativeness/Consequence/
  // Relevance/Reliability/Actionability) when rows exist for the chart. The prior W0 facade
  // reported this as not_in_corpus; this wiring promotes it to computed/honest_empty based
  // on actual DB state. Chart-scoped (chart_id FK), written only by ka_kshetra stage 6;
  // read-only here, no write path added.
  // kala_insights added for W2.8 ordering verification (kala_ahead_get / kala_story_get
  // must lead with the highest-scoring insight_score row). Same writer, same chart scope.
  'kala_field_salience',
  'kala_insights',
  // V4 Bundle B: every kala_* facade reads the chart-level aggregate maturity row
  // (event_class IS NULL) plus its per-class coverage count from this migration-497 table.
  // The query is server-authored, SELECT-only, and chart-scoped; the facade has already
  // authorized the chart before it reaches this proxy. No write capability is added.
  'kala_field_skill',
  // SM-γ C5 (SAMPŪRTI-γ lane C5, 2026-08-13): ahead_autofile.ts's SM_GAMMA_C5_ENABLED path
  // queries kala_field_windows to find the best-matching field window overlapping a served
  // AHEAD window (by chart_id + event_class + date range) and enrich authority_basis with the
  // field_window provenance (item-44 format). Chart-scoped (chart_id FK), written only by
  // ka_kshetra; read-only here, no write path added. Gated behind SM_GAMMA_C5_ENABLED=true.
  'kala_field_windows',
  // MR-25 (PARIṢKĀRA, migration 565): register_gochara_windows.ts's verse_refs
  // lookup queries bg_gochara_citation_resolution to resolve gochara citation
  // strings (gochara_grammar/citations.py constants) to classical_text_chunks
  // verse_refs. Global read-only reference table; no write path added.
  'bg_gochara_citation_resolution',
])

// Forbidden anywhere in the statement: write/DDL verbs and statement separators.
const FORBIDDEN_PATTERN =
  /\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|COPY|EXECUTE|CALL|VACUUM|MERGE)\b|;|--/i

// S9 item 8 (hardening, held). The checks below run on a COPY of the statement in which
// single-quoted string literals and quoted identifiers have been stripped
// (stripLiteralsAndQuotedIdentifiers); the ORIGINAL text is what gets executed, unchanged.
// Stripping stops text inside a literal from being read as SQL structure (for example a literal
// `', profiles AS ('` satisfying the CTE-name check, or a literal comma/FROM hiding a clause).
//
// This is defense in depth over a server-authored query surface. The real fixes still owed are
// a read-only DB role for this route and live key validation.

// Block comments (`FROM/**/profiles` defeats the \s+ in the table-ref scan) and dollar-quote tags
// (a dollar-quoted body is an opaque string to the copy but SQL to the server). Checked on the
// original text; a literal containing either is rejected too, which is the conservative side.
const BLOCK_COMMENT_PATTERN = /\/\*|\*\//
const DOLLAR_QUOTE_PATTERN = /\$[A-Za-z_]*\$/

// `(TABLE profiles)` is a complete relation reference that the FROM/JOIN scan never sees;
// LATERAL re-opens correlated FROM items; INTO makes SELECT ... INTO create a table.
const TABLE_COMMAND_PATTERN = /\bTABLE\s+\w/i
const LATERAL_PATTERN = /\bLATERAL\b/i
const SELECT_INTO_PATTERN = /\bINTO\b/i

// Functions that execute SQL passed as a string, read the server filesystem, or have
// session/process side effects. The allowlist reasons about table references in the text; none
// of these are visible to it, so they are denied by name (case-insensitive, word-boundary).
// ts_stat is not on the originally specified list; it executes a query string the same way
// query_to_xml does.
const FORBIDDEN_FUNCTION_PATTERN =
  /\b(?:query_to_xml\w*|table_to_xml\w*|cursor_to_xml|schema_to_xml\w*|database_to_xml\w*|dblink\w*|pg_read_file|pg_read_binary_file|pg_ls_dir|pg_stat_file|lo_\w*|set_config|pg_sleep\w*|current_setting|pg_terminate_backend|pg_cancel_backend|ts_stat)\b/i

// Matches relation identifiers following FROM/JOIN (schema-unqualified; this DB
// has no cross-schema tables in the whitelist so unqualified matching is
// sufficient). A PostgreSQL table function such as `FROM UNNEST(...)` is not a
// relation and must not be mistaken for an unallowlisted table.
const TABLE_REF_PATTERN = /\b(?:FROM|JOIN)\s+"?([a-zA-Z_][a-zA-Z0-9_]*)"?\b(?!\s*\()/gi

// `FROM (` / `JOIN (` : either a subquery or a parenthesised joined table.
const PAREN_FROM_ITEM_PATTERN = /\b(?:FROM|JOIN)\s*\(([\s(]*)([A-Za-z_]\w*)?/gi

// A FROM item list ends at the first of these at paren depth 0 (or an unmatched `)`).
const FROM_LIST_TERMINATORS = new Set([
  'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'UNION', 'INTERSECT', 'EXCEPT',
  'OFFSET', 'FETCH', 'FOR', 'WINDOW',
])

// A quoted identifier that is a bare word is unwrapped so it is still matched against the
// allowlist (`FROM "profiles"` must be seen as profiles); anything else becomes a neutral
// placeholder. Words that would change clause structure if unwrapped also become the placeholder.
const SIMPLE_IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*$/
const STRUCTURAL_WORDS = new Set([
  'FROM', 'JOIN', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'UNION', 'INTERSECT', 'EXCEPT',
  'OFFSET', 'FETCH', 'FOR', 'WINDOW', 'TABLE', 'LATERAL', 'SELECT', 'WITH', 'INTO', 'AS', 'ON',
])

function isWordChar(c: string | undefined): boolean {
  return c !== undefined && /[A-Za-z0-9_$]/.test(c)
}

/**
 * Returns a copy of `sql` with single-quoted string literals replaced by ` '' ` and quoted
 * identifiers replaced by their bare name (or ` _q_ `), padded with spaces so adjacent keywords
 * cannot fuse. Returns null (caller rejects) for an unterminated quote or for E'..' / U&'..'
 * strings, whose backslash escapes would make this scan disagree with the server about where
 * a literal ends.
 */
function stripLiteralsAndQuotedIdentifiers(sql: string): string | null {
  let out = ''
  let i = 0
  while (i < sql.length) {
    const ch = sql[i]
    if (ch === "'") {
      const prev = sql[i - 1]
      if ((prev === 'E' || prev === 'e') && !isWordChar(sql[i - 2])) return null
      if (prev === '&' && (sql[i - 2] === 'U' || sql[i - 2] === 'u') && !isWordChar(sql[i - 3])) return null
      let j = i + 1
      for (;;) {
        if (j >= sql.length) return null
        if (sql[j] === "'") {
          if (sql[j + 1] === "'") {
            j += 2
            continue
          }
          break
        }
        j++
      }
      out += " '' "
      i = j + 1
      continue
    }
    if (ch === '"') {
      let content = ''
      let j = i + 1
      for (;;) {
        if (j >= sql.length) return null
        if (sql[j] === '"') {
          if (sql[j + 1] === '"') {
            content += '"'
            j += 2
            continue
          }
          break
        }
        content += sql[j]
        j++
      }
      const bare = SIMPLE_IDENTIFIER.test(content) && !STRUCTURAL_WORDS.has(content.toUpperCase())
      out += bare ? ` ${content} ` : ' _q_ '
      i = j + 1
      continue
    }
    out += ch
    i++
  }
  return out
}

/** Index of the `)` matching the `(` at `open`, or -1. */
function matchingParenEnd(s: string, open: number): number {
  let depth = 0
  for (let k = open; k < s.length; k++) {
    if (s[k] === '(') depth++
    else if (s[k] === ')') {
      depth--
      if (depth === 0) return k
    }
  }
  return -1
}

function parenDepthAt(s: string, idx: number): number {
  let depth = 0
  for (let k = 0; k < idx; k++) {
    if (s[k] === '(') depth++
    else if (s[k] === ')') depth--
  }
  return depth
}

/**
 * True only if `name` is declared as a top-level WITH-list CTE whose body is fully CLOSED before
 * `refIndex`. A non-recursive CTE cannot see itself or later siblings (a reference there is the
 * real table), and a WITH nested inside a subquery is not in scope outside it, so neither counts.
 */
function isCteDeclaredBefore(s: string, name: string, refIndex: number): boolean {
  const decl = new RegExp(
    `(?:\\bWITH\\s+(?:RECURSIVE\\s+)?|,)\\s*"?${name}"?\\s+AS\\s*\\(`,
    'gi'
  )
  let m: RegExpExecArray | null
  while ((m = decl.exec(s)) !== null) {
    if (parenDepthAt(s, m.index) !== 0) continue
    const end = matchingParenEnd(s, m.index + m[0].length - 1)
    if (end !== -1 && end < refIndex) return true
  }
  return false
}

/**
 * Rejects a comma-join. For every FROM, scan forward at paren/bracket depth 0 to the end of the
 * FROM item list; a top-level `,` there is an implicit cross join whose later tables the
 * FROM/JOIN identifier scan never sees (`FROM allowed a, profiles p`). Commas inside parentheses
 * (`FROM (SELECT a, b ...) x`, `FROM unnest(...) AS t(a, b)`) are depth > 0 and are fine.
 */
function hasTopLevelCommaInFromList(s: string): boolean {
  const fromRe = /\bFROM\b/gi
  let m: RegExpExecArray | null
  while ((m = fromRe.exec(s)) !== null) {
    // `a IS DISTINCT FROM b` is a comparison, not a FROM clause.
    if (/\bDISTINCT\s+$/i.test(s.slice(0, m.index))) continue
    let depth = 0
    for (let k = m.index + m[0].length; k < s.length; k++) {
      const c = s[k]
      if (c === '(' || c === '[') {
        depth++
        continue
      }
      if (c === ')' || c === ']') {
        if (depth === 0) break
        depth--
        continue
      }
      if (depth !== 0) continue
      if (c === ',') return true
      if (/[A-Za-z_]/.test(c) && !isWordChar(s[k - 1])) {
        const word = /^[A-Za-z_]\w*/.exec(s.slice(k))![0]
        if (FROM_LIST_TERMINATORS.has(word.toUpperCase())) break
        k += word.length - 1
      }
    }
  }
  return false
}

function isNonSubqueryJoinedTable(s: string): boolean {
  // `FROM (profiles p CROSS JOIN d)` is a legal parenthesised joined table whose first relation
  // follows no FROM/JOIN keyword. Anything parenthesised that is not a subquery/VALUES and
  // contains a JOIN is refused. (`EXTRACT(EPOCH FROM (a - b))` has no JOIN and is unaffected.)
  PAREN_FROM_ITEM_PATTERN.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = PAREN_FROM_ITEM_PATTERN.exec(s)) !== null) {
    const first = (m[2] ?? '').toUpperCase()
    if (first === 'SELECT' || first === 'WITH' || first === 'VALUES') continue
    const open = s.indexOf('(', m.index)
    const end = matchingParenEnd(s, open)
    const inner = s.slice(open, end === -1 ? s.length : end)
    if (/\bJOIN\b/i.test(inner)) return true
  }
  return false
}

function validateSql(sql: string): { ok: true } | { ok: false; reason: string } {
  const trimmed = sql.trim()
  if (!/^(WITH|SELECT)\b/i.test(trimmed)) {
    return { ok: false, reason: 'Only SELECT (optionally WITH ... SELECT) statements are permitted.' }
  }
  if (FORBIDDEN_PATTERN.test(trimmed)) {
    return { ok: false, reason: 'Statement contains a forbidden keyword or separator.' }
  }
  if (BLOCK_COMMENT_PATTERN.test(trimmed)) {
    return { ok: false, reason: 'Block comments are not permitted.' }
  }
  if (DOLLAR_QUOTE_PATTERN.test(trimmed)) {
    return { ok: false, reason: 'Dollar-quoted strings are not permitted.' }
  }
  // Every structural check below reads the stripped copy; `sql` itself is what executes.
  const scan = stripLiteralsAndQuotedIdentifiers(trimmed)
  if (scan === null) {
    return { ok: false, reason: 'Unterminated quote or escape-string syntax is not permitted.' }
  }
  if (TABLE_COMMAND_PATTERN.test(scan)) {
    return { ok: false, reason: 'TABLE <name> is not permitted.' }
  }
  if (LATERAL_PATTERN.test(scan)) {
    return { ok: false, reason: 'LATERAL is not permitted.' }
  }
  if (SELECT_INTO_PATTERN.test(scan)) {
    return { ok: false, reason: 'SELECT ... INTO is not permitted.' }
  }
  if (FORBIDDEN_FUNCTION_PATTERN.test(scan)) {
    return { ok: false, reason: 'Statement calls a function that is not permitted on this route.' }
  }
  if (hasTopLevelCommaInFromList(scan)) {
    return { ok: false, reason: 'Comma-joins in a FROM clause are not permitted; use an explicit JOIN.' }
  }
  if (isNonSubqueryJoinedTable(scan)) {
    return { ok: false, reason: 'Parenthesised joined tables in FROM/JOIN are not permitted.' }
  }
  const references: Array<{ name: string; index: number }> = []
  let m: RegExpExecArray | null
  TABLE_REF_PATTERN.lastIndex = 0
  while ((m = TABLE_REF_PATTERN.exec(scan)) !== null) {
    references.push({ name: m[1].toLowerCase(), index: m.index })
  }
  if (references.length === 0) {
    return { ok: false, reason: 'Could not identify any referenced table (FROM/JOIN clause required).' }
  }
  let hasAllowedBaseRelation = false
  for (const ref of references) {
    // CTE names (declared in WITH ... AS (...)) are legitimate references that will not appear
    // in ALLOWED_TABLES; only reject real table names.
    if (ALLOWED_TABLES.has(ref.name)) {
      hasAllowedBaseRelation = true
      continue
    }
    if (!isCteDeclaredBefore(scan, ref.name, ref.index)) {
      return { ok: false, reason: `Table '${ref.name}' is not in the read-only whitelist for this route.` }
    }
  }
  if (!hasAllowedBaseRelation) {
    return { ok: false, reason: 'Query must reference at least one allowlisted base table.' }
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
