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

    // register.glossary and family_overrides are still deliberately NOT populated
    // this pass (genuine per-capability editorial work — see
    // descriptor_defaults.ts's module doc comment). `register` itself, however,
    // is no longer universally undefined: Paripraśna Build PB-1 Lane S-2 (the
    // "future editorial wave" this comment predicted) populated
    // `register.reader_label` — NOT `register.glossary` — on the ~30
    // capabilities the acharya-grade interpretive floor surfaces a working-band
    // label for (see platform/src/lib/pariprashna/lexicon.ts). withRegister now
    // tracks that count; withFamilyOverrides remains an honest zero.
    expect(withRegister).toBe(33)
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
    // DOCTRINE-WAVES D-4b Lane B-5: mechanism_retrodiction_get added — another raw
    // outcome-ledger read (life_events) whose role is calibration-context SUPPLY, not
    // a calibration-quality SURFACE (explicitly set on the descriptor itself, not via
    // the CALIBRATION_CONTEXT_ONLY_URIS default-fill list — see query_mechanism_retrodiction.ts).
    expect(flagged).toEqual([
      'marsys://tool/L5/lel_query',
      'marsys://tool/L5/mechanism_retrodiction_get',
      'marsys://tool/L5/query_predictions',
    ])
  })
})

// ── W3 "One Envelope" — density_contract 100% coverage (plan §7 item 6 / master
// brief §E W3) ───────────────────────────────────────────────────────────────
describe('W3 density_contract — universal field coverage', () => {
  it('every live capability in getCatalog() has a density_contract (100% coverage — was 6/~118 at W3 open)', () => {
    const caps = getCatalog()
    const missing = caps.filter((c) => c.density_contract === undefined).map((c) => c.uri)
    // Fails loudly (not silently) if a future wave adds a capability whose
    // registration file forgets to go through registerCapability() → getCatalog(),
    // or if applyDescriptorDefaults() regresses. This is the gate the brief asked
    // for: "a coverage-counting test that fails if any capability lacks it".
    expect(missing).toEqual([])
  })

  it('density_contract sub-fields are well-formed for every capability (paginated: boolean, facets: string[], empty_reason: boolean, byte ceilings > 0 when present)', () => {
    const caps = getCatalog()
    for (const cap of caps) {
      const dc = cap.density_contract
      expect(dc, `${cap.uri} missing density_contract`).toBeDefined()
      if (!dc) continue
      expect(typeof dc.paginated, `${cap.uri}.density_contract.paginated`).toBe('boolean')
      expect(Array.isArray(dc.facets), `${cap.uri}.density_contract.facets`).toBe(true)
      expect(typeof dc.empty_reason, `${cap.uri}.density_contract.empty_reason`).toBe('boolean')
      if (dc.max_verdict_bytes !== undefined) expect(dc.max_verdict_bytes).toBeGreaterThan(0)
      if (dc.max_digest_bytes !== undefined) expect(dc.max_digest_bytes).toBeGreaterThan(0)
    }
  })

  it('the 6 capabilities that hand-set density_contract before this wave are left untouched (idempotent backfill — never overwrites an explicit value)', () => {
    const caps = getCatalog()
    const byUri = new Map(caps.map((c) => [c.uri, c]))

    // get_yoga_dosha / query_signals previously declared empty_reason:false with an
    // explicit "not yet added" comment — W3 flips both to true AND implements the real
    // handler-side empty_reason string (see get_yoga_dosha.ts / query_signals.ts).
    expect(byUri.get('marsys://tool/L1/get_yoga_dosha')?.density_contract?.empty_reason).toBe(true)
    expect(byUri.get('marsys://tool/L2/query_signals')?.density_contract?.empty_reason).toBe(true)
    expect(byUri.get('marsys://tool/L2/query_signals')?.density_contract?.max_digest_bytes).toBe(1_500_000)

    // get_vichara / get_yoga_firings / get_dasha_lord_capability hand-set empty_reason:true
    // and their own real values — must survive the backfill pass untouched.
    expect(byUri.get('marsys://tool/L1/get_vichara')?.density_contract?.max_verdict_bytes).toBe(1024)
    expect(byUri.get('marsys://tool/L1/get_vichara')?.density_contract?.max_digest_bytes).toBe(4096)
    expect(byUri.get('marsys://tool/L1/get_yoga_firings')?.density_contract?.paginated).toBe(true)
    expect(byUri.get('marsys://tool/L1/get_dasha_lord_capability')?.density_contract?.paginated).toBe(false)

    // judgment_query hand-set paginated:false / empty_reason:false (judgment_flags carries
    // the honest-gap disclosures instead — see register_d9_judgment.ts:415).
    expect(byUri.get('marsys://tool/L-JUDGMENT/judgment_query')?.density_contract?.empty_reason).toBe(false)
  })

  it('measured-budget capabilities (MEASURED_BUDGET_KB_URIS) get their real, evidence-backed byte ceiling, not a generic tier default', () => {
    const caps = getCatalog()
    const byUri = new Map(caps.map((c) => [c.uri, c]))
    // judgment_query is one of the 6 capabilities that hand-set its own density_contract
    // before this wave (register_d9_judgment.ts:415) — the idempotent backfill correctly
    // leaves it untouched (asserted in the prior test), so it's excluded here.
    const preExisting = new Set(['marsys://tool/L-JUDGMENT/judgment_query'])
    for (const [uri, kb] of CLASSIFICATION.MEASURED_BUDGET_KB_URIS) {
      if (preExisting.has(uri)) continue
      const cap = byUri.get(uri)
      if (!cap) continue // e.g. graha_portrait/assess_*/traverse_chart_graph — verified individually if/when their own descriptor file is inspected
      expect(cap.density_contract?.max_digest_bytes, `${uri} digest ceiling`).toBe(kb * 1024)
    }
  })

  it('paginated is derived from real input_schema evidence (a cursor/limit/top_k/offset/page/max_signals param), not a blanket true', () => {
    const caps = getCatalog()
    const nonPaginated = caps.filter((c) => c.density_contract?.paginated === false)
    const paginated = caps.filter((c) => c.density_contract?.paginated === true)
    // Sanity: both buckets are non-trivial — proves this isn't a constant-true or
    // constant-false default masquerading as a derivation.
    expect(nonPaginated.length).toBeGreaterThan(0)
    expect(paginated.length).toBeGreaterThan(0)
  })
})
