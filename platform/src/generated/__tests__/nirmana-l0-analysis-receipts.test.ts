import { createHash } from 'node:crypto'
import { describe, expect, it } from 'vitest'
import writerDigestInventory from '../nirmana-writer-digests.json'
import {
  NIRMANA_L0_ANALYSIS_RECEIPT_COUNT,
  NIRMANA_L0_ANALYSIS_RECEIPTS,
  NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE,
  NIRMANA_L0_FROZEN_MANIFEST_SOURCE,
  NIRMANA_L0_WRITER_INVENTORY_SHA256,
} from '../nirmana-l0-analysis-receipts'

describe('generated Nirmana L0 analysis receipt bases', () => {
  it('preserves the durable source identifier without a lifecycle fixture mock', () => {
    expect(NIRMANA_L0_FROZEN_MANIFEST_SOURCE)
      .toBe('nirmana_elevation_campaign_definitions.manifest')
    for (const receipt of Object.values(NIRMANA_L0_ANALYSIS_RECEIPTS)) {
      expect(receipt.grounding.frozen_manifest_source).toBe(NIRMANA_L0_FROZEN_MANIFEST_SOURCE)
    }
  })

  // The §N.8 detector this convergence anchor never had: this is the same
  // aggregate computation assertNirmanaL0WriterInventoryMatchesConvergence
  // runs at import time (bg_* filter, locale sort, JSON.stringify, sha256),
  // reproduced here so a future writer edit that isn't accompanied by a
  // re-pinned NIRMANA_L0_WRITER_INVENTORY_SHA256 fails this test on the
  // offending PR -- not six days later as a silently closed gate discovered
  // only when something tries to use it in production.
  it('keeps the pinned writer-inventory digest in sync with the checked-in inventory', () => {
    const writers = writerDigestInventory.writers as Record<string, string>
    const l0Inventory = Object.fromEntries(Object.entries(writers)
      .filter(([assetId]) => assetId.startsWith('bg_'))
      .sort(([left], [right]) => left.localeCompare(right)))
    const computedDigest = createHash('sha256').update(JSON.stringify(l0Inventory)).digest('hex')
    expect(computedDigest).toBe(NIRMANA_L0_WRITER_INVENTORY_SHA256)
  })

  it('is available, with exactly the expected receipt count, when the pin matches', () => {
    expect(NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE).toBe(true)
    expect(Object.keys(NIRMANA_L0_ANALYSIS_RECEIPTS)).toHaveLength(NIRMANA_L0_ANALYSIS_RECEIPT_COUNT)
  })
})
