/**
 * sutravali_resource.ts — MCP Resources for Sūtravali rules corpus
 *
 * Registers 2 MCP resource templates:
 *   marsys://resource/sutravali/all-by-planet/{planet}
 *   marsys://resource/sutravali/all-by-house/{n}
 *
 * Both read from sutravali_rules via the canonical service-admitted capability RPC.
 * ZERO LLM — SQL-only; canonical timeout/cache policy, at most 500 rows.
 *
 * BRAHMA L0 Stream D — Sūtravali Pattern Extraction (2026-06-07)
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

import type { Principal } from '../types.js'
import { callRegistryCapability } from '../lib/registry_capability.js'

// Keep successful-empty distinct from transport, capability and malformed-result failures.
async function fetchRules(
  capabilityUri: string,
  args: Record<string, unknown>,
  principal: Principal,
): Promise<Record<string, unknown>[] | null> {
  try {
    const result = await callRegistryCapability(capabilityUri, args, undefined, principal) as
      { is_error?: boolean; content?: { rules?: unknown } } | null
    const rules = result?.content?.rules
    if (result?.is_error !== false || !Array.isArray(rules) ||
        !rules.every(rule => rule !== null && typeof rule === 'object' && !Array.isArray(rule))) {
      return null
    }
    return rules as Record<string, unknown>[]
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

export function registerSutravaliResources(server: McpServer, principal: Principal): void {
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
      const rules = await fetchRules(
        'marsys://tool/L0/query_sutravali_rules_for_planet',
        { planet: p ?? '', limit: 500 },
        principal,
      )

      const content = rules
        ? rulesToMarkdown(`Planet: ${p}`, rules)
        : `# Sūtravali Rules — Planet: ${p}\n\nNo data available (capability query unavailable).`

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
      // Match the legacy house proxy's parseInt spelling and 1..12 guard.
      const house = parseInt(houseNum ?? '', 10)
      const rules = Number.isFinite(house) && house >= 1 && house <= 12
        ? await fetchRules('marsys://tool/L0/query_sutravali_rules', { house, limit: 500 }, principal)
        : null

      const content = rules
        ? rulesToMarkdown(`House: ${houseNum}`, rules)
        : `# Sūtravali Rules — House: ${houseNum}\n\nNo data available (capability query unavailable).`

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
