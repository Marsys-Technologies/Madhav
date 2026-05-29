/**
 * RIR-S6 + RIR-S7: Tool Registration Template + Description Generator
 *
 * Provides:
 * 1. ToolRegistrationSpec — the data structure every retrieval tool must export
 * 2. generateToolDescription() — produces a structured, LLM-facing description
 *    from the spec so LLMs understand when/how to use each tool
 * 3. registerTool() — convenience registration wrapper for MCP server
 *
 * [BUILD-ORCH-RIR-S6, RIR-S7]
 */

import type { AudienceTier, Channel } from './retrieval_envelope'

// ── Tool Spec (RIR-S6) ────────────────────────────────────────────────────────

export interface ToolParamSpec {
  name: string
  type: 'string' | 'number' | 'boolean' | 'string[]' | 'number[]' | 'object'
  required: boolean
  description: string
  example?: string
  default?: unknown
  enum?: string[]
}

export interface ToolRegistrationSpec {
  /** Tool name — must match CAPABILITY_MANIFEST.json tool_name */
  tool_name: string
  /** CAPABILITY_MANIFEST.json asset id */
  asset_id: string
  /** Brief (1-2 sentence) description for tool catalogue */
  brief_description: string
  /**
   * Detailed description including WHEN to use this tool.
   * LLM-facing — include trigger phrases, example questions, DO/DON'T.
   */
  llm_description: string
  /** Input parameters */
  params: ToolParamSpec[]
  /** Which channels this tool is available in */
  channels: Channel[]
  /** Minimum audience tier required to use this tool */
  min_tier: AudienceTier
  /** Whether this tool requires a chart_id */
  requires_chart_id: boolean
  /** Whether this tool is ayanamsha-sensitive (different results per ayanamsha) */
  ayanamsha_sensitive: boolean
  /** Example tool call for few-shot prompting */
  few_shot_example?: {
    query: string
    call: Record<string, unknown>
    expected_output_summary: string
  }
}

// ── Description Generator (RIR-S7) ────────────────────────────────────────────

/**
 * Generate a structured, LLM-facing description from a ToolRegistrationSpec.
 *
 * Output format:
 * ```
 * {tool_name}: {brief_description}
 *
 * USE WHEN: {trigger conditions}
 * ...
 * ```
 */
export function generateToolDescription(spec: ToolRegistrationSpec): string {
  const lines: string[] = []

  lines.push(`**${spec.tool_name}**: ${spec.brief_description}`)
  lines.push('')
  lines.push(spec.llm_description)
  lines.push('')

  // Parameters
  if (spec.params.length > 0) {
    lines.push('**Parameters:**')
    for (const p of spec.params) {
      const req = p.required ? '(required)' : '(optional)'
      const defStr = p.default !== undefined ? ` [default: ${JSON.stringify(p.default)}]` : ''
      const enumStr = p.enum ? ` [one of: ${p.enum.join(' | ')}]` : ''
      lines.push(`- \`${p.name}\` ${req}: ${p.description}${defStr}${enumStr}`)
      if (p.example) lines.push(`  Example: ${p.example}`)
    }
    lines.push('')
  }

  // Routing hints
  const hints: string[] = []
  if (spec.requires_chart_id) hints.push('Requires chart_id')
  if (spec.ayanamsha_sensitive) hints.push('Results vary by ayanamsha_id — always pass the active ayanamsha')
  if (spec.min_tier !== 'public_redacted') hints.push(`Minimum tier: ${spec.min_tier}`)
  if (hints.length > 0) {
    lines.push('**Notes:** ' + hints.join('. ') + '.')
    lines.push('')
  }

  // Few-shot example
  if (spec.few_shot_example) {
    const ex = spec.few_shot_example
    lines.push('**Example:**')
    lines.push(`Query: "${ex.query}"`)
    lines.push(`Call: \`${spec.tool_name}(${JSON.stringify(ex.call)})\``)
    lines.push(`Returns: ${ex.expected_output_summary}`)
  }

  return lines.join('\n').trim()
}

/**
 * Format tool name + description for inclusion in the MCP server.ts tool list.
 * Returns the description string to pass to `server.tool(name, description, ...)`.
 */
export function toolDescription(spec: ToolRegistrationSpec): string {
  return generateToolDescription(spec)
}

// ── Catalogue entry for CAPABILITY_MANIFEST auto-sync (RIR-S8) ─────────────

export interface ManifestToolEntry {
  tool_name: string
  asset_id: string
  channels: Channel[]
  min_tier: AudienceTier
  requires_chart_id: boolean
  ayanamsha_sensitive: boolean
  description_hash: string
}

/** Generate a CAPABILITY_MANIFEST entry from a ToolRegistrationSpec. */
export function specToManifestEntry(spec: ToolRegistrationSpec): ManifestToolEntry {
  // Simple hash of description for change detection
  const descText = spec.brief_description + spec.llm_description
  let hash = 0
  for (let i = 0; i < descText.length; i++) {
    hash = ((hash << 5) - hash + descText.charCodeAt(i)) | 0
  }
  const description_hash = Math.abs(hash).toString(16).padStart(8, '0')

  return {
    tool_name: spec.tool_name,
    asset_id: spec.asset_id,
    channels: spec.channels,
    min_tier: spec.min_tier,
    requires_chart_id: spec.requires_chart_id,
    ayanamsha_sensitive: spec.ayanamsha_sensitive,
    description_hash,
  }
}
