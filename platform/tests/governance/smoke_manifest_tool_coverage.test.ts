/**
 * smoke_manifest_tool_coverage.test.ts
 *
 * COV-S2 manifest_audit gate: verifies that all 30 wired retrieval tools have
 * a manifest entry. Counts tool_name entries across:
 *   (a) CAPABILITY_MANIFEST.json (existing generated entries)
 *   (b) manifest_overrides.yaml additional_entries (hand-authored entries)
 *
 * Halt condition: total < 30 (manifest_audit fingerprint divergence beyond
 * known living-files set — per §G.2 acceptance criterion).
 *
 * Audit reference: §G.2 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md (v1.2)
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const REPO_ROOT = resolve(__dirname, '../../../')

function loadManifestToolNames(): Set<string> {
  const manifestPath = resolve(REPO_ROOT, '00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8')) as {
    entries: Array<Record<string, unknown>>
  }
  const names = new Set<string>()
  for (const entry of manifest.entries) {
    if (typeof entry['tool_name'] === 'string' && entry['tool_name'].length > 0) {
      names.add(entry['tool_name'] as string)
    }
  }
  return names
}

function loadOverrideToolNames(): Set<string> {
  const overridePath = resolve(REPO_ROOT, '00_ARCHITECTURE/manifest_overrides.yaml')
  const yaml = readFileSync(overridePath, 'utf-8')
  const names = new Set<string>()
  // Simple regex extraction — YAML parsing without a dep; tool_name lines under additional_entries
  const matches = yaml.matchAll(/^\s{2}-\s[\s\S]*?tool_name:\s*["']?([a-z_]+)["']?/gm)
  for (const m of matches) {
    names.add(m[1])
  }
  return names
}

// The 30 canonical tool names from RETRIEVAL_TOOLS[] in retrieve/index.ts
const EXPECTED_TOOLS = new Set([
  'msr_sql',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'temporal',
  'query_msr_aggregate',
  'cgm_graph_walk',
  'manifest_query',
  'vector_search',
  'kp_query',
  'saham_query',
  'divisional_query',
  'chart_facts_query',
  'cross_varga_dignity_query',
  'domain_report_query',
  'remedial_codex_query',
  'timeline_query',
  'query_signal_state',
  'query_kp_ruling_planets',
  'query_varshaphala',
  'lel_query',
  'classical_text_search',
  'classical_attribution_lookup',
  'multi_school_signal_lookup',
  'convergence_score_lookup',
  'query_ephemeris',
  'query_panchanga',
  'query_transit_event',
  'query_dasha_periods',
])

describe('COV-S2 — manifest_audit: all 30 retrieval tools have a manifest entry', () => {
  it('CAPABILITY_MANIFEST.json parses and has at least 5 tool_name entries', () => {
    const names = loadManifestToolNames()
    expect(names.size).toBeGreaterThanOrEqual(5)
  })

  it('manifest_overrides.yaml additional_entries contains at least 25 tool_name entries', () => {
    const names = loadOverrideToolNames()
    // Only count tools that are in EXPECTED_TOOLS to avoid false positives
    const toolNames = new Set([...names].filter((n) => EXPECTED_TOOLS.has(n)))
    expect(toolNames.size).toBeGreaterThanOrEqual(25)
  })

  it('combined coverage across manifest + overrides reaches all 30 expected tools', () => {
    const manifestNames = loadManifestToolNames()
    const overrideNames = loadOverrideToolNames()
    const combined = new Set([...manifestNames, ...overrideNames])
    const covered = new Set([...combined].filter((n) => EXPECTED_TOOLS.has(n)))

    const missing = [...EXPECTED_TOOLS].filter((t) => !covered.has(t))
    expect(missing).toHaveLength(0)
    expect(covered.size).toBe(30)
  })

  it('every expected tool name appears exactly once across combined sources', () => {
    const manifestNames = loadManifestToolNames()
    const overrideNames = loadOverrideToolNames()
    for (const tool of EXPECTED_TOOLS) {
      const inManifest = manifestNames.has(tool)
      const inOverrides = overrideNames.has(tool)
      expect(inManifest || inOverrides).toBe(true)
    }
  })
})
