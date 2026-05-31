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
  it('has at least 28 entries', () => {
    expect(Object.keys(ASSET_NAMES).length).toBeGreaterThanOrEqual(28)
  })

  it('every entry has sanskrit, english, subtitle, and layer', () => {
    for (const [key, entry] of Object.entries(ASSET_NAMES)) {
      expect(entry.sanskrit, `${key}.sanskrit`).toBeTruthy()
      expect(entry.english, `${key}.english`).toBeTruthy()
      expect(entry.subtitle, `${key}.subtitle`).toBeTruthy()
      expect(['L1', 'L2_5', 'L3', 'L4'], `${key}.layer`).toContain(entry.layer)
    }
  })

  it('contains all 8 L1 Adhara foundation assets', () => {
    const l1Keys: AssetKey[] = [
      'pratyaksha', 'panchanga', 'drishti_lakshana', 'graha_sthana',
      'bhava_vibhaga', 'varga', 'dasha_krama', 'yoga_sambandha',
    ]
    for (const k of l1Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L1')
    }
  })

  it('contains all 5 L2_5 Sambandha synthesis assets', () => {
    const l25Keys: AssetKey[] = [
      'lakshana_kosha', 'karana_jala', 'anubandha_mandala', 'upaya_kosha', 'sangam',
    ]
    for (const k of l25Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L2_5')
    }
  })

  it('contains all 8 core L3 Sutra meta-thread assets', () => {
    const l3Keys: AssetKey[] = [
      'kala_yoga', 'bandha', 'chakra_vichara', 'vedha_drishti',
      'bhrigu_kshetra', 'tajik_varsha', 'sphurana', 'kala_smriti',
    ]
    for (const k of l3Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L3')
    }
  })

  it('contains all 3 L4 Vyavahara interface assets', () => {
    const l4Keys: AssetKey[] = ['prashna', 'yantra_mcp', 'marga']
    for (const k of l4Keys) {
      expect(ASSET_NAMES[k].layer).toBe('L4')
    }
  })

  it('lakshana_kosha subtitle references MSR', () => {
    expect(ASSET_NAMES.lakshana_kosha.subtitle).toContain('MSR')
  })

  it('karana_jala subtitle references CGM', () => {
    expect(ASSET_NAMES.karana_jala.subtitle).toContain('CGM')
  })
})

describe('LAYER_NAMES', () => {
  const layers: LayerKey[] = ['L1', 'L2_5', 'L3', 'L4']

  it('has all four layers', () => {
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

  it('L1 is Adhara Foundation', () => {
    expect(LAYER_NAMES.L1.sanskrit).toBe('Adhara')
    expect(LAYER_NAMES.L1.english).toBe('Foundation')
  })

  it('L2_5 is Sambandha Synthesis', () => {
    expect(LAYER_NAMES.L2_5.sanskrit).toBe('Sambandha')
    expect(LAYER_NAMES.L2_5.english).toBe('Synthesis')
  })

  it('L3 is Sutra Meta-threads', () => {
    expect(LAYER_NAMES.L3.sanskrit).toBe('Sutra')
    expect(LAYER_NAMES.L3.english).toBe('Meta-threads')
  })

  it('L4 is Vyavahara Interface', () => {
    expect(LAYER_NAMES.L4.sanskrit).toBe('Vyavahara')
    expect(LAYER_NAMES.L4.english).toBe('Interface')
  })
})

describe('assetsByLayer', () => {
  it('returns 8 L1 assets', () => {
    expect(assetsByLayer('L1').length).toBe(8)
  })

  it('returns 5 L2_5 assets', () => {
    expect(assetsByLayer('L2_5').length).toBe(5)
  })

  it('returns L4 assets including prashna', () => {
    const l4 = assetsByLayer('L4')
    expect(l4).toContain('prashna')
  })

  it('every returned key actually has the requested layer', () => {
    for (const layer of ['L1', 'L2_5', 'L3', 'L4'] as LayerKey[]) {
      for (const key of assetsByLayer(layer)) {
        expect(ASSET_NAMES[key].layer).toBe(layer)
      }
    }
  })
})

describe('assetLabel', () => {
  it('formats pratyaksha correctly', () => {
    expect(assetLabel('pratyaksha')).toBe('Pratyaksha · Direct perception')
  })

  it('formats lakshana_kosha correctly', () => {
    expect(assetLabel('lakshana_kosha')).toBe('Lakshana Kosha · Treasury of indicators')
  })
})
