/**
 * INF11-S1: chart_bundle_resource.ts
 * MCP Resource: marsys://chart-bundle/{chart_id}
 *
 * Exposes the Layer-1 chart bundle (planet positions, house cusps, current dasha,
 * active yogas, birth panchanga) for a given chart as an auto-loaded MCP Resource.
 *
 * Calls /api/charts/{chart_id}/bundle (new endpoint) via the platform internal API.
 * Falls back to a minimal static structure on any error.
 *
 * [BUILD-ORCH-J-03] INF11-S1
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Bundle fetcher ─────────────────────────────────────────────────────────────

interface BundleResponse {
  chart_id: string
  ayanamshas_requested: string[]
  ayanamshas_found: string[]
  birth_panchanga: Record<string, unknown>
  active_yogas: Array<{ yoga_name: string; strength: number | null }>
  ayanamsha_slices: Array<{
    ayanamsha_id: string
    planets: Array<{ planet: string; sign: string | null; house: number | null; nakshatra: string | null }>
    houses: Array<{ house: number; sign: string | null }>
    dasha_chain: Array<{ level: string; lord: string; start_date: string | null; end_date: string | null }>
  }>
  cross_ayanamsha: Array<{ ayanamsha_1: string; ayanamsha_2: string; divergence_score: number | null }>
  token_estimate: number
}

async function fetchBundle(chartId: string): Promise<BundleResponse | null> {
  try {
    const resp = await fetch(`${PLATFORM_URL}/api/charts/${encodeURIComponent(chartId)}/bundle`, {
      headers: { 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
      signal: AbortSignal.timeout(8000),
    })
    if (!resp.ok) return null
    return (await resp.json()) as BundleResponse
  } catch {
    return null
  }
}

function bundleToMarkdown(bundle: BundleResponse): string {
  const lines: string[] = []

  lines.push(`# Chart Bundle — ${bundle.chart_id}`)
  lines.push(`Ayanamshas: ${bundle.ayanamshas_found.join(', ') || 'none loaded'}`)
  lines.push('')

  // Panchanga
  const p = bundle.birth_panchanga
  if (Object.keys(p).length > 0) {
    lines.push('## Birth Panchanga')
    if (p['tithi']) lines.push(`- Tithi: ${p['tithi']}`)
    if (p['vara']) lines.push(`- Vara: ${p['vara']}`)
    if (p['moon_nakshatra']) lines.push(`- Moon Nakshatra: ${p['moon_nakshatra']}`)
    if (p['yoga']) lines.push(`- Yoga: ${p['yoga']}`)
    if (p['karana']) lines.push(`- Karana: ${p['karana']}`)
    lines.push('')
  }

  // Planets (first ayanamsha slice)
  const slice = bundle.ayanamsha_slices[0]
  if (slice?.planets && slice.planets.length > 0) {
    lines.push(`## Planetary Positions (${slice.ayanamsha_id})`)
    for (const p of slice.planets.slice(0, 9)) {
      lines.push(`- ${p.planet}: ${p.sign ?? '?'}, H${p.house ?? '?'}, ${p.nakshatra ?? '?'}`)
    }
    lines.push('')
  }

  // House cusps
  if (slice?.houses && slice.houses.length > 0) {
    lines.push(`## House Cusps (${slice.ayanamsha_id})`)
    for (const h of slice.houses.slice(0, 12)) {
      lines.push(`- H${h.house}: ${h.sign ?? '?'}`)
    }
    lines.push('')
  }

  // Current dasha
  if (slice?.dasha_chain && slice.dasha_chain.length > 0) {
    lines.push('## Current Dasha Chain')
    for (const d of slice.dasha_chain.slice(0, 3)) {
      lines.push(`- ${d.level}: ${d.lord} (${d.start_date ?? '?'} → ${d.end_date ?? '?'})`)
    }
    lines.push('')
  }

  // Active yogas
  if (bundle.active_yogas.length > 0) {
    lines.push('## Active Yogas (top 10)')
    for (const y of bundle.active_yogas.slice(0, 10)) {
      const str = y.strength != null ? ` (strength: ${y.strength.toFixed(2)})` : ''
      lines.push(`- ${y.yoga_name}${str}`)
    }
    lines.push('')
  }

  // Cross-ayanamsha
  if (bundle.cross_ayanamsha.length > 0) {
    lines.push('## Cross-Ayanamsha Summary')
    for (const c of bundle.cross_ayanamsha.slice(0, 5)) {
      const score = c.divergence_score != null ? c.divergence_score.toFixed(3) : 'n/a'
      lines.push(`- ${c.ayanamsha_1} vs ${c.ayanamsha_2}: divergence_score=${score}`)
    }
    lines.push('')
  }

  return lines.join('\n')
}

// ── Registration ───────────────────────────────────────────────────────────────

export function registerChartBundleResource(server: McpServer): void {
  // Static resource listing (no dynamic per-chart listing — too many charts)
  server.resource(
    'chart-bundle',
    new ResourceTemplate('marsys://chart-bundle/{chart_id}', { list: undefined }),
    async (uri, _variables) => {
      const chartId = (uri.pathname ?? '').replace(/^\//, '')
      const bundle = await fetchBundle(chartId)

      const text = bundle
        ? bundleToMarkdown(bundle)
        : `# Chart Bundle — ${chartId}\n\n*Bundle data not yet loaded. Trigger a build for this chart first.*`

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
