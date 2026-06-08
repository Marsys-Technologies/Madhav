import { describe, it, expect } from 'vitest'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

// L0 brahmagyan asset registry mirroring migration 179 depends_on values.
// Tier 0: bg_ontology, bg_reference (no deps)
// Tier 1: bg_yogas, bg_dasha_systems, bg_doshas (dep: bg_ontology)
// Tier 2: bg_texts (already done; dep: bg_ontology)
// Tier 3: bg_text_index, bg_rules, bg_remedies (deps include bg_ontology, bg_texts, etc.)
// Tier 4: bg_concordance, bg_compendium_index (deps include bg_texts, bg_text_index, etc.)

function reg(
  asset_id: string,
  depends_on: string[],
  estimated_seconds: number | null = 60
): RegistryEntry {
  return { asset_id, layer: 'brahmagyan', depends_on, estimated_seconds }
}

const L0_REGISTRY: RegistryEntry[] = [
  reg('bg_ontology', []),
  reg('bg_reference', ['bg_ontology']),
  reg('bg_texts', ['bg_ontology']),
  reg('bg_yogas', ['bg_ontology']),
  reg('bg_dasha_systems', ['bg_ontology']),
  reg('bg_doshas', ['bg_ontology']),
  reg('bg_text_index', ['bg_texts']),
  reg('bg_rules', ['bg_texts', 'bg_ontology']),
  reg('bg_remedies', ['bg_ontology', 'bg_doshas']),
  reg('bg_concordance', ['bg_texts', 'bg_text_index', 'bg_reference', 'bg_rules']),
  reg('bg_compendium_index', ['bg_texts', 'bg_text_index', 'bg_reference']),
  reg('bg_ephemeris', []),
]

const EMPTY_THROUGHPUT = new Map<string, ThroughputEntry>()

describe('L0 brahmagyan layer — topo dispatch order', () => {
  it('includes all 12 brahmagyan assets when all are dormant', () => {
    const result = resolveBuildPlan({
      scope: 'layer',
      scope_target: 'brahmagyan',
      action: 'build',
      registry: L0_REGISTRY,
      throughput: EMPTY_THROUGHPUT,
    })
    expect(result.plan).toHaveLength(12)
    for (const id of L0_REGISTRY.map(r => r.asset_id)) {
      expect(result.plan).toContain(id)
    }
  })

  it('bg_ontology precedes all Tier-1 assets (bg_yogas, bg_dasha_systems, bg_doshas)', () => {
    const result = resolveBuildPlan({
      scope: 'layer',
      scope_target: 'brahmagyan',
      action: 'build',
      registry: L0_REGISTRY,
      throughput: EMPTY_THROUGHPUT,
    })
    const plan = result.plan
    const ontIdx = plan.indexOf('bg_ontology')
    expect(ontIdx).toBeGreaterThan(-1)
    expect(plan.indexOf('bg_yogas')).toBeGreaterThan(ontIdx)
    expect(plan.indexOf('bg_dasha_systems')).toBeGreaterThan(ontIdx)
    expect(plan.indexOf('bg_doshas')).toBeGreaterThan(ontIdx)
  })

  it('bg_texts precedes bg_text_index, bg_rules, bg_concordance, bg_compendium_index', () => {
    const result = resolveBuildPlan({
      scope: 'layer',
      scope_target: 'brahmagyan',
      action: 'build',
      registry: L0_REGISTRY,
      throughput: EMPTY_THROUGHPUT,
    })
    const plan = result.plan
    const textsIdx = plan.indexOf('bg_texts')
    expect(plan.indexOf('bg_text_index')).toBeGreaterThan(textsIdx)
    expect(plan.indexOf('bg_rules')).toBeGreaterThan(textsIdx)
    expect(plan.indexOf('bg_concordance')).toBeGreaterThan(textsIdx)
    expect(plan.indexOf('bg_compendium_index')).toBeGreaterThan(textsIdx)
  })

  it('bg_text_index precedes bg_concordance and bg_compendium_index', () => {
    const result = resolveBuildPlan({
      scope: 'layer',
      scope_target: 'brahmagyan',
      action: 'build',
      registry: L0_REGISTRY,
      throughput: EMPTY_THROUGHPUT,
    })
    const plan = result.plan
    const idxIdx = plan.indexOf('bg_text_index')
    expect(plan.indexOf('bg_concordance')).toBeGreaterThan(idxIdx)
    expect(plan.indexOf('bg_compendium_index')).toBeGreaterThan(idxIdx)
  })
})
