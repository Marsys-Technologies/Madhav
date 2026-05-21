/**
 * r_rule_gating.test.ts — COV-S6
 *
 * Verifies that R-rule routing constraints from PLANNER_PROMPT_v2_0.md are
 * promoted into machine-readable gating_constraints fields in
 * manifest_overrides.yaml, and that manifest_compressor passes them through.
 *
 * AC1: query_panchanga entry has gating_constraints in manifest_overrides.yaml
 * AC2: manifest_compressor passes through gating_constraints in CompressedEntry
 * AC3: (this file)
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import yaml from 'js-yaml'
import {
  compressManifest,
  type CapabilityManifest,
  type CapabilityManifestEntry,
} from '@/lib/pipeline/manifest_compressor'

const REPO_ROOT = resolve(__dirname, '../../../')
const ARCH_DIR = resolve(REPO_ROOT, '00_ARCHITECTURE')

// ── helper: load and parse manifest_overrides.yaml ──────────────────────────

interface ManifestOverrides {
  additional_entries?: CapabilityManifestEntry[]
  overrides?: Record<string, unknown>
  mirror_pairs?: Record<string, unknown>
}

function loadOverrides(): ManifestOverrides {
  const raw = readFileSync(resolve(ARCH_DIR, 'manifest_overrides.yaml'), 'utf-8')
  return yaml.load(raw) as ManifestOverrides
}

// ── AC1 group — manifest_overrides.yaml structural checks ───────────────────

describe('COV-S6 AC1 — manifest_overrides.yaml gating_constraints structure', () => {
  it('query_panchanga entry exists in additional_entries', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_panchanga')
    expect(entry, 'query_panchanga not found in additional_entries').toBeDefined()
  })

  it('query_panchanga has gating_constraints array with at least 1 entry', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_panchanga')
    expect(entry?.gating_constraints).toBeDefined()
    expect(Array.isArray(entry?.gating_constraints)).toBe(true)
    expect(entry!.gating_constraints!.length).toBeGreaterThanOrEqual(1)
  })

  it('each query_panchanga gating_constraint has type and action fields', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_panchanga')
    for (const constraint of entry!.gating_constraints!) {
      expect(typeof constraint.type).toBe('string')
      expect(constraint.type.length).toBeGreaterThan(0)
      expect(typeof constraint.action).toBe('string')
      expect(constraint.action.length).toBeGreaterThan(0)
    }
  })

  it('query_panchanga has a query_type_match constraint for panchang queries', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_panchanga')
    const hasMatch = entry!.gating_constraints!.some(
      c => c.type === 'query_type_match' && typeof c.query_type === 'string',
    )
    expect(hasMatch, 'No query_type_match constraint found on query_panchanga').toBe(true)
  })

  it('query_muhurat has gating_constraints with a query_type_match entry', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_muhurat')
    expect(entry, 'query_muhurat not found').toBeDefined()
    expect(Array.isArray(entry?.gating_constraints)).toBe(true)
    expect(entry!.gating_constraints!.length).toBeGreaterThanOrEqual(1)
    const hasMatch = entry!.gating_constraints!.some(c => c.type === 'query_type_match')
    expect(hasMatch).toBe(true)
  })

  it('query_jaimini_drishti has gating_constraints with a jaimini query_type_match', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_jaimini_drishti')
    expect(entry, 'query_jaimini_drishti not found').toBeDefined()
    expect(Array.isArray(entry?.gating_constraints)).toBe(true)
    const hasJaimini = entry!.gating_constraints!.some(
      c => c.type === 'query_type_match' && c.query_type === 'jaimini',
    )
    expect(hasJaimini, 'No jaimini query_type_match on query_jaimini_drishti').toBe(true)
  })

  it('query_v7_additions has gating_constraints with at least one divisional entry', () => {
    const overrides = loadOverrides()
    const entry = overrides.additional_entries?.find(e => e.tool_name === 'query_v7_additions')
    expect(entry, 'query_v7_additions not found').toBeDefined()
    expect(Array.isArray(entry?.gating_constraints)).toBe(true)
    expect(entry!.gating_constraints!.length).toBeGreaterThanOrEqual(1)
  })
})

// ── AC2 group — manifest_compressor passes through gating_constraints ────────

describe('COV-S6 AC2 — manifest_compressor passes through gating_constraints', () => {
  it('compressManifest includes g field when entry has gating_constraints', () => {
    const synthetic: CapabilityManifest = {
      entries: [
        {
          canonical_id: 'TEST_PANCHANGA',
          tool_name: 'query_panchanga',
          tool_description: 'Test panchanga tool for gating constraint passthrough.',
          expose_to_planner: true,
          token_cost_hint: 'low',
          linked_data_asset_id: 'PANCHANGA_DAILY',
          query_schema: { type: 'object', properties: { date: { type: 'string' } } },
          gating_constraints: [
            { type: 'query_type_match', query_type: 'panchang', action: 'prefer' },
          ],
        },
      ],
    }
    const compressed = compressManifest(synthetic)
    expect(compressed).toHaveLength(1)
    expect(compressed[0].g).toBeDefined()
    expect(Array.isArray(compressed[0].g)).toBe(true)
    expect(compressed[0].g!.length).toBe(1)
    expect(compressed[0].g![0].type).toBe('query_type_match')
    expect(compressed[0].g![0].action).toBe('prefer')
    expect(compressed[0].g![0].query_type).toBe('panchang')
  })

  it('compressManifest omits g field when entry has no gating_constraints', () => {
    const synthetic: CapabilityManifest = {
      entries: [
        {
          canonical_id: 'NO_GATE',
          tool_name: 'msr_sql',
          tool_description: 'MSR signal retrieval without gating constraints.',
          expose_to_planner: true,
          token_cost_hint: 'med',
          linked_data_asset_id: 'MSR',
          query_schema: { type: 'object', properties: { domain: { type: 'string' } } },
        },
      ],
    }
    const compressed = compressManifest(synthetic)
    expect(compressed).toHaveLength(1)
    expect(compressed[0].g).toBeUndefined()
  })

  it('compressManifest omits g field when gating_constraints is empty array', () => {
    const synthetic: CapabilityManifest = {
      entries: [
        {
          canonical_id: 'EMPTY_GATE',
          tool_name: 'some_tool',
          tool_description: 'Tool with empty gating constraints array.',
          expose_to_planner: true,
          token_cost_hint: 'low',
          linked_data_asset_id: 'FORENSIC',
          query_schema: { type: 'object', properties: {} },
          gating_constraints: [],
        },
      ],
    }
    const compressed = compressManifest(synthetic)
    expect(compressed).toHaveLength(1)
    expect(compressed[0].g).toBeUndefined()
  })

  it('compressManifest passthrough preserves all constraint fields (type, action, query_type)', () => {
    const constraints = [
      { type: 'query_type_match', query_type: 'panchang', action: 'prefer' },
      { type: 'query_type_match', query_type: 'tithi_lookup', action: 'prefer' },
    ]
    const synthetic: CapabilityManifest = {
      entries: [
        {
          canonical_id: 'MULTI_GATE',
          tool_name: 'query_panchanga_multi',
          tool_description: 'Multi-constraint tool for passthrough test.',
          expose_to_planner: true,
          token_cost_hint: 'low',
          linked_data_asset_id: 'PANCHANGA_DAILY',
          query_schema: { type: 'object', properties: { date: { type: 'string' } } },
          gating_constraints: constraints,
        },
      ],
    }
    const compressed = compressManifest(synthetic)
    expect(compressed[0].g).toHaveLength(2)
    expect(compressed[0].g).toEqual(constraints)
  })
})
