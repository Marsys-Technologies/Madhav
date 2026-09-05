import { createHash } from 'node:crypto'
import { describe, expect, it } from 'vitest'
import writerDigestInventory from '../nirmana-writer-digests.json'
import layerPinRecord from '../nirmana-analysis-layer-pins.json'
import {
  NIRMANA_ANALYSIS_LAYERS,
  NIRMANA_ANALYSIS_LAYER_PINS,
  NIRMANA_ANALYSIS_RECEIPTS,
  assertNirmanaWriterInventoryMatchesConvergence,
  getNirmanaAnalysisReceiptBase,
  nirmanaAnalysisReceiptsAvailable,
  type NirmanaAnalysisLayer,
} from '../nirmana-analysis-receipts'
import {
  NIRMANA_L0_ANALYSIS_RECEIPTS,
  NIRMANA_L0_CONVERGENCE_COMMIT,
  NIRMANA_L0_WRITER_INVENTORY_SHA256,
} from '../nirmana-l0-analysis-receipts'

const writerDigests = writerDigestInventory.writers as Record<string, string>

describe('nirmana analysis receipt spine (all layers)', () => {
  it('produces the pinned receipt count for every layer', () => {
    for (const layer of NIRMANA_ANALYSIS_LAYERS) {
      expect(nirmanaAnalysisReceiptsAvailable(layer)).toBe(true)
      expect(Object.keys(NIRMANA_ANALYSIS_RECEIPTS[layer]))
        .toHaveLength(NIRMANA_ANALYSIS_LAYER_PINS[layer].receipt_count)
    }
  })

  it('binds the layer into every receipt base, so a base cannot cross layers', () => {
    for (const layer of NIRMANA_ANALYSIS_LAYERS) {
      for (const base of Object.values(NIRMANA_ANALYSIS_RECEIPTS[layer])) {
        expect(base.layer).toBe(layer)
        expect(base.grounding.convergence_commit)
          .toBe(NIRMANA_ANALYSIS_LAYER_PINS[layer].convergence_commit)
      }
    }
  })

  it('refuses to resolve a real asset under the wrong layer', () => {
    // ga_positions genuinely exists -- but only as an L1 receipt base.
    expect(getNirmanaAnalysisReceiptBase('ga_positions', 'L1')).toBeDefined()
    expect(getNirmanaAnalysisReceiptBase('ga_positions', 'L2')).toBeUndefined()
    expect(getNirmanaAnalysisReceiptBase('bg_prashna_rules', 'L0')).toBeDefined()
    expect(getNirmanaAnalysisReceiptBase('bg_prashna_rules', 'L1')).toBeUndefined()
  })

  it('re-derives each layer aggregate from the live inventory, so a hand-edited pin fails', () => {
    for (const layer of NIRMANA_ANALYSIS_LAYERS) {
      const { asset_prefix, writer_inventory_sha256 } = NIRMANA_ANALYSIS_LAYER_PINS[layer]
      const slice = Object.fromEntries(Object.entries(writerDigests)
        .filter(([assetId]) => assetId.startsWith(asset_prefix))
        .sort(([left], [right]) => left.localeCompare(right)))
      expect(createHash('sha256').update(JSON.stringify(slice)).digest('hex'))
        .toBe(writer_inventory_sha256)
    }
  })

  it('fails closed for the drifted layer ONLY, never globally', () => {
    // Substituting one L1 writer digest must invalidate L1 and leave L0 valid.
    const drifted = { ...writerDigests, ga_positions: '0'.repeat(64) }
    expect(() => assertNirmanaWriterInventoryMatchesConvergence('L1', drifted))
      .toThrow(/L1 writer inventory/i)
    expect(() => assertNirmanaWriterInventoryMatchesConvergence('L0', drifted))
      .not.toThrow()
  })

  it('every layer carries a distinct aggregate, which is what makes per-layer isolation real', () => {
    const aggregates = NIRMANA_ANALYSIS_LAYERS
      .map((layer) => NIRMANA_ANALYSIS_LAYER_PINS[layer].writer_inventory_sha256)
    expect(new Set(aggregates).size).toBe(NIRMANA_ANALYSIS_LAYERS.length)
  })
})

describe('L0 preservation (adjudication #1715, ruling requirement 3)', () => {
  it('keeps L0 pinned constants byte-identical to the pre-generalisation values', () => {
    // Hardcoded here on purpose: this test is the detector for "no L0 capsule is
    // re-accepted". Deriving them from the same record the implementation reads
    // would make it assert nothing.
    expect(NIRMANA_L0_CONVERGENCE_COMMIT).toBe('49bb5c98b864a2cb2fee037cdb7f14f6892a8263')
    expect(NIRMANA_L0_WRITER_INVENTORY_SHA256)
      .toBe('8650e7a7e85beb27adbb66087344a13f3ee77b3fb1c84ebbb6170b9d7ad1c2ae')
    expect(Object.keys(NIRMANA_L0_ANALYSIS_RECEIPTS)).toHaveLength(40)
  })

  it('serves the identical L0 bases through the deprecated shim and the generic module', () => {
    expect(NIRMANA_L0_ANALYSIS_RECEIPTS).toEqual(NIRMANA_ANALYSIS_RECEIPTS.L0)
  })

  it('keeps the four L0 non-writer assets receipt-addressable', () => {
    for (const assetId of layerPinRecord.layers.L0.non_writer_assets) {
      const base = getNirmanaAnalysisReceiptBase(assetId, 'L0' as NirmanaAnalysisLayer)
      expect(base).toBeDefined()
      expect(base?.writer_digest_sha256).toBeNull()
    }
  })
})
