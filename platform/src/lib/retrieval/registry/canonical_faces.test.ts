/**
 * canonical_faces.test.ts — D-2 Lane V-3, ledger row 22 (CR-30 dedup).
 *
 * Validates the authored canonical-face list that V-0's alias_check.ts consumes
 * (platform/scripts/audit/doctrine_harness/lib/alias_check.ts). Asserts the file matches the
 * documented interface { canonical_faces: string[], deprecated_aliases: Record<string,string> }
 * and reconciles internally: every deprecated alias's canonical target exists in canonical_faces,
 * no name is both canonical and deprecated, and the union covers the 144 census tools with no orphans.
 * (D-4a Lane A-0: 135 -> 138 — plan_retrieval, reading_notes_get, scan_fetch_signals were
 * previously unaccounted; added to canonical_faces so census == canonical list again.)
 * (RC-14 2026-07-23: 138 -> 144 — the 6 DEFERRED tools were renamed at source; their OLD names
 * moved from canonical_faces into deprecated_aliases (kept for web-channel replay), a net +6 to
 * the union since each old name now coexists with its new canonical face.)
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
// Read-only import of V-0's consumer to prove the row-4 reconcile end-to-end (their glob; not edited).
import { checkAliasCount } from '../../../../scripts/audit/doctrine_harness/lib/alias_check.js'

const FILE = path.resolve(process.cwd(), 'src/lib/retrieval/registry/canonical_faces.json')
const parsed = JSON.parse(readFileSync(FILE, 'utf-8')) as {
  canonical_faces: string[]
  deprecated_aliases: Record<string, string>
}

describe('canonical_faces.json — V-0 alias_check contract', () => {
  it('matches the CanonicalFacesFile interface', () => {
    expect(Array.isArray(parsed.canonical_faces)).toBe(true)
    expect(typeof parsed.deprecated_aliases).toBe('object')
  })

  it('every deprecated alias maps to a canonical face that exists (no orphan twins)', () => {
    const canon = new Set(parsed.canonical_faces)
    const orphans = Object.entries(parsed.deprecated_aliases).filter(([, c]) => !canon.has(c))
    expect(orphans).toEqual([])
  })

  it('no name is both canonical and a deprecated alias key', () => {
    const canon = new Set(parsed.canonical_faces)
    const overlap = Object.keys(parsed.deprecated_aliases).filter((a) => canon.has(a))
    expect(overlap).toEqual([])
  })

  it('canonical faces are unique', () => {
    expect(new Set(parsed.canonical_faces).size).toBe(parsed.canonical_faces.length)
  })

  it('accounts for all 144 census tools (canonical ∪ deprecated = census), no unaccounted', () => {
    const union = new Set([...parsed.canonical_faces, ...Object.keys(parsed.deprecated_aliases)])
    expect(union.size).toBe(144)
  })

  it('V-0 checkAliasCount reconciles against the 144-tool census (row-4 green, source=v3)', () => {
    const census = [...parsed.canonical_faces, ...Object.keys(parsed.deprecated_aliases)]
      .map((name) => ({ name, description: '' }))
    const result = checkAliasCount(census)
    expect(result.source).toBe('v3_canonical_face_list')
    expect(result.reconciles).toBe(true)
    expect(result.orphan_twins).toEqual([])
    expect(result.unaccounted_tools).toEqual([])
  })
})
