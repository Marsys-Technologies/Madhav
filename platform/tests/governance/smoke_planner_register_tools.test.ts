/**
 * smoke_planner_register_tools.test.ts
 *
 * COV-S8 smoke gate: verifies that manifest_compressor.ts can read and project
 * the live CAPABILITY_MANIFEST.json after COV-S1's schema extension, and that
 * the per-entry `interface_version` field is structurally present as a string.
 *
 * This test does NOT check the specific value of interface_version so that
 * future bumps (e.g., "1.0" → "2.0") do not require test edits — only the
 * type contract is asserted.
 *
 * Audit reference: §G.8 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md (v1.2)
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  compressManifest,
  type CapabilityManifest,
} from '@/lib/pipeline/manifest_compressor'

function loadLiveManifest(): CapabilityManifest {
  const manifestPath = resolve(__dirname, '../../../00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  return JSON.parse(readFileSync(manifestPath, 'utf-8')) as CapabilityManifest
}

describe('COV-S8 — smoke: manifest version gate', () => {
  it('compressManifest returns an array', () => {
    const manifest = loadLiveManifest()
    const result = compressManifest(manifest)
    expect(Array.isArray(result)).toBe(true)
  })

  it('compressManifest returns at least one entry', () => {
    const manifest = loadLiveManifest()
    const result = compressManifest(manifest)
    expect(result.length).toBeGreaterThanOrEqual(1)
  })

  it('every compressed entry has a non-empty t (tool_name) string', () => {
    const manifest = loadLiveManifest()
    const result = compressManifest(manifest)
    for (const entry of result) {
      expect(typeof entry.t).toBe('string')
      expect(entry.t.length).toBeGreaterThan(0)
    }
  })

  it('manifest.entries array is present and non-empty', () => {
    const manifest = loadLiveManifest()
    expect(Array.isArray(manifest.entries)).toBe(true)
    expect(manifest.entries.length).toBeGreaterThan(0)
  })

  it('at least one manifest entry carries interface_version as a string', () => {
    const manifest = loadLiveManifest()
    const entriesWithVersion = manifest.entries.filter(
      (e) => 'interface_version' in e && typeof e['interface_version'] === 'string',
    )
    expect(entriesWithVersion.length).toBeGreaterThanOrEqual(1)
  })

  it('no manifest entry carries interface_version as a non-string (type consistency)', () => {
    const manifest = loadLiveManifest()
    const badEntries = manifest.entries.filter(
      (e) => 'interface_version' in e && typeof e['interface_version'] !== 'string',
    )
    expect(badEntries).toHaveLength(0)
  })
})
