import { describe, expect, it } from 'vitest'
import { readGoogleCloudEnv } from '@/lib/config/google_cloud_env'

const aliasPairs = [
  ['GOOGLE_CLOUD_PROJECT', 'GCP_PROJECT'],
  ['GOOGLE_CLOUD_REGION', 'GCP_REGION'],
  ['GOOGLE_CLOUD_BILLING_PROJECT_ID', 'GCP_BILLING_PROJECT_ID'],
  ['GOOGLE_CLOUD_BILLING_DATASET_ID', 'GCP_BILLING_DATASET_ID'],
  ['GOOGLE_CLOUD_BILLING_TABLE_ID', 'GCP_BILLING_TABLE_ID'],
] as const

const resolutionCases = [
  ['both undefined', undefined, undefined, undefined],
  ['canonical only', undefined, 'canonical', 'canonical'],
  ['legacy only', 'legacy', undefined, 'legacy'],
  ['equal bindings', 'same', 'same', 'same'],
  ['conflicting bindings', 'legacy', 'canonical', 'legacy'],
  ['empty legacy with canonical', '', 'canonical', ''],
  ['legacy with empty canonical', 'legacy', '', 'legacy'],
  ['both empty', '', '', ''],
  ['empty canonical only', undefined, '', ''],
  ['empty legacy only', '', undefined, ''],
] as const

describe.each(aliasPairs)('readGoogleCloudEnv %s', (canonical, legacy) => {
  it('distinguishes absent bindings from empty values', () => {
    expect(readGoogleCloudEnv(canonical, {})).toBeUndefined()
  })

  it.each(resolutionCases)('%s', (_name, legacyValue, canonicalValue, expected) => {
    expect(readGoogleCloudEnv(canonical, {
      [legacy]: legacyValue,
      [canonical]: canonicalValue,
    })).toBe(expected)
  })
})
