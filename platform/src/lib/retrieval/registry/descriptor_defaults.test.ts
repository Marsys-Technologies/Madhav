/**
 * descriptor_defaults.test.ts
 * =============================
 * CI gate for the R-1.1 descriptor migration (W2 "One Catalog", plan R-1
 * item 1). Proves the backfill in `descriptor_defaults.ts` — wired into
 * `catalog.ts`'s `getCatalog()` — actually reaches every live capability,
 * not just the ones this wave happened to spot-check.
 *
 * Loads the REAL, complete registered catalog via `getCatalog()` (the same
 * aggregator both the MCP and chat channels use — same pattern as
 * `chart_agnostic_gate_registry.test.ts`'s full-catalog block), not a
 * curated subset or a fixture.
 */
import { describe, it, expect } from 'vitest'
import { getCatalog } from './catalog'
import {
  __backfillClassificationTables as CLASSIFICATION,
  applyDescriptorDefaults,
} from './descriptor_defaults'
import type { CapabilityDescriptor } from './types'

describe('R-1.1 descriptor migration — universal field coverage', () => {
  it('getCatalog() returns the live ~118-capability registry (sanity bound, not a hardcoded exact count)', () => {
    const caps = getCatalog()
    expect(caps.length).toBeGreaterThanOrEqual(100)
  })

  it('every capability has a non-null annotations object with all four boolean sub-fields', () => {
    const caps = getCatalog()
    const missing = caps.filter((c) => c.annotations === undefined)
    expect(missing.map((c) => c.uri)).toEqual([])

    for (const cap of caps) {
      expect(cap.annotations, `${cap.uri} missing annotations`).toBeDefined()
      expect(typeof cap.annotations?.read_only).toBe('boolean')
      expect(typeof cap.annotations?.idempotent).toBe('boolean')
      expect(typeof cap.annotations?.destructive).toBe('boolean')
      expect(typeof cap.annotations?.open_world).toBe('boolean')
    }
  })

  it('every capability has a non-null boolean mutation field', () => {
    const caps = getCatalog()
    const missing = caps.filter((c) => c.mutation === undefined)
    expect(missing.map((c) => c.uri)).toEqual([])
    for (const cap of caps) {
      expect(typeof cap.mutation).toBe('boolean')
    }
  })

  it("every capability has a non-null data_source in {'stored','computed','hybrid'}", () => {
    const caps = getCatalog()
    const missing = caps.filter((c) => c.data_source === undefined)
    expect(missing.map((c) => c.uri)).toEqual([])
    for (const cap of caps) {
      expect(['stored', 'computed', 'hybrid']).toContain(cap.data_source)
    }
  })

  it('a mutation:true capability is never also data_source:stored-only-by-omission (both fields are always set together)', () => {
    // Regression guard: the three "universal" fields are set in the same
    // applyDescriptorDefaults() pass — this catches a future partial-apply bug.
    const caps = getCatalog()
    for (const cap of caps) {
      const universalFieldsSet =
        cap.annotations !== undefined && cap.mutation !== undefined && cap.data_source !== undefined
      expect(universalFieldsSet, `${cap.uri} has a partially-applied backfill`).toBe(true)
    }
  })

  it('mutation:true is NEVER paired with annotations.read_only:true (safety invariant — a write-capable capability must never be stamped read-only)', () => {
    // Regression for a real defect found by the W2 phase-1 verifier:
    // deriveAnnotations() originally ignored `mutation` entirely and
    // unconditionally returned read_only:true, so a future write-capable
    // capability with only `mutation` pre-set (and `annotations` left
    // undefined) would have been silently backfilled as read-only. This
    // test exercises applyDescriptorDefaults() directly against a synthetic
    // mutation:true fixture whose URI is in MUTATION_URIS — it does not
    // depend on any live capability actually being mutation:true today.
    const mutableMutationUris = CLASSIFICATION.MUTATION_URIS as unknown as Set<CapabilityDescriptor['uri']>
    const preexisting = Array.from(mutableMutationUris)
    const sampleMutationUri =
      preexisting[0] ?? ('marsys://tool/TEST/synthetic_mutation_fixture' as CapabilityDescriptor['uri'])
    const addedForTest = preexisting.length === 0
    if (addedForTest) mutableMutationUris.add(sampleMutationUri)
    try {
      const fixture = {
        uri: sampleMutationUri,
        name: 'synthetic_mutation_fixture',
        description: 'Synthetic fixture for the mutation/read_only coupling regression test.',
      } as CapabilityDescriptor
      applyDescriptorDefaults(fixture)
      expect(fixture.mutation).toBe(true)
      expect(fixture.annotations?.read_only).toBe(false)
      expect(fixture.annotations?.idempotent).toBe(false)
    } finally {
      if (addedForTest) mutableMutationUris.delete(sampleMutationUri)
    }
  })

  it('reports narrower (non-universal) field coverage honestly — no assertion of 100% where the plan does not require it', () => {
    const caps = getCatalog()
    const total = caps.length
    const withDisplay = caps.filter((c) => c.display !== undefined).length
    const withProjectionTags = caps.filter((c) => c.projection_tags !== undefined).length
    const withRegister = caps.filter((c) => c.register !== undefined).length
    const withFamilyOverrides = caps.filter((c) => c.family_overrides !== undefined).length

    // display: populated on every capability (mechanical derivation from
    // name/description always succeeds — no reason for a gap).
    expect(withDisplay).toBe(total)

    // projection_tags: narrower by design — the two internal-only channel
    // introspection tools are deliberately excluded (not applicable to any
    // projection). Everything else gets a tag set.
    expect(total - withProjectionTags).toBe(CLASSIFICATION.INTERNAL_INTROSPECTION_URIS.size)

    // register.glossary and family_overrides are deliberately NOT populated
    // this pass (genuine per-capability editorial work — see
    // descriptor_defaults.ts's module doc comment). Asserting zero here
    // documents that as an intentional, CI-visible gap rather than a silent
    // one — this assertion should FAIL (and force an update) the day a
    // future editorial wave starts populating either field.
    expect(withRegister).toBe(0)
    expect(withFamilyOverrides).toBe(0)
  })

  it('mutation:true is set only for capabilities backed by real write-capable code (currently: none in the registry)', () => {
    // Honesty check, not a permanent invariant: a repo-wide grep for direct
    // SQL writes (INSERT/UPDATE/DELETE) across the registry layer tree found
    // zero hits at migration time (2026-07-20) — see descriptor_defaults.ts's
    // MUTATION_URIS doc comment for the important caveat (the real
    // write-capable surface, /api/mcp/writes/[action], is NOT one of the 118
    // registry capabilities). If a future capability legitimately becomes
    // mutation:true, this test's job is to make that change visible in a
    // diff, not to forbid it — update the expected count deliberately.
    const caps = getCatalog()
    const mutationTrue = caps.filter((c) => c.mutation === true)
    expect(mutationTrue.map((c) => c.uri)).toEqual([])
  })

  it('calibration_context_only is applied narrowly (F-R7: single-digit, not over-applied)', () => {
    const caps = getCatalog()
    const flagged = caps.filter((c) => c.calibration_context_only === true).map((c) => c.uri).sort()
    expect(flagged).toEqual(['marsys://tool/L5/lel_query', 'marsys://tool/L5/query_predictions'])
  })
})
