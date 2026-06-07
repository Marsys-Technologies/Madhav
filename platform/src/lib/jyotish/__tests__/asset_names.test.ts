import { describe, it, expect } from 'vitest'
import {
  ASSET_NAMES,
  LAYER_NAMES,
  assetsByLayer,
  assetLabel,
  type AssetKey,
  type LayerKey,
} from '../asset_names'

describe('ASSET_NAMES', () => {
  it('has at least 42 entries (Brahma 6-layer model)', () => {
    expect(Object.keys(ASSET_NAMES).length).toBeGreaterThanOrEqual(42)
  })

  it('every entry has sanskrit, english, subtitle, and layer', () => {
    for (const [key, entry] of Object.entries(ASSET_NAMES)) {
      expect(entry.sanskrit, `${key}.sanskrit`).toBeTruthy()
      expect(entry.english, `${key}.english`).toBeTruthy()
      expect(entry.subtitle, `${key}.subtitle`).toBeTruthy()
      expect(['L0', 'L1', 'L2', 'L3', 'L4', 'L5'], `${key}.layer`).toContain(entry.layer)
    }
  })

  it('contains all 12 L0 Brahmagyan global foundation assets', () => {
    const l0Keys: AssetKey[] = [
      'bg_ephemeris', 'bg_reference', 'bg_texts', 'bg_ontology',
      'bg_text_index', 'bg_rules', 'bg_remedies', 'bg_concordance',
      'bg_yogas', 'bg_dasha_systems', 'bg_doshas', 'bg_compendium_index',
    ]
    for (const k of l0Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L0')
    }
  })

  it('contains all 8 L1 Gaṇita chart-facts assets', () => {
    const l1Keys: AssetKey[] = [
      'ga_engine', 'ga_positions', 'ga_divisionals', 'ga_dashas',
      'ga_strength', 'ga_sensitive', 'ga_panchanga', 'ga_facts_store',
    ]
    for (const k of l1Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L1')
    }
  })

  it('contains all 8 L2 Bodha intelligence assets', () => {
    const l2Keys: AssetKey[] = [
      'bo_signals', 'bo_graph', 'bo_domain_links', 'bo_resonance',
      'bo_lenses', 'bo_remediation', 'bo_embeddings', 'bo_holistic',
    ]
    for (const k of l2Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L2')
    }
  })

  it('contains all 4 L3 Kāla temporal assets', () => {
    const l3Keys: AssetKey[] = ['ka_timeline', 'ka_convergence', 'ka_obstruction', 'ka_temporal']
    for (const k of l3Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L3')
    }
  })

  it('contains all 5 L4 Phala prediction assets', () => {
    const l4Keys: AssetKey[] = [
      'ph_anchors', 'ph_mitigation', 'ph_rectification', 'ph_muhurta', 'ph_outlook',
    ]
    for (const k of l4Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L4')
    }
  })

  it('contains all 6 L5 Mīmāṃsā learning assets', () => {
    const l5Keys: AssetKey[] = [
      'mi_lel_intake', 'mi_ledger', 'mi_outcome', 'mi_multiplier', 'mi_research', 'mi_answer_quality',
    ]
    for (const k of l5Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L5')
    }
  })

  it('ga_positions subtitle references Swiss Ephemeris', () => {
    expect(ASSET_NAMES.ga_positions.subtitle).toContain('Swiss Ephemeris')
  })

  it('bo_signals subtitle references MSR', () => {
    expect(ASSET_NAMES.bo_signals.subtitle).toContain('MSR')
  })

  it('bo_graph subtitle references CGM', () => {
    expect(ASSET_NAMES.bo_graph.subtitle).toContain('CGM')
  })
})

describe('LAYER_NAMES', () => {
  const layers: LayerKey[] = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']

  it('has all six Brahma layers', () => {
    for (const layer of layers) {
      expect(LAYER_NAMES[layer]).toBeDefined()
    }
  })

  it('each layer has sanskrit and english', () => {
    for (const layer of layers) {
      expect(LAYER_NAMES[layer].sanskrit).toBeTruthy()
      expect(LAYER_NAMES[layer].english).toBeTruthy()
    }
  })

  it('L0 is Brahmagyan Foundation', () => {
    expect(LAYER_NAMES.L0.sanskrit).toBe('Brahmagyan')
    expect(LAYER_NAMES.L0.english).toBe('Foundation')
  })

  it('L1 is Gaṇita Chart Facts', () => {
    expect(LAYER_NAMES.L1.sanskrit).toBe('Gaṇita')
    expect(LAYER_NAMES.L1.english).toBe('Chart Facts')
  })

  it('L2 is Bodha Intelligence', () => {
    expect(LAYER_NAMES.L2.sanskrit).toBe('Bodha')
    expect(LAYER_NAMES.L2.english).toBe('Intelligence')
  })

  it('L3 is Kāla Temporal', () => {
    expect(LAYER_NAMES.L3.sanskrit).toBe('Kāla')
    expect(LAYER_NAMES.L3.english).toBe('Temporal')
  })

  it('L4 is Phala Prediction', () => {
    expect(LAYER_NAMES.L4.sanskrit).toBe('Phala')
    expect(LAYER_NAMES.L4.english).toBe('Prediction')
  })

  it('L5 is Mīmāṃsā Learning', () => {
    expect(LAYER_NAMES.L5.sanskrit).toBe('Mīmāṃsā')
    expect(LAYER_NAMES.L5.english).toBe('Learning')
  })
})

describe('assetsByLayer', () => {
  it('returns 12 L0 Brahmagyan assets', () => {
    expect(assetsByLayer('L0').length).toBe(12)
  })

  it('returns 8 L1 Gaṇita assets', () => {
    expect(assetsByLayer('L1').length).toBe(8)
  })

  it('returns 8 L2 Bodha assets', () => {
    expect(assetsByLayer('L2').length).toBe(8)
  })

  it('returns 4 L3 Kāla assets', () => {
    expect(assetsByLayer('L3').length).toBe(4)
  })

  it('returns 5 L4 Phala assets', () => {
    expect(assetsByLayer('L4').length).toBe(5)
  })

  it('returns 6 L5 Mīmāṃsā assets', () => {
    expect(assetsByLayer('L5').length).toBe(6)
  })

  it('every returned key actually has the requested layer', () => {
    for (const layer of ['L0', 'L1', 'L2', 'L3', 'L4', 'L5'] as LayerKey[]) {
      for (const key of assetsByLayer(layer)) {
        expect(ASSET_NAMES[key].layer).toBe(layer)
      }
    }
  })
})

describe('assetLabel', () => {
  it('formats ga_positions correctly', () => {
    expect(assetLabel('ga_positions')).toBe('Graha Sthāna · Positions')
  })

  it('formats bo_signals correctly', () => {
    expect(assetLabel('bo_signals')).toBe('Lakṣaṇa · Signals')
  })
})
