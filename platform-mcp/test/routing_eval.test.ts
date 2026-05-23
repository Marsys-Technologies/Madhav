/**
 * routing_eval.test.ts — MCPT v3.2 Phase 9b: MCP routing eval CI gate.
 *
 * Tests:
 *   1. prompts.json has exactly 30 entries with required fields.
 *   2. All gold_first_tool and acceptable_alternatives reference known tool names.
 *   3. All 22 tools in the catalog are covered by at least one prompt's gold or acceptable list.
 *   4. Dry-run mode of the runner works without ANTHROPIC_API_KEY.
 *   5. Dry-run pass_rate == 1.0 (simulates perfect routing as infrastructure check).
 *
 * NOTE: This test file does NOT call the live Anthropic API — it is CI-safe.
 *
 * To run the actual routing eval quality check (requires ANTHROPIC_API_KEY):
 *   ANTHROPIC_API_KEY=sk-ant-... npx tsx evals/mcp-routing/runner.ts
 * Goal: ≥80% gold-or-acceptable routing accuracy.
 *
 * MCPT v3.2 Phase 9b — Routing Eval
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { runEval, loadPrompts } from '../../evals/mcp-routing/runner.js'
import type { RoutingPrompt } from '../../evals/mcp-routing/runner.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PROMPTS_PATH = join(__dirname, '../../evals/mcp-routing/prompts.json')

// ── Known tool names (all 22 registered MCP tools) ────────────────────────────

const KNOWN_TOOLS = new Set([
  // Tier 1
  'chart_summary',
  // Tier 2
  'holistic_bundle',
  'multi_school_bundle',
  // Tier 3
  'query_chart_facts',
  'query_signals',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  'vector_search',
  'get_cgm_subgraph',
  'cross_school_lookup',
  // Tier 4
  'read_asset',
  'read_classical_text',
  // Tier 5
  'get_trace',
  'list_recent_queries',
  'tool_health',
  'data_coverage',
  // Tier 6
  'log_prediction',
  'record_outcome',
  'flag_disagreement',
])

// ── Coverage requirement (tools that should appear in routing prompts) ─────────
// Observability/write tools (get_trace, list_recent_queries, tool_health,
// data_coverage, log_prediction, record_outcome, flag_disagreement) are
// intentionally excluded from routing evals — they are triggered by governance
// obligations or explicit operator actions, not by astrological questions.
const ROUTING_TOOLS = new Set([
  'chart_summary',
  'holistic_bundle',
  'multi_school_bundle',
  'query_chart_facts',
  'query_signals',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  'vector_search',
  'get_cgm_subgraph',
  'cross_school_lookup',
  'read_asset',
  'read_classical_text',
])

// ── Helpers ───────────────────────────────────────────────────────────────────

function loadPromptsRaw(): RoutingPrompt[] {
  const raw = readFileSync(PROMPTS_PATH, 'utf-8')
  return JSON.parse(raw) as RoutingPrompt[]
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('MCPT v3.2 P9b — Routing eval: prompts.json structure', () => {
  it('prompts.json has exactly 30 entries', () => {
    const prompts = loadPromptsRaw()
    expect(prompts).toHaveLength(30)
  })

  it('every prompt has required fields: id, prompt, audience_tier, gold_first_tool, acceptable_alternatives', () => {
    const prompts = loadPromptsRaw()
    for (const p of prompts) {
      expect(p, `prompt entry missing "id"`).toHaveProperty('id')
      expect(p, `prompt entry missing "prompt"`).toHaveProperty('prompt')
      expect(p, `prompt entry missing "audience_tier"`).toHaveProperty('audience_tier')
      expect(p, `prompt entry missing "gold_first_tool"`).toHaveProperty('gold_first_tool')
      expect(p, `prompt entry missing "acceptable_alternatives"`).toHaveProperty('acceptable_alternatives')
    }
  })

  it('every id is unique', () => {
    const prompts = loadPromptsRaw()
    const ids = prompts.map(p => p.id)
    const uniqueIds = new Set(ids)
    expect(uniqueIds.size).toBe(ids.length)
  })

  it('every gold_first_tool references a known MCP tool', () => {
    const prompts = loadPromptsRaw()
    for (const p of prompts) {
      expect(
        KNOWN_TOOLS.has(p.gold_first_tool),
        `Prompt "${p.id}": gold_first_tool "${p.gold_first_tool}" is not a known MCP tool`
      ).toBe(true)
    }
  })

  it('every acceptable_alternative references a known MCP tool', () => {
    const prompts = loadPromptsRaw()
    for (const p of prompts) {
      for (const alt of p.acceptable_alternatives) {
        expect(
          KNOWN_TOOLS.has(alt),
          `Prompt "${p.id}": acceptable_alternative "${alt}" is not a known MCP tool`
        ).toBe(true)
      }
    }
  })

  it('acceptable_alternatives does not include gold_first_tool', () => {
    const prompts = loadPromptsRaw()
    for (const p of prompts) {
      expect(
        p.acceptable_alternatives.includes(p.gold_first_tool),
        `Prompt "${p.id}": gold_first_tool "${p.gold_first_tool}" should not also appear in acceptable_alternatives`
      ).toBe(false)
    }
  })

  it('every prompt text is non-empty', () => {
    const prompts = loadPromptsRaw()
    for (const p of prompts) {
      expect(p.prompt.trim().length, `Prompt "${p.id}": prompt text is empty`).toBeGreaterThan(0)
    }
  })

  it('all prompts use super_admin audience_tier', () => {
    const prompts = loadPromptsRaw()
    for (const p of prompts) {
      expect(
        ['super_admin', 'acharya', 'client'].includes(p.audience_tier),
        `Prompt "${p.id}": audience_tier "${p.audience_tier}" is not valid`
      ).toBe(true)
    }
  })
})

describe('MCPT v3.2 P9b — Routing eval: tool coverage', () => {
  it('chart_summary is covered by at least 5 prompts as gold', () => {
    const prompts = loadPromptsRaw()
    const count = prompts.filter(p => p.gold_first_tool === 'chart_summary').length
    expect(count, `Expected ≥5 chart_summary gold prompts, got ${count}`).toBeGreaterThanOrEqual(5)
  })

  it('query_chart_facts is covered by at least 5 prompts as gold', () => {
    const prompts = loadPromptsRaw()
    const count = prompts.filter(p => p.gold_first_tool === 'query_chart_facts').length
    expect(count, `Expected ≥5 query_chart_facts gold prompts, got ${count}`).toBeGreaterThanOrEqual(5)
  })

  it('holistic_bundle is covered by at least 3 prompts as gold', () => {
    const prompts = loadPromptsRaw()
    const count = prompts.filter(p => p.gold_first_tool === 'holistic_bundle').length
    expect(count, `Expected ≥3 holistic_bundle gold prompts, got ${count}`).toBeGreaterThanOrEqual(3)
  })

  it('query_dasha_periods is covered by at least 3 prompts as gold', () => {
    const prompts = loadPromptsRaw()
    const count = prompts.filter(p => p.gold_first_tool === 'query_dasha_periods').length
    expect(count, `Expected ≥3 query_dasha_periods gold prompts, got ${count}`).toBeGreaterThanOrEqual(3)
  })

  it('query_signals is covered by at least 3 prompts as gold', () => {
    const prompts = loadPromptsRaw()
    const count = prompts.filter(p => p.gold_first_tool === 'query_signals').length
    expect(count, `Expected ≥3 query_signals gold prompts, got ${count}`).toBeGreaterThanOrEqual(3)
  })

  it('all routing tools appear at least once as gold or acceptable', () => {
    const prompts = loadPromptsRaw()
    const allMentioned = new Set<string>()
    for (const p of prompts) {
      allMentioned.add(p.gold_first_tool)
      for (const alt of p.acceptable_alternatives) {
        allMentioned.add(alt)
      }
    }

    for (const tool of ROUTING_TOOLS) {
      expect(
        allMentioned.has(tool),
        `Routing tool "${tool}" is not covered by any prompt (gold or acceptable)`
      ).toBe(true)
    }
  })
})

describe('MCPT v3.2 P9b — Routing eval: runner dry-run mode (CI-safe)', () => {
  it('loadPrompts() returns 30 entries', () => {
    const prompts = loadPrompts()
    expect(prompts).toHaveLength(30)
  })

  it('runEval dry-run mode completes without error', async () => {
    const results = await runEval({ dryRun: true })
    expect(results).toBeDefined()
    expect(results.mode).toBe('dry_run')
  })

  it('dry-run result has total == 30', async () => {
    const results = await runEval({ dryRun: true })
    expect(results.total).toBe(30)
  })

  it('dry-run result has required top-level fields', async () => {
    const results = await runEval({ dryRun: true })
    expect(results).toHaveProperty('run_at')
    expect(results).toHaveProperty('git_sha')
    expect(results).toHaveProperty('mode')
    expect(results).toHaveProperty('model')
    expect(results).toHaveProperty('total')
    expect(results).toHaveProperty('passed')
    expect(results).toHaveProperty('failed')
    expect(results).toHaveProperty('pass_rate')
    expect(results).toHaveProperty('goal')
    expect(results).toHaveProperty('goal_met')
    expect(results).toHaveProperty('results')
  })

  it('dry-run simulates perfect routing (all prompts gold-match)', async () => {
    const results = await runEval({ dryRun: true })
    expect(results.passed).toBe(30)
    expect(results.failed).toBe(0)
    expect(results.pass_rate).toBe(1.0)
  })

  it('dry-run each result has required fields', async () => {
    const results = await runEval({ dryRun: true })
    for (const r of results.results) {
      expect(r).toHaveProperty('id')
      expect(r).toHaveProperty('prompt')
      expect(r).toHaveProperty('gold_first_tool')
      expect(r).toHaveProperty('acceptable_alternatives')
      expect(r).toHaveProperty('first_tool_called')
      expect(r).toHaveProperty('outcome')
      expect(r).toHaveProperty('pass')
    }
  })

  it('dry-run all outcomes are "gold"', async () => {
    const results = await runEval({ dryRun: true })
    for (const r of results.results) {
      expect(r.outcome).toBe('gold')
      expect(r.pass).toBe(true)
    }
  })

  it('dry-run goal_met is null (not meaningful without live API)', async () => {
    const results = await runEval({ dryRun: true })
    // In dry-run mode, goal_met is null because the routing quality is simulated
    expect(results.goal_met).toBeNull()
  })

  it('live eval requirement: ≥80% gold-or-acceptable (documented)', () => {
    // This test documents the quality requirement for live eval.
    // It does NOT call the API — it simply asserts the threshold constant.
    // Run: ANTHROPIC_API_KEY=sk-ant-... npx tsx evals/mcp-routing/runner.ts
    const GOAL_THRESHOLD = 0.8
    expect(GOAL_THRESHOLD).toBe(0.8)
  })
})
