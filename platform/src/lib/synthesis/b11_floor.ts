/**
 * INF7-S2: B.11 Inline Floor Check
 *
 * Enforces the Whole-Chart-Read discipline (principle B.11) inline in the
 * agentic loop. Before synthesis, verifies that the minimum set of chart_facts
 * categories was consulted. If not, returns a list of mandatory tool calls to
 * inject into the next iteration.
 *
 * Minimum required categories (configurable):
 *   - planet_positions (or 'planet' legacy)
 *   - house_positions  (or 'house' legacy)
 *   - current_dasha    (dasha_vimshottari or dasha_chara)
 *   - active_yogas     (yoga)
 *
 * [BUILD-ORCH-J-10] INF7-S2
 */

import type { LoopToolResult } from './agentic_loop'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface MandatoryToolCall {
  tool_name: string
  params: Record<string, unknown>
  reason: string
}

export interface B11FloorResult {
  /** Whether all minimum categories have been consulted. */
  satisfied: boolean
  /** Tool calls to inject if not satisfied. */
  mandatory_calls: MandatoryToolCall[]
  /** Which categories are missing. */
  missing_categories: string[]
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** Canonical category families to satisfy B.11 */
const REQUIRED_FAMILIES: Array<{
  name: string
  patterns: string[]
  tool_name: string
  params: Record<string, unknown>
}> = [
  {
    name: 'planet_positions',
    patterns: ['planet_positions', 'chart_facts_query', 'query_chart_facts'],
    tool_name: 'query_chart_facts',
    params: { categories: ['planet', 'planet_positions'], limit: 15 },
  },
  {
    name: 'house_positions',
    patterns: ['house_positions', 'house'],
    tool_name: 'query_chart_facts',
    params: { categories: ['house', 'house_positions'], limit: 12 },
  },
  {
    name: 'current_dasha',
    patterns: ['dasha', 'dasha_vimshottari', 'dasha_chara', 'query_dasha'],
    tool_name: 'query_dasha_periods',
    params: { as_of: 'today', systems: ['vimshottari'] },
  },
  {
    name: 'active_yogas',
    patterns: ['yoga', 'query_yogas'],
    tool_name: 'query_yogas_active_now',
    params: { limit: 20 },
  },
]

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Check whether B.11 minimum categories have been covered by the tool calls
 * so far. Returns mandatory calls to inject if not.
 */
export function checkB11Floor(
  toolResults: LoopToolResult[],
  chartId?: string,
): B11FloorResult {
  const calledTools = toolResults.map((r) => r.name.toLowerCase())
  const calledOutputs = toolResults
    .filter((r) => !r.isError)
    .map((r) => r.output.toLowerCase().slice(0, 500))

  const missing_categories: string[] = []
  const mandatory_calls: MandatoryToolCall[] = []

  for (const family of REQUIRED_FAMILIES) {
    const covered = family.patterns.some(
      (pat) =>
        calledTools.some((t) => t.includes(pat)) ||
        calledOutputs.some((o) => o.includes(pat)),
    )

    if (!covered) {
      missing_categories.push(family.name)
      mandatory_calls.push({
        tool_name: family.tool_name,
        params: chartId
          ? { ...family.params, chart_id: chartId }
          : { ...family.params },
        reason: `B.11 floor: ${family.name} not yet consulted`,
      })
    }
  }

  return {
    satisfied: missing_categories.length === 0,
    mandatory_calls,
    missing_categories,
  }
}

/**
 * Format mandatory calls as a prompt injection string for the model.
 * This string is appended to the user turn before the model synthesizes.
 */
export function formatB11Injection(result: B11FloorResult): string {
  if (result.satisfied) return ''
  const lines = [
    '[B.11 FLOOR] The following chart data must be retrieved before synthesis:',
    ...result.missing_categories.map((c) => `  - ${c}`),
    'Please call the mandatory tools listed above before responding.',
  ]
  return lines.join('\n')
}
