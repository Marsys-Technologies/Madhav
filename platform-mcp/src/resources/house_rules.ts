/**
 * house_rules.ts — MCP resource: marsys://house-rules
 *
 * Loads the universal house rules from house_rules_variants/universal.md.
 *
 * D0.5 tier excision (2026-06-28): tier-conditioned variants (super_admin/acharya/client)
 * collapsed to a single universal variant per §N.4 no-audience-tier principle.
 * Prior: v3.1.0-S3 loaded 3 tier variants; Stream A 3.tier_excision 2026-05-28 had already
 * removed audience_tier from Principal. This completes the MCP resource layer excision.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { join, dirname } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const VARIANTS_DIR = join(__dirname, 'house_rules_variants')

// ── Load universal variant ─────────────────────────────────────────────────────

function loadUniversalRules(): string {
  try {
    return readFileSync(join(VARIANTS_DIR, 'universal.md'), 'utf-8')
  } catch {
    return `# MARSYS-JIS House Rules\n\n*House rules file unavailable. Default operating rules apply.*`
  }
}

const UNIVERSAL_RULES = loadUniversalRules()

// ── Registration ───────────────────────────────────────────────────────────────

export function registerHouseRules(server: McpServer): void {
  server.resource(
    'house-rules',
    new ResourceTemplate('marsys://house-rules', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://house-rules',
          mimeType: 'text/markdown',
          text: UNIVERSAL_RULES,
        },
      ],
    })
  )
}

/** Export for programmatic access — returns universal rules regardless of input */
export function getHouseRules(): string {
  return UNIVERSAL_RULES
}
