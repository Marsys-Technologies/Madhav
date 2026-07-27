/**
 * chart_snapshot.ts — MCP resource: marsys://chart-snapshot
 *
 * NEW in v3.1 (MCPT v3.1.0-S3). Structured L1 facts generated at session attach.
 * ~2.5k tokens. Pure facts — no prose synthesis.
 *
 * Reads from: chart_facts table (categories: planet, karaka, house, metadata) +
 *   query_dasha_periods(active_only:true) + query_panchanga(today)
 *
 * IMPORTANT — B.10 compliance: ALL L1 chart values (planetary positions, lagna
 * degree, karaka assignments) are read live from the chart_facts DB table via
 * query_chart_facts. No L1 values are hardcoded in this file. If the DB does
 * not yet contain a fact, this resource emits an explicit placeholder directing
 * the consumer to call query_chart_facts directly. This ensures consumers always
 * receive the DB-authoritative value, never a stale static string.
 *
 * MCPT v3.1.0-S3 (B.10-fixed: GA-1-7)
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Fetch helpers ──────────────────────────────────────────────────────────────

async function fetchPrimitive(toolName: string, params: Record<string, unknown>, userUid: string): Promise<unknown> {
  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${toolName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': userUid,
        'X-MCP-Audience-Tier': 'super_admin',
        'X-MCP-Key-Id': 'resource-loader',
      },
      body: JSON.stringify({ params }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

// ── chart_facts row type ───────────────────────────────────────────────────────

interface ChartFactRow {
  fact_id: string
  category: string
  divisional_chart?: string
  value_text?: string | null
  value_number?: number | null
  value_json?: unknown
  source_section?: string
}

/** Extract facts array from a fetchPrimitive response. Returns [] if absent. */
function extractFacts(response: unknown): ChartFactRow[] {
  if (!response || typeof response !== 'object') return []
  const r = response as Record<string, unknown>
  // Shape: { result: { count, facts: [...] } }
  const result = r['result']
  if (!result || typeof result !== 'object') return []
  const rr = result as Record<string, unknown>
  const facts = rr['facts']
  if (!Array.isArray(facts)) return []
  return facts as ChartFactRow[]
}

// ── Section renderers — all read from DB rows only ────────────────────────────

/**
 * Render Lagna section from DB rows with fact_id prefix 'PLN.LAGNA' or
 * category 'metadata'/'special_lagna'. If absent: explicit placeholder.
 */
function renderLagna(facts: ChartFactRow[]): string[] {
  const lines: string[] = ['## Lagna']
  // Lagna rows are stored with fact_id matching PLN.LAGNA.* or category metadata/special_lagna
  const lagnaRows = facts.filter(
    (f) =>
      f.fact_id.startsWith('PLN.LAGNA') ||
      f.category === 'special_lagna' ||
      (f.category === 'metadata' && f.fact_id.includes('LAGNA'))
  )
  if (lagnaRows.length === 0) {
    lines.push(
      '- [DATA_NOT_IN_DB — lagna position not yet seeded into chart_facts.' +
        ' Call query_chart_facts(category:"special_lagna") or query_chart_facts(fact_id:"PLN.LAGNA.D1") for live data.]'
    )
  } else {
    for (const row of lagnaRows) {
      const val = row.value_text ?? (row.value_number !== null ? String(row.value_number) : '?')
      lines.push(`- ${row.fact_id}: ${val}`)
    }
  }
  lines.push('')
  return lines
}

/**
 * Render Planetary Positions (D1) section from DB rows with category 'planet'
 * and divisional_chart 'D1'. Groups attribute rows by planet name extracted
 * from fact_id (PLN.<PLANET>.<ATTRIBUTE>). If absent: explicit placeholder.
 */
