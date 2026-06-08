import { describe, it, expect } from 'vitest'
import { deriveManifest } from '../auto_deriver'

describe('deriveManifest', () => {
  it('returns entries for L1, L2.5, L3 files', async () => {
    const entries = await deriveManifest()
    expect(entries.length).toBeGreaterThan(10)
  })

  // FORENSIC v8.0 markdown deleted in PR #187; no longer in any SCAN_DIRS directory.
  // Live FORENSIC source = chart_facts DB table via forensic_render.ts.

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
