/**
 * house_rules.ts — MCP resource: marsys://house-rules (rewrite for v3.1)
 *
 * Loads tier-conditioned house rules from variant markdown files:
 *   house_rules_variants/super_admin.md
 *   house_rules_variants/acharya.md
 *   house_rules_variants/client.md
 *
 * MCPT v3.1.0-S3; public_redacted variant retired (Stream A 3.tier_excision 2026-05-28).
 * Audience-tier system excised; resource resolves to super_admin variant by default.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { join, dirname } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const VARIANTS_DIR = join(__dirname, 'house_rules_variants')

// ── Load variant files ─────────────────────────────────────────────────────────

function loadVariant(tier: string): string {
  const validTiers = ['super_admin', 'acharya', 'client']
  const safeTier = validTiers.includes(tier) ? tier : 'super_admin'
  try {
    return readFileSync(join(VARIANTS_DIR, `${safeTier}.md`), 'utf-8')
  } catch {
    // Fallback: try super_admin
    try {
      return readFileSync(join(VARIANTS_DIR, 'super_admin.md'), 'utf-8')
    } catch {
      return `# MARSYS-JIS House Rules\n\n*Variant file unavailable. Default operating rules apply.*`
    }
  }
}

// Pre-load all variants at server start
const VARIANTS: Record<string, string> = {
  super_admin: loadVariant('super_admin'),
  acharya: loadVariant('acharya'),
  client: loadVariant('client'),
  // public_redacted retired (Stream A 3.tier_excision 2026-05-28).
}

// ── Registration ───────────────────────────────────────────────────────────────

export function registerHouseRules(server: McpServer): void {
  // Default resource (super_admin content — most principals are acharya+)
  server.resource(
    'house-rules',
    new ResourceTemplate('marsys://house-rules', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://house-rules',
          mimeType: 'text/markdown',
          text: VARIANTS['super_admin'] ?? '',
        },
      ],
    })
  )
}

/** Export for programmatic tier-specific access */
export function getHouseRulesForTier(tier: string): string {
  return VARIANTS[tier] ?? VARIANTS['super_admin'] ?? ''
}