function renderPlanetaryPositions(facts: ChartFactRow[]): string[] {
  const lines: string[] = ['## Planetary Positions (D1)', '*Source: chart_facts table — category:planet, D1 rows*']
  const planetRows = facts.filter((f) => f.category === 'planet' && (f.divisional_chart === 'D1' || !f.divisional_chart))

  if (planetRows.length === 0) {
    lines.push(
      '',
      '[DATA_NOT_IN_DB — planetary position rows (house, sign, degree, nakshatra) not yet seeded' +
        ' into chart_facts. Call query_chart_facts(category:"planet", divisional_chart:"D1") for' +
        ' live data once seeding is complete.]'
    )
    lines.push('')
    return lines
  }

  // Group by planet name (second segment of fact_id: PLN.<PLANET>.<ATTR>)
  const byPlanet = new Map<string, Record<string, string>>()
  for (const row of planetRows) {
    const parts = row.fact_id.split('.')
    if (parts.length < 3) continue
    const planet = parts[1] ?? ''
    const attr = parts.slice(2).join('.')
    if (!planet || !attr) continue
    if (!byPlanet.has(planet)) byPlanet.set(planet, {})
    const val = row.value_text ?? (row.value_number != null ? String(row.value_number) : '')
    const planetAttrs = byPlanet.get(planet)
    if (planetAttrs) planetAttrs[attr] = val
  }

  if (byPlanet.size === 0) {
    lines.push(
      '',
      '[DATA_NOT_IN_DB — no recognisable PLN.<planet>.<attr> rows found in DB result.' +
        ' Call query_chart_facts(category:"planet") for live data.]'
    )
    lines.push('')
    return lines
  }

  lines.push('| Planet | Attributes (from chart_facts) |')
  lines.push('|---|---|')
  for (const [planet, attrs] of byPlanet) {
    const attrStr = Object.entries(attrs)
      .map(([k, v]) => `${k}=${v}`)
      .join('; ')
    lines.push(`| ${planet} | ${attrStr} |`)
  }
  lines.push('')
  lines.push(
    '*Note: Full positional detail (house, sign, degree, nakshatra, retrograde) is available via' +
      ' `query_chart_facts(category:"planet", divisional_chart:"D1")` once all position rows are seeded.*'
  )
  lines.push('')
  return lines
}

/**
 * Render Karakas section from DB rows with category 'karaka' or fact_ids
 * matching PLN.<PLANET>.CHARA_KARAKA. If absent: explicit placeholder.
 */
function renderKarakas(facts: ChartFactRow[]): string[] {
  const lines: string[] = ['## Karakas (Jaimini, D1)', '*Source: chart_facts table — category:karaka or CHARA_KARAKA attribute rows*']
  const karakaRows = facts.filter(
    (f) =>
      f.category === 'karaka' ||
      f.fact_id.endsWith('.CHARA_KARAKA') ||
      f.fact_id.includes('KARAKA')
  )

  if (karakaRows.length === 0) {
    lines.push(
      '',
      '[DATA_NOT_IN_DB — karaka assignment rows not yet seeded into chart_facts.' +
        ' Call query_chart_facts(category:"karaka") or query_chart_facts(category:"planet",' +
        ' value_contains:"karaka") for live data.]'
    )
    lines.push('')
    return lines
  }

  for (const row of karakaRows) {
    const val = row.value_text ?? '?'
    lines.push(`- ${row.fact_id}: ${val}`)
  }
  lines.push('')
  return lines
}

// ── Snapshot generator ─────────────────────────────────────────────────────────

