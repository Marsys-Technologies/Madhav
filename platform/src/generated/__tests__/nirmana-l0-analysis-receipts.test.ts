import { describe, expect, it } from 'vitest'
import {
  NIRMANA_L0_ANALYSIS_RECEIPTS,
  NIRMANA_L0_FROZEN_MANIFEST_SOURCE,
} from '../nirmana-l0-analysis-receipts'

describe('generated Nirmana L0 analysis receipt bases', () => {
  it('preserves the durable source identifier without a lifecycle fixture mock', () => {
    expect(NIRMANA_L0_FROZEN_MANIFEST_SOURCE)
      .toBe('nirmana_elevation_campaign_definitions.manifest')
    for (const receipt of Object.values(NIRMANA_L0_ANALYSIS_RECEIPTS)) {
      expect(receipt.grounding.frozen_manifest_source).toBe(NIRMANA_L0_FROZEN_MANIFEST_SOURCE)
    }
  })
})
