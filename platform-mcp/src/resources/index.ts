/**
 * resources/index.ts — MCP resource registration for MARSYS-JIS.
 *
 * Registers two MCP resources that Claude reads once at session attach:
 *   - marsys://chart-overview  (~1300 words, L1-grounded chart summary)
 *   - marsys://house-rules     (~1000 words, acharya-grade operating manual)
 *
 * Together these replace 5-10 tool calls of orientation per session
 * (MCP_BRIEF §4.5). Resources are served as text/markdown. The files
 * are loaded synchronously at registration time; the MCP server restarts
 * on Cloud Run update, so stale content is not a runtime risk.
 *
 * Authored: MCP-2-S2 (2026-05-21)
 */

import { McpServer, ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { join, dirname } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))

// Resolve the resources/ directory relative to this source file.
// In the compiled output (dist/), __dirname is platform-mcp/dist/resources/
// and the markdown files live at platform-mcp/resources/ — two levels up from
// dist/resources/. Adjust if the tsconfig outDir changes.
const RESOURCES_DIR = join(__dirname, '..', '..', 'resources')

/**
 * Load a markdown resource file synchronously.
 * Throws clearly if the file is missing — fail-fast is preferable to serving
 * empty or stale content.
 */
function loadMarkdown(filename: string): string {
  const fullPath = join(RESOURCES_DIR, filename)
  return readFileSync(fullPath, 'utf-8')
}

/**
 * Register both MARSYS-JIS MCP resources on the given server.
 *
 * Call this once per McpServer instance, alongside the tool registrations,
 * before connecting the transport.
 *
 * @param server  The McpServer instance to register resources on.
 */
export function registerResources(server: McpServer): void {
  const chartOverview = loadMarkdown('chart-overview.md')
  const houseRules = loadMarkdown('house-rules.md')

  // ── Resource 1: marsys://chart-overview ──────────────────────────────────
  // Compact, L1-grounded summary of Abhisek's natal chart. Contains:
  // birth data, lagna + key placements, planets-by-house grid, active dasha
  // state, top 5 forward-looking L2.5 themes, one-paragraph synthesis.
  // Regenerate when FORENSIC_ASTROLOGICAL_DATA bumps to a new version.

  server.resource(
    'chart-overview',
    new ResourceTemplate('marsys://chart-overview', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://chart-overview',
          mimeType: 'text/markdown',
          text: chartOverview,
        },
      ],
    })
  )

  // ── Resource 2: marsys://house-rules ─────────────────────────────────────
  // Operating manual for acharya-grade interpretation in this corpus. Contains:
  // school commitments (Parashara primary, Jaimini/KP/Tajaka secondary),
  // terminology conventions + citation protocol, quality bars, disclosure tier,
  // tool-deferral guidance, escalation rules.
  // Update as the discipline evolves.

  server.resource(
    'house-rules',
    new ResourceTemplate('marsys://house-rules', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://house-rules',
          mimeType: 'text/markdown',
          text: houseRules,
        },
      ],
    })
  )
}
