import { describe, it, expect } from 'vitest'
import { deriveManifest } from '../auto_deriver'

describe('deriveManifest', () => {
  it('returns entries for L1, L2.5, L3 files', async () => {
    const entries = await deriveManifest()
    expect(entries.length).toBeGreaterThan(10)
  })

  it('FORENSIC entry has correct fields', async () => {
    const entries = await deriveManifest()
    // Find the forensic entry by path
    const forensic = entries.find(e => e.path.includes('FORENSIC_ASTROLOGICAL_DATA_v8_0'))
    expect(forensic).toBeDefined()
    expect(forensic!.expose_to_chat).toBe(true)
    expect(forensic!.native_id).toBe('abhisek')
    expect(forensic!.layer).toBe('L1')
    expect(forensic!.fingerprint).toHaveLength(64)
  })

  it('all entries have required fields', async () => {
    const entries = await deriveManifest()
    for (const entry of entries) {
      expect(entry.canonical_id).toBeTruthy()
      expect(entry.path).toBeTruthy()
      expect(entry.fingerprint).toHaveLength(64)
      expect(entry.interface_version).toBe('1.0')
    }
  })

  it('MSR entry has expose_to_chat true', async () => {
    const entries = await deriveManifest()
    const msr = entries.find(e => e.path.includes('MSR_v5_0'))
    expect(msr).toBeDefined()
    expect(msr!.expose_to_chat).toBe(true)
  })
})
