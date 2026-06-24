/**
 * sutravali_resource.ts — MCP Resources for Sūtravali rules corpus
 *
 * Registers 2 MCP resource templates:
 *   marsys://resource/sutravali/all-by-planet/{planet}
 *   marsys://resource/sutravali/all-by-house/{n}
 *
 * Both read from sutravali_rules via Python sidecar SQL endpoints.
 * ZERO LLM — SQL-only via /api/brahma/sutravali/by_planet and /by_house.
 *
 * BRAHMA L0 Stream D — Sūtravali Pattern Extraction (2026-06-07)
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Helper ─────────────────────────────────────────────────────────────────────

async function fetchSidecarJson(path: string): Promise<unknown[] | null> {
  try {
    const resp = await fetch(`${PLATFORM_URL}${path}`, {
      headers: { 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
      signal: AbortSignal.timeout(8000),
    })
    if (!resp.ok) return null
    return (await resp.json()) as unknown[]
  } catch {
    return null
  }
}

// ── Resource: all-by-planet ────────────────────────────────────────────────────

function rulesToMarkdown(
  groupLabel: string,
  rules: Record<string, unknown>[],
): string {
  if (!rules.length) {
    return `# Sūtravali Rules — ${groupLabel}\n\nNo rules found for this query.`
  }

  const lines: string[] = [
    `# Sūtravali Rules — ${groupLabel}`,
    `**Count:** ${rules.length}`,
    '',
  ]

  for (const r of rules) {
    const ant = r.antecedent as Record<string, unknown> | null
    const pred = r.predicate as Record<string, unknown> | null
    const pred_ = r.prediction as Record<string, unknown> | null
    const textRef = `${r.text_id ?? ''}${r.verse_ref ? ' ' + r.verse_ref : ''}`
    lines.push(`## ${textRef || String(r.rule_id).slice(0, 8)}`)
    if (ant) lines.push(`**Antecedent:** ${JSON.stringify(ant)}`)
    if (pred) lines.push(`**Predicate:** ${JSON.stringify(pred)}`)
    if (pred_) lines.push(`**Prediction:** ${JSON.stringify(pred_)}`)
    if (r.confidence != null) lines.push(`**Confidence:** ${r.confidence}`)
    lines.push('')
  }

  return lines.join('\n')
}

export function registerSutravaliResources(server: McpServer): void {
  // Resource 1: all rules by planet
  const planetTemplate = new ResourceTemplate(
    'marsys://resource/sutravali/all-by-planet/{planet}',
    { list: undefined },
  )

  server.resource(
    'sutravali-by-planet',
    planetTemplate,
    async (uri, { planet }) => {
      const p = Array.isArray(planet) ? planet[0] : planet
      const rules = await fetchSidecarJson(
        `/api/brahma/sutravali/by_planet/${encodeURIComponent(p ?? '')}`,
      )

      const content = rules
        ? rulesToMarkdown(`Planet: ${p}`, rules as Record<string, unknown>[])
        : `# Sūtravali Rules — Planet: ${p}\n\nNo data available (sidecar unreachable or no rules found).`

      return {
        contents: [{
          uri: uri.href,
          mimeType: 'text/markdown',
          text: content,
        }],
      }
    },
  )

  // Resource 2: all rules by house number
  const houseTemplate = new ResourceTemplate(
    'marsys://resource/sutravali/all-by-house/{n}',
    { list: undefined },
  )

  server.resource(
    'sutravali-by-house',
    houseTemplate,
    async (uri, { n }) => {
      const houseNum = Array.isArray(n) ? n[0] : n
      const rules = await fetchSidecarJson(
        `/api/brahma/sutravali/by_house/${encodeURIComponent(houseNum ?? '')}`,
      )

      const content = rules
        ? rulesToMarkdown(`House: ${houseNum}`, rules as Record<string, unknown>[])
        : `# Sūtravali Rules — House: ${houseNum}\n\nNo data available (sidecar unreachable or no rules found).`

      return {
        contents: [{
          uri: uri.href,
          mimeType: 'text/markdown',
          text: content,
        }],
      }
    },
  )
}
