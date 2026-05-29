/**
 * INF11-S1: multi_ayanamsha_resource.ts
 * MCP Resource: marsys://multi-ayanamsha/{chart_id}
 *
 * Exposes cross-ayanamsha consensus and divergence summary for a given chart
 * as an auto-loaded MCP Resource. Useful for timing queries where ayanamsha
 * selection matters (Rahu transit, sign boundaries, etc.).
 *
 * Calls /api/charts/{chart_id}/ayanamsha-status via platform internal API.
 *
 * [BUILD-ORCH-J-03] INF11-S1
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Types ──────────────────────────────────────────────────────────────────────

interface AyanamshaStatusEntry {
  ayanamsha_id: string
  latest_build_id: string | null
  status: string | null
  finished_at: string | null
  engine_version: string | null
  is_latest_engine: boolean
  steps_complete: number
  steps_total: number
}

// ── Fetcher ─────────────────────────────────────────────────────────────────────

async function fetchAyanamshaStatus(chartId: string): Promise<AyanamshaStatusEntry[] | null> {
  try {
    const resp = await fetch(
      `${PLATFORM_URL}/api/charts/${encodeURIComponent(chartId)}/ayanamsha-status`,
      {
        headers: { 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
        signal: AbortSignal.timeout(6000),
      },
    )
    if (!resp.ok) return null
    const data = await resp.json() as { ayanamsha_status: AyanamshaStatusEntry[] }
    return data.ayanamsha_status ?? null
  } catch {
    return null
  }
}

function statusToMarkdown(chartId: string, entries: AyanamshaStatusEntry[]): string {
  const lines: string[] = []
  lines.push(`# Multi-Ayanamsha Status — ${chartId}`)
  lines.push('')
  lines.push('## Build Status per Ayanamsha')
  lines.push('')
  lines.push('| Ayanamsha | Status | Completed | Engine Current | Progress |')
  lines.push('|-----------|--------|-----------|----------------|----------|')

  for (const e of entries) {
    const status = e.status ?? 'not_built'
    const completed = e.finished_at ? e.finished_at.split('T')[0] : '—'
    const current = e.is_latest_engine ? '✓' : '—'
    const progress = e.steps_total > 0
      ? `${e.steps_complete}/${e.steps_total}`
      : '—'
    lines.push(`| ${e.ayanamsha_id} | ${status} | ${completed} | ${current} | ${progress} |`)
  }

  lines.push('')
  lines.push('## Guidance for Cross-Ayanamsha Queries')
  lines.push('')

  const built = entries.filter((e) => e.status === 'complete')
  const notBuilt = entries.filter((e) => e.status !== 'complete')

  if (built.length === 5) {
    lines.push('All 5 ayanamshas are built. Use `cross_ayanamsha_consensus` to identify')
    lines.push('which chart facts are stable across systems vs. ayanamsha-sensitive.')
  } else if (built.length > 0) {
    lines.push(`${built.length}/5 ayanamshas built (${built.map((e) => e.ayanamsha_id).join(', ')}).`)
    if (notBuilt.length > 0) {
      lines.push(`Not yet built: ${notBuilt.map((e) => e.ayanamsha_id).join(', ')}.`)
    }
    lines.push('Cross-ayanamsha consensus is partially available for built ayanamshas.')
  } else {
    lines.push('No ayanamshas built yet. Trigger a build via /clients/{chart_id}/build to populate data.')
  }

  return lines.join('\n')
}

// ── Registration ───────────────────────────────────────────────────────────────

export function registerMultiAyanamshaResource(server: McpServer): void {
  server.resource(
    'multi-ayanamsha',
    new ResourceTemplate('marsys://multi-ayanamsha/{chart_id}', { list: undefined }),
    async (uri, _variables) => {
      const chartId = (uri.pathname ?? '').replace(/^\//, '')
      const entries = await fetchAyanamshaStatus(chartId)

      const text = entries && entries.length > 0
        ? statusToMarkdown(chartId, entries)
        : `# Multi-Ayanamsha Status — ${chartId}\n\n*No ayanamsha build data available. Trigger a build first.*`

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
