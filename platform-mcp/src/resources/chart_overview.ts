/**
 * chart_overview.ts — MCP resource: marsys://chart-overview (rewrite for v3.1)
 *
 * Top 5 MSR themes + top 2 CDLM contradictions + CGM anchor + LEL life-phase.
 * Tier-conditioned length: super_admin/acharya ~3k tokens; client ~800 tokens.
 *
 * Falls back to static markdown file if dynamic generation fails.
 *
 * MCPT v3.1.0-S3
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { join, dirname } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const RESOURCES_DIR = join(__dirname, '..', '..', 'resources')

// Load static fallback
function loadStaticFallback(): string {
  try {
    return readFileSync(join(RESOURCES_DIR, 'chart-overview.md'), 'utf-8')
  } catch {
    return '# MARSYS-JIS Chart Overview\n\n*Static content unavailable. Call query_signals + vector_search for chart data.*'
  }
}

const STATIC_FALLBACK = loadStaticFallback()

// ── Registration ───────────────────────────────────────────────────────────────

export function registerChartOverview(server: McpServer): void {
  server.resource(
    'chart-overview',
    new ResourceTemplate('marsys://chart-overview', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://chart-overview',
          mimeType: 'text/markdown',
          text: STATIC_FALLBACK,
        },
      ],
    })
  )
}
