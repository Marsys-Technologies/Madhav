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
  it('keeps L0 pinned constants byte-identical to the ratified baseline', () => {
    // Hardcoded here on purpose: this test is the detector for "no L0 capsule is
    // re-accepted, and no UNRATIFIED re-pin lands silently". Deriving these from
    // the same record the implementation reads would make it assert nothing.
    //
    // writer_inventory_sha256 updated 2026-09-06 (D-NATIVE-06, native-ratified
    // transparent re-derivation): bg_yogas's writer was fixed (a dict-row-as-tuple
    // bug silently yielded 0 corpus-extracted yogas on every real dispatch), which
    // changes bg_yogas's own writer digest and therefore the L0 aggregate. Verified
    // before this update: regenerating the writer-digest inventory changed exactly
    // one entry (bg_yogas); all other 35 frozen L0 writers' digests are
    // byte-identical to before, and this aggregate is not part of any per-asset
    // NirmanaAnalysisReceiptBase (see buildLayerReceipts in
    // nirmana-analysis-receipts.ts), so no other asset's already-accepted
    // analysis_digest is affected. convergence_commit and receipt_count are
    // unchanged -- this re-pin touches exactly the one value that changed.
    //
    // Updated again 2026-09-07 (issue #2122, F-D21/F-D23): bg_vidhi_primitives.py's
    // from_moon_view entry corrected (inert reference_point arg -> the real
    // ganita_transit_anchors_get consumer). Same discipline: regenerating the
    // inventory changed exactly one entry (bg_vidhi_primitives); all other 35
    // frozen L0 writers (bg_yogas included) are byte-identical to the prior re-pin.
    expect(NIRMANA_L0_CONVERGENCE_COMMIT).toBe('49bb5c98b864a2cb2fee037cdb7f14f6892a8263')
    expect(NIRMANA_L0_WRITER_INVENTORY_SHA256)
      .toBe('5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178')
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
