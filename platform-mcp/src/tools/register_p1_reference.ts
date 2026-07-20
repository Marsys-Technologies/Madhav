/**
 * P1 Group 2 — Reference-layer tools (7 tools)
 * ==============================================
 * Thin read tools over L0 Brahmagyan reference tables.
 * Global scope (no chart_id required), bounded, cited.
 * Per BA-P1 brief §Step 2.
 *
 * ref_rules_search          → marsys://tool/L0/query_classical_texts
 * ref_yogas_get             → marsys://tool/L0/query_yoga_catalog
 * ref_doshas_get            → marsys://tool/L0/query_dosha_catalog
 * ref_dignity_reference_get → marsys://tool/L0/query_classical_texts (topic=dignity)
 * ref_dasha_systems_get     → marsys://tool/L0/query_classical_texts (topic=dasha)
 * ref_nakshatra_get         → marsys://tool/L0/query_classical_texts (topic=nakshatra)
 * ref_transit_rules_get     → bg_transit_rules table via platformQuery
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { describeProxyFailure } from './registry_bridge.js'
import {
  buildTeachingError, reconcileVocabulary,
  YOGA_CATALOG_DOMAINS, YOGA_CATALOG_TRADITIONS, YOGA_DOMAIN_SYNONYMS,
} from './errors_that_teach.js'
import { budgetMcpContent } from '../lib/response_budget.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistryCapability(uri: string, args: Record<string, unknown>, principal: Principal): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding, same class as registry_bridge.ts's identical fix):
    // don't leak the raw HTTP status code into the MCP-facing error text.
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[p1_reference] capability error: ${data.error ?? 'unknown'}`)
  return data.content
}

// R6 0a-envauth (R-16/O-5): only sent x-mcp-internal-token (Layer 1). The target
// route (/api/mcp/db/query) also gates on Layer 2 principal headers —
// `if (!userUid || !keyId) return 401 'Missing principal headers (X-MCP-User, X-MCP-Key-Id)'`
// (platform/src/app/api/mcp/db/query/route.ts) — so every call 401'd, surfacing
// as this function's own `platform DB query failed: 401` message (the literal
// evidence string cited for R-16). Added the two missing headers, matching the
// working 3-header pattern already used by callRegistryCapability() above.
async function platformQuery(
  sql: string,
  params: unknown[],
  principal: Principal,
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
      'x-mcp-user': principal.user_uid,
      'x-mcp-key-id': principal.key_id,
    },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) throw new Error(`[p1_reference] platform DB query failed: ${res.status}`)
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

function envelope(content: unknown, toolName: string) {
  return {
    envelope_version: 'v1',
    tool: toolName,
    verdict: null,
    ranking_basis: null,
    grounding: { fact_ids: [], citations: [], grounding_score: null },
    pagination: { offset: 0, limit: 0, total: null, next_cursor: null },
    drill_pointers: [],
    judgment_flags: [],
    insight_type: null,
    query_class: 'reference',
    content,
  }
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// S3 fix (R5 W0a perf lane): no pretty-print; text duplicate suppressed above
// threshold (structuredContent already carries the full payload).
//
// W3-L5 (budget unification, R-2 item 5 / W-8): this file's 7 ref_* tools previously
// shipped through this dualOutput with NO response-budget pass at all — part of the
// ~36-of-~115 unclamped surface (GT-48). budgetMcpContent (response_budget.ts) applies
// the same generic auto-detect + finalizeMcpBudget mechanism register_p1_aliases.ts's
// dualOutput already uses, keyed off the `tool` field envelope() stamps on every
// response here.
function dualOutput(data: unknown) {
  let finalData = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const toolName = typeof obj['tool'] === 'string' ? obj['tool'] : 'unknown_tool'
    finalData = budgetMcpContent(obj, toolName)
  }
  const structuredContent = { type: 'object' as const, object: finalData }
  const json = JSON.stringify(finalData)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

// ── R-5 fix: typed error envelope, never leak raw SQL/driver detail ──────────
//
// Denial ≠ empty ≠ internal error (register R-5): a caught error's `String(err)` may be a
// deliberately-authored, safe validation/denial message ("chart_id is required",
// "ENTITLEMENT_DENIED: ...") OR a raw driver/SQL error ('column "salience_score" does not
// exist', a stack frame, a connection string). The former is safe to echo verbatim; the
// latter must NEVER reach the client — it leaks internal schema/implementation detail and
// gives callers no stable, typed thing to branch on. classifyErrorMessage() distinguishes
// the three classes; errorOutput() logs the raw detail server-side only when it collapses
// an internal-looking message to the generic safe one.
type McpErrorClass = 'validation' | 'permission_denied' | 'internal_error'

function classifyErrorMessage(message: string): { error_class: McpErrorClass; safe_message: string } {
  if (/ENTITLEMENT_DENIED|AUTHZ_DENIED|lacks .* access/i.test(message)) {
    return { error_class: 'permission_denied', safe_message: message }
  }
  if (/ is required($|[^a-zA-Z])|^either `|^Unknown facet|^Unsupported /i.test(message)) {
    return { error_class: 'validation', safe_message: message }
  }
  const looksInternal =
    /column ".*" does not exist|relation ".*" does not exist|syntax error at or near|ECONNREFUSED|invalid input syntax|PostgresError|\bat \S+\.(ts|js):\d+|\.node_modules[\\/]/i.test(message)
  if (looksInternal) {
    return {
      error_class: 'internal_error',
      safe_message: 'An internal error occurred while serving this request. The specific ' +
        'cause has been logged server-side and is not exposed to the client (never leak raw ' +
        'SQL/driver detail — R-5).',
    }
  }
  return { error_class: 'internal_error', safe_message: message }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const { error_class, safe_message } = classifyErrorMessage(message)
  if (error_class === 'internal_error' && safe_message !== message) {
    console.error(`[${tool}] internal_error (raw, server-only, never sent to client): ${message}`)
  }
  const data = { ok: false, error: { class: error_class, message: safe_message }, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
}

export function registerP1ReferenceTools(server: McpServer, principal: Principal): void {

  // ── 1. ref_rules_search ───────────────────────────────────────────────────
  server.tool(
    'ref_rules_search',
    'Search classical Jyotish texts and rule corpus in the L0 Brahmagyan reference layer. ' +
    'Covers Parashara Hora Shastra, Brihat Jataka, Saravali, Phaladeepika, and other authoritative ' +
    'classical sources stored in bg_classical_texts. Free-text keyword search with optional author, ' +
    'tradition, and topic filters. Returns matched sloka/verse + translation + source reference. ' +
    'Primary tool for grounding interpretive claims in classical authority (B.3 derivation ledger).',
    {
      keyword: z.string().optional().describe('Free-text search term (searches title + body).'),
      author:  z.string().optional().describe('Filter by classical author (e.g. Parashara, Varahamihira).'),
      topic:   z.string().optional().describe('Filter by topic tag (e.g. yoga, transit, nakshatra, dasha).'),
      tradition: z.string().optional().describe('Filter by tradition (e.g. Parashari, Jaimini, Tajaka).'),
      limit:   z.number().int().min(1).max(200).optional().describe('Max results (default: 50)'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ keyword, author, topic, tradition, limit, offset }) => {
      try {
        const data = await callRegistryCapability('marsys://tool/L0/query_classical_texts', {
          keyword, author, topic, tradition, limit: limit ?? 50, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(data, 'ref_rules_search'))
      } catch (err) {
        return errorOutput('ref_rules_search', String(err))
      }
    }
  )

  // ── 2. ref_yogas_get ──────────────────────────────────────────────────────
  server.tool(
    'ref_yogas_get',
    'Retrieve Yoga definitions from the L0 Brahmagyan yoga catalog (bg_yoga_catalog). ' +
    'Returns classical yoga definitions: name, constituent conditions, tradition source, domain tags, ' +
    'activation rule, and expected phala. Supports filtering by yoga name, tradition, and domain. ' +
    'Use to identify which yogas are theoretically possible for a chart BEFORE querying L1 for activations.',
    {
      yoga_name:  z.string().optional().describe('Partial name match (case-insensitive LIKE search).'),
      tradition:  z.string().optional().describe('Filter by tradition (Parashari, Jaimini, Tajaka, etc.).'),
      domain:     z.string().optional().describe('Filter by domain tag (career, wealth, health, etc.).'),
      limit:      z.number().int().min(1).max(500).optional().describe('Max results (default: 100)'),
      offset:     z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ yoga_name, tradition, domain, limit, offset }) => {
      try {
        // CR-7 CLASS / errors-that-teach (D-2 V-3, ledger row 24): the §B.5 domain-vocabulary trap.
        // The stored `category` vocabulary is raja/dhana/aristha/pancha_mahapurusha/sannyasa/other —
        // a caller filtering domain="wealth" gets an HONEST 0 rows, but 0 rows reads like "no wealth
        // yogas exist". If the requested domain isn't in the stored vocabulary, pre-empt with a
        // teaching error naming the corrected call (domain="dhana") instead of a silent empty page.
        if (domain) {
          const rec = reconcileVocabulary(domain, YOGA_CATALOG_DOMAINS, YOGA_DOMAIN_SYNONYMS)
          if (!rec.matched) {
            const corrected = rec.stored_value
              ? { yoga_name, tradition, domain: rec.stored_value, limit, offset }
              : null
            return dualOutput(buildTeachingError(
              'ref_yogas_get',
              `domain="${domain}" is not in the stored yoga-catalog vocabulary — it would return 0 rows ` +
              `(honest, but misleading as "no such yogas").`,
              corrected,
              rec.stored_value
                ? `The stored category for "${domain}" is "${rec.stored_value}". Retry with domain="${rec.stored_value}".`
                : `Use one of the stored categories: ${YOGA_CATALOG_DOMAINS.join(', ')}.`,
              { domain: YOGA_CATALOG_DOMAINS, tradition: YOGA_CATALOG_TRADITIONS },
            ))
          }
          domain = rec.stored_value ?? domain // forward the reconciled stored term
        }
        const data = await callRegistryCapability('marsys://tool/L0/query_yoga_catalog', {
          yoga_name, tradition, domain, limit: limit ?? 100, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(data, 'ref_yogas_get'))
      } catch (err) {
        return errorOutput('ref_yogas_get', String(err))
      }
    }
  )

  // ── 3. ref_doshas_get ─────────────────────────────────────────────────────
  server.tool(
    'ref_doshas_get',
    'Retrieve Dosha definitions from the L0 Brahmagyan dosha catalog (bg_dosha_catalog). ' +
    'Returns classical dosha definitions: name, affliction conditions, severity classification, ' +
    'remediation pathways, and source authority. Covers Mangal Dosha, Kemadruma Yoga, Grahan Yoga, ' +
    'Shrapit Dosha, Shakata Yoga, Kalasarpa/Kaalaamrit, Pitru Dosha, and other classical afflictions. ' +
    'Filter by name or severity to quickly locate relevant doshas.',
    {
      dosha_name: z.string().optional().describe('Partial name match (case-insensitive LIKE search).'),
      severity:   z.string().optional().describe('Filter by severity class (severe/moderate/mild).'),
      limit:      z.number().int().min(1).max(500).optional().describe('Max results (default: 100)'),
      offset:     z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ dosha_name, severity, limit, offset }) => {
      try {
        const data = await callRegistryCapability('marsys://tool/L0/query_dosha_catalog', {
          dosha_name, severity, limit: limit ?? 100, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(data, 'ref_doshas_get'))
      } catch (err) {
        return errorOutput('ref_doshas_get', String(err))
      }
    }
  )

  // ── 4. ref_dignity_reference_get ──────────────────────────────────────────
  // CR-42/R-19/R-20 fix (D-1.6 S-1): this handler used to merge `planet` into a
  // generic keyword string and send it through query_classical_texts' hybrid
  // free-text search as `topic: 'dignity'` — because that capability's freeText
  // priority is query_text ?? query ?? topic, the static 4-letter `topic` value
  // WON the priority race and `planet`/`keyword` were silently discarded
  // (`query_used` was always literally "dignity", confirmed live 2026-07-16:
  // ref_dignity_reference_get(planet="saturn") -> query_used:"dignity", a
  // hybrid-vector dump of the whole corpus instead of Saturn's structured row).
  // Fix: query the REAL structured table (bg_dignity_reference, 9 rows — one
  // per graha, seeded by migration 250) directly by graha when `planet` is
  // given (case-insensitive exact match on the `graha` column). Only fall
  // through to the classical-texts hybrid search when no structured planet
  // match exists, and that fallback is now labelled `source:
  // 'classical_text_fallback'` so a caller can tell structured-table rows
  // from a keyword-search degradation.
  server.tool(
    'ref_dignity_reference_get',
    'Retrieve classical dignity rules and planetary sign-state references from L0 Brahmagyan. ' +
    'Returns classical authority on Ucha (exaltation), Moolatrikona, Swakshetra (own sign), ' +
    'Neecha (debilitation), and own-sign positions — sourced from the structured ' +
    'bg_dignity_reference table (one row per graha) when `planet` is given. ' +
    'Grounds dignity assessments in L0 Brahmagyan authority before interpreting L1 dignity data.',
    {
      planet:  z.string().optional().describe('Filter by planet name (e.g. sun, moon, mars) — matched case-insensitively against the structured bg_dignity_reference table.'),
      keyword: z.string().optional().describe('Free-text search within dignity rules (classical-text fallback; used only when planet is omitted or matches no structured row).'),
      limit:   z.number().int().min(1).max(200).optional().describe('Max results (default: 50)'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ planet, keyword, limit, offset }) => {
      try {
        if (planet) {
          const structured = await platformQuery(
            `SELECT graha, exaltation_sign, exaltation_degree, debilitation_sign, debilitation_degree,
                    moolatrikona_sign, moolatrikona_from, moolatrikona_to, own_signs,
                    classical_citation, notes
             FROM bg_dignity_reference
             WHERE LOWER(graha) = LOWER($1)`,
            [planet],
            principal,
          )
          if (structured.rows.length > 0) {
            return dualOutput(envelope({
              source: 'bg_dignity_reference',
              structured_filter_applied: true,
              planet,
              rows: structured.rows,
              total: structured.rows.length,
            }, 'ref_dignity_reference_get'))
          }
        }
        // No planet given, or planet matched no structured row — degrade to the
        // classical-text hybrid search, but say so explicitly (no silent swap).
        const kw = [keyword, planet, 'dignity'].filter(Boolean).join(' ')
        const data = await callRegistryCapability('marsys://tool/L0/query_classical_texts', {
          query_text: kw, limit: limit ?? 50, offset: offset ?? 0,
        }, principal)
        const dataObj = (typeof data === 'object' && data !== null) ? data as Record<string, unknown> : { result: data }
        return dualOutput(envelope({
          source: 'classical_text_fallback',
          structured_filter_applied: false,
          fallback_reason: planet
            ? `No structured bg_dignity_reference row for planet="${planet}" — degraded to classical-text hybrid search.`
            : 'No planet filter given — classical-text hybrid search over dignity corpus.',
          ...dataObj,
        }, 'ref_dignity_reference_get'))
      } catch (err) {
        return errorOutput('ref_dignity_reference_get', String(err))
      }
    }
  )

  // ── 5. ref_dasha_systems_get ──────────────────────────────────────────────
  server.tool(
    'ref_dasha_systems_get',
    'Retrieve classical Dasha system definitions and sequencing rules from L0 Brahmagyan. ' +
    'Covers Vimshottari (120-year, 9-planet nakshatra-based standard), Yogini (36-year), ' +
    'Ashtottari (108-year), Kalachakra, Shodashottari (116-year), and Jaimini Chara Dasha. ' +
    'Returns system name, total years, planet sequence with period lengths, activation criteria, ' +
    'and source authority. Use before interpreting L1 dasha data.',
    {
      system:  z.string().optional().describe('Filter by dasha system name (e.g. vimshottari, yogini).'),
      keyword: z.string().optional().describe('Free-text search within dasha descriptions.'),
      limit:   z.number().int().min(1).max(100).optional().describe('Max results (default: 30)'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ system, keyword, limit, offset }) => {
      try {
        // CR-42/R-19/R-20 fix (D-1.6 S-1): no structured bg_dasha_systems catalog table
        // exists (confirmed absent from the migration set), so this stays a classical-text
        // search — but it used to send the actual `system` filter value only inside a
        // `keyword` param that query_classical_texts' hybrid handler NEVER READS once
        // `topic` is also present (freeText priority is query_text ?? query ?? topic, so
        // the static 4-letter `topic: 'dasha'` value always won and `system`/`keyword` were
        // silently discarded — confirmed live: system="vimshottari" -> query_used:"dasha").
        // Fix: send the joined filter string via `query_text` (top priority) so `system`
        // genuinely participates in the search, and disclose the degraded mode honestly.
        const kw = [keyword, system, 'dasha system'].filter(Boolean).join(' ')
        const data = await callRegistryCapability('marsys://tool/L0/query_classical_texts', {
          query_text: kw, limit: limit ?? 30, offset: offset ?? 0,
        }, principal)
        const dataObj = (typeof data === 'object' && data !== null) ? data as Record<string, unknown> : { result: data }
        return dualOutput(envelope({
          structured_filter_applied: false,
          fallback_reason: 'No structured bg_dasha_systems catalog table exists — this is a classical-text hybrid search using the system/keyword filter as the search query, not a WHERE-clause match.',
          ...dataObj,
        }, 'ref_dasha_systems_get'))
      } catch (err) {
        return errorOutput('ref_dasha_systems_get', String(err))
      }
    }
  )

  // ── 6. ref_nakshatra_get ──────────────────────────────────────────────────
  server.tool(
    'ref_nakshatra_get',
    'Retrieve classical Nakshatra definitions and characteristics from L0 Brahmagyan. ' +
    'Returns the 27 (or 28) nakshatra definitions: lord, devata, gender, gana (divine/human/demon), ' +
    'varna, nadi, pada lords, body part, symbol, and classical associations. ' +
    'Also covers Tara classification rules (9-fold Janma/Sampat/Vipat/Kshema/Pratyak/Sadhaka/Vadha/' +
    'Mitra/Ati-Mitra) and Abhijit (28th nakshatra). Filter by nakshatra name or lord.',
    {
      nakshatra: z.string().optional().describe('Filter by nakshatra name (e.g. ashwini, rohini, purva_bhadrapada).'),
      lord:      z.string().optional().describe('Filter by ruling planet (e.g. ketu, venus, sun).'),
      keyword:   z.string().optional().describe('Free-text search.'),
      limit:     z.number().int().min(1).max(100).optional().describe('Max results (default: 30)'),
      offset:    z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ nakshatra, lord, keyword, limit, offset }) => {
      try {
        // CR-42/R-19/R-20 fix (D-1.6 S-1): same class of bug as ref_dasha_systems_get above
        // — no structured bg_nakshatra catalog table exists, and `nakshatra`/`lord` were
        // silently discarded because `topic: 'nakshatra'` always won the freeText priority
        // race inside query_classical_texts. Send the joined filter via `query_text` so the
        // actual nakshatra/lord value participates in the search, and disclose the
        // degraded (non-structural) mode honestly.
        const kw = [keyword, nakshatra, lord, 'nakshatra'].filter(Boolean).join(' ')
        const data = await callRegistryCapability('marsys://tool/L0/query_classical_texts', {
          query_text: kw, limit: limit ?? 30, offset: offset ?? 0,
        }, principal)
        const dataObj = (typeof data === 'object' && data !== null) ? data as Record<string, unknown> : { result: data }
        return dualOutput(envelope({
          structured_filter_applied: false,
          fallback_reason: 'No structured bg_nakshatra catalog table exists — this is a classical-text hybrid search using the nakshatra/lord/keyword filter as the search query, not a WHERE-clause match.',
          ...dataObj,
        }, 'ref_nakshatra_get'))
      } catch (err) {
        return errorOutput('ref_nakshatra_get', String(err))
      }
    }
  )

  // ── 7. ref_transit_rules_get ──────────────────────────────────────────────
  server.tool(
    'ref_transit_rules_get',
    'Retrieve Gochara (planetary transit) rule definitions from L0 Brahmagyan (bg_transit_rules). ' +
    'Returns classical transit rules: which transit house from natal Moon is favorable/unfavorable ' +
    'for each planet, Vedha (obstruction) point pairs, and the Ashtakavarga bindu threshold rules. ' +
    'Covers all 9 grahas. Use to contextualize transit quality before interpreting Gochara analysis ' +
    'from the ganita_transit_anchors_get tool.',
    {
      graha:   z.string().optional().describe('Filter by planet (sun/moon/mars/mercury/jupiter/venus/saturn/rahu/ketu).'),
      house:   z.number().int().min(1).max(12).optional().describe('Filter by transit house from natal Moon.'),
      limit:   z.number().int().min(1).max(200).optional().describe('Max results (default: 100)'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ graha, house, limit, offset }) => {
      try {
        // W4-loop-1 (E-5 group1): the prior SELECT referenced columns that do not exist on
        // bg_transit_rules (house_from_moon/quality/rule_text/av_threshold/source_text/
        // created_at) and lowercased `graha` against a capitalized column ("Jupiter"). The
        // real schema is id/rule_type/graha/primary_house/vedha_house/phala/
        // classical_citation/rule_notes. Reconciled + made graha match case-insensitive.
        const params: unknown[] = []
        const filters: string[] = []
        if (graha) { params.push(graha); filters.push(`LOWER(graha) = LOWER($${params.length})`) }
        if (house) { params.push(house); filters.push(`primary_house = $${params.length}`) }
        params.push(limit ?? 100)
        params.push(offset ?? 0)
        const where = filters.length > 0 ? `WHERE ${filters.join(' AND ')}` : ''
        const sql = `
          SELECT id, rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes
          FROM bg_transit_rules
          ${where}
          ORDER BY graha, primary_house
          LIMIT $${params.length - 1} OFFSET $${params.length}
        `
        const result = await platformQuery(sql, params, principal)
        return dualOutput(envelope({
          transit_rules: result.rows,
          total: result.rows.length,
          ...(result.rows.length === 0
            ? { empty_reason: `No transit rules matched (graha=${graha ?? 'any'}, house=${house ?? 'any'}).` }
            : {}),
          filters: { graha, house },
          note: 'primary_house: classical 1-based transit house from natal Moon. vedha_house: obstruction point. phala: classical result text.',
        }, 'ref_transit_rules_get'))
      } catch (err) {
        return errorOutput('ref_transit_rules_get', String(err), { graha, house })
      }
    }
  )
}
