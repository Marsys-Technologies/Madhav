/**
 * chart_snapshot.ts — MCP resource: marsys://chart-snapshot
 *
 * NEW in v3.1 (MCPT v3.1.0-S3). Structured L1 facts generated at session attach.
 * ~2.5k tokens. Pure facts — no prose synthesis.
 *
 * Reads from: chart_facts table + query_dasha_periods(active_only:true) +
 *   query_panchanga(today) + query_transit_event(now)
 *
 * Tier conditioning: all tiers receive the same content; client tier gets inline
 * Sanskrit glosses (planet names etc.) in parentheses.
 *
 * MCPT v3.1.0-S3
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Fetch helpers ──────────────────────────────────────────────────────────────

async function fetchPrimitive(toolName: string, params: Record<string, unknown>): Promise<unknown> {
  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${toolName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': 'system',
        'X-MCP-Audience-Tier': 'super_admin',
        'X-MCP-Key-Id': 'resource-loader',
      },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(10_000),
    })
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

// ── Snapshot generator ─────────────────────────────────────────────────────────

async function generateChartSnapshot(): Promise<string> {
  const now = new Date().toISOString()
  const today = now.slice(0, 10)

  // Fetch in parallel
  const [chartFacts, dashaPeriods, panchanga] = await Promise.all([
    fetchPrimitive('query_chart_facts', { category: 'house', limit: 100 }),
    fetchPrimitive('query_dasha_periods', { active_only: true }),
    fetchPrimitive('query_panchanga', { date: today }),
  ])

  // Build markdown sections
  const lines: string[] = []
  lines.push(`# MARSYS-JIS Chart Snapshot (auto-generated, last refresh: ${now})`)
  lines.push('')
  lines.push('*Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md (L1). No synthesis. Pure facts.*')
  lines.push('')

  // Lagna
  lines.push('## Lagna')
  lines.push('- Sign: Aries (Mesha) | Degree: 12°23′55″ | Lord: Mars | State: Neutral | Nakshatra: Ashwini | Nak-Lord: Ketu')
  lines.push('')

  // Planetary positions (D1) — sourced from FORENSIC v8.0
  lines.push('## Planetary Positions (D1)')
  lines.push('| Planet | House | Sign | Degree | Dignity | Nakshatra | Nak-Lord | Retro? |')
  lines.push('|---|---|---|---|---|---|---|---|')
  lines.push('| Sun | 10 | Capricorn | 21°57′35″ | Enemy Sign | Shravana | Moon | — |')
  lines.push('| Moon | 11 | Aquarius | 27°02′48″ | Neutral | Purva Bhadrapada | Jupiter | — |')
  lines.push('| Mars | 7 | Libra | 18°31′38″ | Enemy Sign | Swati | Rahu | — |')
  lines.push('| Mercury | 10 | Capricorn | 00°50′11″ | Neutral | Uttara Ashadha | Sun | — |')
  lines.push('| Jupiter | 9 | Sagittarius | 09°48′28″ | Own Sign | Moola | Ketu | — |')
  lines.push('| Venus | 9 | Sagittarius | 19°10′12″ | Neutral | Purva Ashadha | Venus | — |')
  lines.push('| Saturn | 7 | Libra | 22°27′04″ | Exalted | Vishakha | Jupiter | — |')
  lines.push('| Rahu | 2 | Taurus | 19°01′47″ | Neutral | Rohini | Moon | Yes |')
  lines.push('| Ketu | 8 | Scorpio | 19°01′47″ | Neutral | Jyeshtha | Mercury | Yes |')
  lines.push('')

  // Karakas (Jaimini)
  lines.push('## Karakas (Jaimini, D1 — 7-karaka system)')
  lines.push('- Atmakaraka (AK): Moon (27°02′48″ — highest degree)')
  lines.push('- Amatyakaraka (AmK): Saturn (22°27′04″)')
  lines.push('- Bhatrikaraka (BK): Sun (21°57′35″)')
  lines.push('- Matrikaraka (MK): Venus (19°10′12″)')
  lines.push('- Pitrikaraka (PiK): Mars (18°31′38″)')
  lines.push('- Putrakaraka (PK): Jupiter (09°48′28″)')
  lines.push('- Gnatikaraka (GK): Mercury (00°50′11″)')
  lines.push('')

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

  // Used chart_facts data if available
  if (chartFacts && typeof chartFacts === 'object') {
    const d = chartFacts as Record<string, unknown>
    const result = d['result']
    if (result && typeof result === 'object') {
      const r = result as Record<string, unknown>
      if (typeof r['count'] === 'number') {
        lines.push(`*chart_facts table: ${r['count']} house-category rows loaded.*`)
      }
    }
  }

  return lines.join('\n')
}

// ── Registration ───────────────────────────────────────────────────────────────

export function registerChartSnapshot(server: McpServer): void {
  server.resource(
    'chart-snapshot',
    new ResourceTemplate('marsys://chart-snapshot', { list: undefined }),
    async (_uri) => {
      const text = await generateChartSnapshot()
      return {
        contents: [
          {
            uri: 'marsys://chart-snapshot',
            mimeType: 'text/markdown',
            text,
          },
        ],
      }
    }
  )
}
