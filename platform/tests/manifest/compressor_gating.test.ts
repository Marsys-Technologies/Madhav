/**
 * compressor_gating.test.ts — COV-S6 gate test
 *
 * Verifies that manifest_compressor.ts correctly emits gating_constraints
 * into the tool description string when an entry carries the COV-S6
 * { preferred_when, avoid_when } object form.
 *
 * Tests:
 *   1. Synthetic entry with preferred_when emits "Preferred when: ..." in d field
 *   2. Synthetic entry with avoid_when emits "Avoid when: ..." in d field
 *   3. Synthetic entry with both emits both parts
 *   4. Legacy Array<{ condition, action }> form produces no gating hint (backward compat)
 *   5. Entry with no gating_constraints produces no hint (plain description only)
 *   6. Live manifest entries for R28/R29/R30 tools have gating_constraints and their
 *      compressed description contains "Preferred when:"
 *   7. buildGatingHint is exported and callable directly
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  compressManifest,
  buildGatingHint,
  type CapabilityManifest,
  type CapabilityManifestEntry,
} from '@/lib/pipeline/manifest_compressor'

function loadLiveManifest(): CapabilityManifest {
  const path = resolve(__dirname, '../../../00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  return JSON.parse(readFileSync(path, 'utf-8')) as CapabilityManifest
}

function makeSyntheticManifest(toolEntry: CapabilityManifestEntry): CapabilityManifest {
  return {
    entries: [
      {
        ...toolEntry,
        canonical_id: toolEntry.canonical_id ?? 'TEST_TOOL',
        tool_name: toolEntry.tool_name ?? 'test_tool',
        expose_to_planner: true,
        tool_description: toolEntry.tool_description ?? 'Base description text for this tool.',
        query_schema: toolEntry.query_schema ?? {
          type: 'object',
          properties: { param_a: {}, param_b: {} },
        },
        token_cost_hint: toolEntry.token_cost_hint ?? 'low',
      },
    ],
  }
}

describe('compressor_gating (COV-S6)', () => {
  it('emits "Preferred when:" hint when preferred_when is set', () => {
    const manifest = makeSyntheticManifest({
      canonical_id: 'T1',
      gating_constraints: {
        preferred_when: ['test condition for preferred'],
        avoid_when: [],
      },
    })
    const entries = compressManifest(manifest)
    expect(entries).toHaveLength(1)
    expect(entries[0].d).toContain('Preferred when: test condition for preferred')
  })

  it('emits "Avoid when:" hint when avoid_when is set', () => {
    const manifest = makeSyntheticManifest({
      canonical_id: 'T2',
      gating_constraints: {
        preferred_when: [],
        avoid_when: ['test condition for avoid'],
      },
    })
    const entries = compressManifest(manifest)
    expect(entries).toHaveLength(1)
    expect(entries[0].d).toContain('Avoid when: test condition for avoid')
  })

  it('emits both preferred and avoid hints when both are set', () => {
    const manifest = makeSyntheticManifest({
      canonical_id: 'T3',
      gating_constraints: {
        preferred_when: ['preferred condition A'],
        avoid_when: ['avoid condition B'],
      },
    })
    const entries = compressManifest(manifest)
    expect(entries).toHaveLength(1)
    expect(entries[0].d).toContain('Preferred when: preferred condition A')
    expect(entries[0].d).toContain('Avoid when: avoid condition B')
  })

  it('produces no gating hint for legacy Array<{condition,action}> form', () => {
    const manifest = makeSyntheticManifest({
      canonical_id: 'T4',
      tool_description: 'Plain base description only.',
      gating_constraints: [{ condition: 'legacy_cond', action: 'legacy_action' }] as unknown as {
        preferred_when: string[]
        avoid_when: string[]
      },
    })
    const entries = compressManifest(manifest)
    expect(entries).toHaveLength(1)
    // No gating hint — legacy format is silently ignored
    expect(entries[0].d).not.toContain('Preferred when:')
    expect(entries[0].d).not.toContain('Avoid when:')
    expect(entries[0].d).toContain('Plain base description only.')
  })

  it('produces no gating hint when gating_constraints is absent', () => {
    const manifest = makeSyntheticManifest({
      canonical_id: 'T5',
      tool_description: 'Description with no gating.',
    })
    const entries = compressManifest(manifest)
    expect(entries).toHaveLength(1)
    expect(entries[0].d).not.toContain('Preferred when:')
    expect(entries[0].d).not.toContain('Avoid when:')
    expect(entries[0].d).toBe('Description with no gating.')
  })

  it('buildGatingHint returns empty string for undefined/null', () => {
    expect(buildGatingHint(undefined)).toBe('')
    expect(buildGatingHint([] as unknown as { preferred_when: string[]; avoid_when: string[] })).toBe('')
  })

  it('buildGatingHint uses only the first condition from each list (token minimization)', () => {
    const hint = buildGatingHint({
      preferred_when: ['first preferred', 'second preferred'],
      avoid_when: ['first avoid', 'second avoid'],
    })
    expect(hint).toContain('first preferred')
    expect(hint).not.toContain('second preferred')
    expect(hint).toContain('first avoid')
    expect(hint).not.toContain('second avoid')
  })

  it('live manifest: R28 query_signal_state has gating_constraints and emits Preferred when hint', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    const signalState = entries.find(e => e.t === 'query_signal_state')
    expect(signalState, 'query_signal_state must be in manifest with expose_to_planner=true').toBeDefined()
    expect(signalState!.d).toContain('Preferred when:')
  })

  it('live manifest: R29 query_kp_ruling_planets has gating_constraints and emits Preferred when hint', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    const kpRuling = entries.find(e => e.t === 'query_kp_ruling_planets')
    expect(kpRuling, 'query_kp_ruling_planets must be in manifest with expose_to_planner=true').toBeDefined()
    expect(kpRuling!.d).toContain('Preferred when:')
  })

  it('live manifest: R30 query_varshaphala has gating_constraints and emits Preferred when hint', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    const varsha = entries.find(e => e.t === 'query_varshaphala')
    expect(varsha, 'query_varshaphala must be in manifest with expose_to_planner=true').toBeDefined()
    expect(varsha!.d).toContain('Preferred when:')
  })

  it('gating hint does not cause description word count to violate 60-word base limit (base words still ≤60)', () => {
    // The gating hint is appended AFTER the 60-word base description, so total d may exceed 60 words.
    // But the base tool description itself is still capped at DESCRIPTION_MAX_WORDS.
    // This test confirms the base is respected.
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    for (const entry of entries) {
      // Strip gating hint portion to check base description words
      const baseOnly = entry.d.split(' Preferred when:')[0].split(' Avoid when:')[0]
      const wordCount = baseOnly.split(/\s+/).filter(Boolean).length
      expect(wordCount).toBeLessThanOrEqual(60)
    }
  })
})
