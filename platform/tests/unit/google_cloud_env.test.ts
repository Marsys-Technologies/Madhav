import { describe, expect, it } from 'vitest'
import { readGoogleCloudEnv } from '@/lib/config/google_cloud_env'

describe('readGoogleCloudEnv', () => {
  it('reads canonical project and billing bindings', () => {
    expect(readGoogleCloudEnv('GOOGLE_CLOUD_PROJECT', { GOOGLE_CLOUD_PROJECT: 'canonical' })).toBe('canonical')
    expect(readGoogleCloudEnv('GOOGLE_CLOUD_BILLING_DATASET_ID', {
      GOOGLE_CLOUD_BILLING_DATASET_ID: 'billing',
    })).toBe('billing')
  })

  it('retains the deployed value when both names are set', () => {
    expect(readGoogleCloudEnv('GOOGLE_CLOUD_REGION', {
      GCP_REGION: 'legacy',
      GOOGLE_CLOUD_REGION: 'canonical',
    })).toBe('legacy')
  })

  it('preserves an explicitly empty legacy binding and distinguishes absence', () => {
    expect(readGoogleCloudEnv('GOOGLE_CLOUD_PROJECT', { GCP_PROJECT: '' })).toBe('')
    expect(readGoogleCloudEnv('GOOGLE_CLOUD_PROJECT', {})).toBeUndefined()
  })
})
