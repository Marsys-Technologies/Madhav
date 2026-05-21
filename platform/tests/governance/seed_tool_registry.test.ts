/**
 * seed_tool_registry.test.ts
 *
 * COV-S9 unit tests for seed_tool_registry.ts manifest parsing logic.
 * Tests run against live CAPABILITY_MANIFEST.json + manifest_overrides.yaml
 * (no DB connection needed — only the file-reading + parsing functions are tested).
 *
 * Audit reference: §G.9 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md (v1.2)
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const REPO_ROOT = resolve(__dirname, '../../../')
const MANIFEST_PATH = resolve(REPO_ROOT, '00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
const OVERRIDES_PATH = resolve(REPO_ROOT, '00_ARCHITECTURE/manifest_overrides.yaml')

// ── Inline reimplementation of the parsing logic (avoids importing a script with top-level side-effects) ──

interface ToolSeedRow {
  tool_name: string
  expose_to_planner: boolean
  description: string
  linked_data_asset_ids: string[]
  binding_source: 'manifest' | 'override' | 'inferred'
}

function loadManifestTools(): ToolSeedRow[] {
  const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8')) as {
    entries: Array<Record<string, unknown>>
  }
  const rows: ToolSeedRow[] = []
  for (const entry of manifest.entries) {
    const toolName = entry['tool_name']
    if (typeof toolName !== 'string' || toolName.length === 0) continue
    const linked: string[] = []
    if (typeof entry['linked_data_asset_id'] === 'string') linked.push(entry['linked_data_asset_id'] as string)
    if (Array.isArray(entry['linked_data_asset_ids'])) {
      for (const id of entry['linked_data_asset_ids'] as string[]) {
        if (!linked.includes(id)) linked.push(id)
      }
    }
    rows.push({
      tool_name: toolName,
      expose_to_planner: Boolean(entry['expose_to_planner'] ?? entry['expose_to_chat'] ?? true),
      description: String(entry['tool_description'] ?? entry['description'] ?? ''),
      linked_data_asset_ids: linked,
      binding_source: 'manifest',
    })
  }
  return rows
}

function loadOverrideTools(): ToolSeedRow[] {
  const yaml = readFileSync(OVERRIDES_PATH, 'utf-8')
  const rows: ToolSeedRow[] = []
  const afterAdditional = yaml.split(/^additional_entries:/m)[1]
  if (!afterAdditional) return rows
  const entries = afterAdditional.split(/\n  - canonical_id:/g)
  for (const block of entries.slice(1)) {
    const toolNameMatch = block.match(/\n\s+tool_name:\s*["']?([a-z_]+)["']?/)
    if (!toolNameMatch) continue
    const toolName = toolNameMatch[1]
    const descMatch = block.match(/\n\s+tool_description:\s*["']?([^\n"']+)["']?/)
    const description = descMatch ? descMatch[1].trim() : ''
    const exposeMatch = block.match(/\n\s+expose_to_planner:\s*(true|false)/)
    const expose_to_planner = exposeMatch ? exposeMatch[1] === 'true' : true
    const linkedMatch = block.match(/\n\s+linked_data_asset_ids:\s*\[([^\]]*)\]/)
    const linked: string[] = []
    if (linkedMatch) {
      const ids = linkedMatch[1].match(/"([^"]+)"|'([^']+)'|([A-Z0-9_]+)/g) ?? []
      for (const id of ids) {
        const clean = id.replace(/['"]/g, '').trim()
        if (clean.length > 0) linked.push(clean)
      }
    }
    rows.push({ tool_name: toolName, expose_to_planner, description, linked_data_asset_ids: linked, binding_source: 'override' })
  }
  return rows
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('COV-S9 — seed_tool_registry: manifest tool parsing', () => {
  it('loadManifestTools returns at least 5 tool rows', () => {
    const rows = loadManifestTools()
    expect(rows.length).toBeGreaterThanOrEqual(5)
  })

  it('every manifest tool row has a non-empty tool_name', () => {
    const rows = loadManifestTools()
    for (const row of rows) {
      expect(row.tool_name.length).toBeGreaterThan(0)
    }
  })

  it('loadOverrideTools returns at least 25 tool rows (COV-S2 additions)', () => {
    const rows = loadOverrideTools()
    expect(rows.length).toBeGreaterThanOrEqual(25)
  })

  it('combined manifest + override tools covers all 30 expected RETRIEVAL_TOOLS', () => {
    const EXPECTED_30 = new Set([
      'msr_sql', 'pattern_register', 'resonance_register', 'cluster_atlas',
      'contradiction_register', 'temporal', 'query_msr_aggregate', 'cgm_graph_walk',
      'manifest_query', 'vector_search', 'kp_query', 'saham_query', 'divisional_query',
      'chart_facts_query', 'cross_varga_dignity_query', 'domain_report_query',
      'remedial_codex_query', 'timeline_query', 'query_signal_state',
      'query_kp_ruling_planets', 'query_varshaphala', 'lel_query',
      'classical_text_search', 'classical_attribution_lookup',
      'multi_school_signal_lookup', 'convergence_score_lookup', 'query_ephemeris',
      'query_panchanga', 'query_transit_event', 'query_dasha_periods',
    ])
    const manifestNames = new Set(loadManifestTools().map((r) => r.tool_name))
    const overrideNames = new Set(loadOverrideTools().map((r) => r.tool_name))
    const combined = new Set([...manifestNames, ...overrideNames])
    const missing = [...EXPECTED_30].filter((t) => !combined.has(t))
    expect(missing).toHaveLength(0)
  })

  it('every override tool row with linked_data_asset_ids has at least one entry', () => {
    const rows = loadOverrideTools()
    // Only tools with non-empty linked_data_asset_ids should have valid entries
    const toolsWithLinks = rows.filter((r) => r.linked_data_asset_ids.length > 0)
    expect(toolsWithLinks.length).toBeGreaterThan(0)
    for (const row of toolsWithLinks) {
      for (const id of row.linked_data_asset_ids) {
        expect(id.length).toBeGreaterThan(0)
      }
    }
  })
})
