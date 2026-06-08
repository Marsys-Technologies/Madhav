import { describe, it, expect } from 'vitest'
import { mergeOverrides } from '../override_merger'
import type { AssetEntry } from '../auto_deriver'

describe('mergeOverrides', () => {
  it('applies always_required to FORENSIC', async () => {
    const base: AssetEntry[] = [{
      canonical_id: 'FORENSIC',
      path: '99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md',

      version: '8.0',
      status: 'CURRENT',
      layer: 'L1',
      expose_to_chat: true,
      representations: ['file'],
      interface_version: '1.0',
      fingerprint: 'abc123',
      native_id: 'abhisek',
    }]
    const result = await mergeOverrides(base)
    expect(result[0].always_required).toBe(true)
    expect(result[0].preferred_for).toContain('factual')
  })

  it('passes through entries with no override', async () => {
    const base: AssetEntry[] = [{
      canonical_id: 'SOME_RANDOM_ID',
      path: 'test/file.md',
      version: '1.0',
      status: 'CURRENT',
      layer: 'L1',
      expose_to_chat: true,
      representations: ['file'],
      interface_version: '1.0',
      fingerprint: 'abc123',
      native_id: 'abhisek',
    }]
    const result = await mergeOverrides(base)
    expect(result[0].canonical_id).toBe('SOME_RANDOM_ID')
    expect(result[0].always_required).toBeUndefined()
  })
})