async function generateChartSnapshot(chartId: string, userUid: string): Promise<string> {
  const now = new Date().toISOString()
  const today = now.slice(0, 10)

  // Fetch in parallel — planet category covers positions + karaka attributes
  const [planetFacts, karakaFacts, dashaPeriods, panchanga] = await Promise.all([
    fetchPrimitive('query_chart_facts', { chart_id: chartId, category: 'planet', divisional_chart: 'D1', limit: 100 }, userUid),
    fetchPrimitive('query_chart_facts', { chart_id: chartId, category: 'karaka', limit: 50 }, userUid),
    fetchPrimitive('query_dasha_periods', { chart_id: chartId, active_only: true }, userUid),
    fetchPrimitive('query_panchanga', { date: today }, userUid),
  ])

  // Merge all chart_facts rows (planet rows may contain CHARA_KARAKA attrs; karaka category holds dedicated rows)
  const allChartFacts: ChartFactRow[] = [
    ...extractFacts(planetFacts),
    ...extractFacts(karakaFacts),
  ]

  // Build markdown sections
  const lines: string[] = []
  lines.push(`# MARSYS-JIS Chart Snapshot (auto-generated, last refresh: ${now})`)
  lines.push('')
  lines.push('*All L1 values sourced live from chart_facts DB table. No values are hardcoded.*')
  // MC-003 (ŚODHANA T1): FORENSIC_ASTROLOGICAL_DATA_v8_0.md was deleted in PR #187
  // Legacy Teardown — it is not a live artifact any served response may cite as its
  // source. The live canonical source is the chart_facts DB table itself, built by the
  // L1 ga_* writers (see CLAUDE.md §B); a cold archived benchmark copy (informational
  // only, not authoritative) lives at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md.
  lines.push('*L1 provenance: chart_facts DB table (built by the L1 ga_* writers). ' +
    'The historical FORENSIC v8.0 markdown this table was originally seeded from was retired ' +
    'in PR #187 Legacy Teardown; a cold archived benchmark copy is retained at ' +
    '99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md for audit reference only — ' +
    'it is not the live source.*')
  lines.push('')

  // Lagna — from DB
  lines.push(...renderLagna(allChartFacts))

  // Planetary positions — from DB
  lines.push(...renderPlanetaryPositions(allChartFacts))

  // Karakas — from DB
  lines.push(...renderKarakas(allChartFacts))

  // Active dasha
  lines.push('## Active Dasha (Vimshottari)')
  if (dashaPeriods && typeof dashaPeriods === 'object') {
    const d = dashaPeriods as Record<string, unknown>
    const result = d['result']
    if (result && typeof result === 'object') {
      const r = result as Record<string, unknown>
      const periods = r['periods']
      if (Array.isArray(periods) && periods.length > 0) {
        const active = periods.slice(0, 3)
        const labels = ['Maha', 'Antar', 'Pratyantar']
        for (let i = 0; i < active.length; i++) {
          const p = active[i] as Record<string, unknown>
          lines.push(`- ${labels[i]}: ${p['lord'] ?? '?'}, ends ${p['end_date'] ?? '?'}`)
        }
      } else {
        lines.push('- (dasha data not yet backfilled — call query_dasha_periods for live data)')
      }
    }
  } else {
    lines.push('- (dasha data unavailable at attach time — call query_dasha_periods for live data)')
  }
  lines.push('')

  // Current panchang
  lines.push('## Current Panchang')
  if (panchanga && typeof panchanga === 'object') {
    const d = panchanga as Record<string, unknown>
    const result = d['result']
    if (result && typeof result === 'object') {
      const r = result as Record<string, unknown>
      lines.push(`- Date: ${today}`)
      lines.push(`- Tithi: ${r['tithi'] ?? '?'} | Vara: ${r['vara'] ?? '?'} | Nakshatra: ${r['moon_nakshatra'] ?? '?'}`)
      lines.push(`- Yoga: ${r['yoga'] ?? '?'} | Karana: ${r['karana'] ?? '?'}`)
    }
  } else {
    lines.push(`- Date: ${today}`)
    lines.push('- (panchang data unavailable — call query_panchanga for live data)')
  }
  lines.push('')

  // DB inventory summary
  const planetCount = extractFacts(planetFacts).length
  const karakaCount = extractFacts(karakaFacts).length
  lines.push(`*chart_facts DB: ${planetCount} planet-category rows + ${karakaCount} karaka-category rows loaded at attach time.*`)

  return lines.join('\n')
}

// ── Registration ───────────────────────────────────────────────────────────────

export function registerChartSnapshot(server: McpServer, principal: Principal): void {
  // M0: parametrize with {chart_id} so each user's session accesses their own chart.
  // The resource template URI includes the chart_id, and remoteAuthorize gates access.
  server.resource(
    'chart-snapshot',
    new ResourceTemplate('marsys://chart-snapshot/{chart_id}', { list: undefined }),
    async (uri, _variables) => {
      // Extract chart_id from the URI path (matches chart_bundle_resource.ts pattern)
      const chartId = (uri.pathname ?? '').replace(/^\//, '')
      if (!chartId) {
        return { contents: [{ uri: uri.href, mimeType: 'text/plain', text: 'Error: chart_id required in URI (marsys://chart-snapshot/{chart_id})' }] }
      }

      // M0 entitlement gate — authorize before fetching
      const authorized = await remoteAuthorize(principal, chartId)
      if (!authorized) {
        return { contents: [{ uri: uri.href, mimeType: 'text/plain', text: `Error: AUTHZ_DENIED for chart ${chartId}` }] }
      }

      const text = await generateChartSnapshot(chartId, principal.user_uid)
      return {
        contents: [
          {
            uri: uri.href,
            mimeType: 'text/markdown',
            text,
          },
        ],
      }
    }
  )
}
