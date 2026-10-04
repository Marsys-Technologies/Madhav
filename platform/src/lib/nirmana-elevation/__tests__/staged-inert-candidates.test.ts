import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import {
  canonicalRegistryContractDigest,
  registryContractFingerprintInput,
  assertManifestMatchesRegistry,
  assertManifestMatchesRegistryIdentity,
  excludeNirmanaStagedInertCandidates,
  assertStagedInertCandidateRules,
  excludedNirmanaStagedInertCandidates,
  isNirmanaStagedInertCandidate,
  type NirmanaStagedInertCandidateRule,
  NIRMANA_STAGED_INERT_CANDIDATE_RULES,
  NIRMANA_STAGED_INERT_CANDIDATES,
  runtimeEvidenceSql,
  type NirmanaRegistryContractRow,
} from '../definitions'
import { buildNirmanaBaselineCandidate, classifyNirmanaDivergence } from '../monitor'

/**
 * PRAVĀHA #2996 (migration 1243) — the two staged inert Gochara candidates (ka_gochara_v4_41_candidate, ka_gochara_v5) hold asset_registry rows only
 * so the orchestrator's writer-gap pre-flight finds a row for every registered writer. They are excluded from the Nirmāṇa frozen population by ONE
 * shape-conditioned rule (Suvarṇa's conditions): inert shape AND positively no receipt / build-run evidence; never "all inactive".
 * Both directions are asserted: inert ⇒ excluded and the monitor is healthy; any change of shape ⇒ NOT excluded and the monitor sees the row.
 */
const V41 = 'ka_gochara_v4_41_candidate'
const V5 = 'ka_gochara_v5'
const V3 = 'ka_gochara_v3_century_materialize'
/** The rule-entry defaults the validation tests start from (every per-id field explicit). */
const BASE_RULE = { declaredDependsOn: [] as string[], emptyDependsOnAllowed: true, testTriggers: [] as string[], evidenceCutoff: null, dependents: 'none' as const }

function registryRow(asset_id: string, overrides: Partial<NirmanaRegistryContractRow> = {}): NirmanaRegistryContractRow {
  return {
    asset_id, layer: 'brahmagyan', depends_on: [], sort_order: 1, scope: 'global', asset_kind: 'data', catalog_status: 'CURRENT', is_active: true, has_writer: true,
    target_table: `${asset_id}_rows`, count_sql: `SELECT count(*) FROM ${asset_id}_rows`, integrity_check_sql: null, health_probe: null, natural_key_partition: null,
    superseded_by: null, data_disposition: null, dead_flag: null, sanskrit_name: null, english_name: null, english_description: null, ...overrides,
  }
}

/** A staged candidate exactly as migration 1243 leaves it (and as the loaders read it: has_non_test_runtime_evidence = false). */
const staged = (id: string, over: Partial<NirmanaRegistryContractRow> = {}) => registryRow(id, {
  layer: 'kala', sort_order: id === V5 ? 142 : 141, scope: 'per_chart', is_active: false, has_writer: true, depends_on: [], has_non_test_runtime_evidence: false,
  target_table: 'kala_gochara_windows', ...over,
})

/** The existing frozen population: ordinary assets, a dependent pair, and an already RETIRED identity (inactive, has a writer, no dependencies — the lookalike). */
const population: NirmanaRegistryContractRow[] = [
  registryRow('bg_reference', { sort_order: 1 }),
  registryRow('bg_texts', { sort_order: 2, depends_on: ['bg_reference'] }),
  registryRow('ka_gochara_sweep', { layer: 'kala', sort_order: 90, is_active: false, catalog_status: 'RETIRED', superseded_by: 'bg_reference', data_disposition: 'RETAINED_AS_CAPITAL', has_non_test_runtime_evidence: false }),
]
const frozen = () => buildNirmanaBaselineCandidate(population)
const definition = (c = frozen()) => ({ definition_status: 'frozen' as const, manifest: c.manifest, manifest_sha256: c.manifest_sha256 })

describe('staged inert Gochara candidates — excluded while inert, visible the moment the shape changes', () => {
  it('the rule names exactly the three ids (the two staged candidates and, from N-138, the retirement-pending v3 century writer)', () => {
    expect([...NIRMANA_STAGED_INERT_CANDIDATES].sort()).toEqual([V3, V41, V5])
  })

  it('INERT ⇒ excluded: the baseline equals the frozen population, both frozen-registry comparisons pass, and the monitor reads in_sync', () => {
    const withBoth = [...population, staged(V41), staged(V5)]
    expect(buildNirmanaBaselineCandidate(withBoth)).toEqual(frozen())
    const candidate = frozen()
    expect(() => assertManifestMatchesRegistryIdentity(candidate.manifest, withBoth)).not.toThrow()
    expect(() => assertManifestMatchesRegistry(candidate.manifest, withBoth)).not.toThrow()
    expect(classifyNirmanaDivergence({ definition: definition(candidate), candidate: buildNirmanaBaselineCandidate(withBoth), observation: null }))
      .toMatchObject({ status: 'in_sync', affected_asset_ids: [] })
  })

  it('WITHOUT the rule the two rows break it — the reproduced defect (the rows ARE rejected as unresolved when not excluded)', () => {
    const notInert = [...population, staged(V41, { has_non_test_runtime_evidence: true }), staged(V5, { has_non_test_runtime_evidence: true })]
    expect(() => buildNirmanaBaselineCandidate(notInert)).toThrow()                                    // assertFreezableManifest: execution_obligation 'unresolved'
    expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, notInert)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 5/)
  })

  it.each([
    ['activated', { is_active: true }],
    ['gains a dependency', { depends_on: ['bg_reference'] }],
    ['has receipt / build-run evidence from a NON-test run (or a run that cannot be found)', { has_non_test_runtime_evidence: true }],
    ['the loader gave no evidence column', { has_non_test_runtime_evidence: undefined }],
    ['the evidence column is NULL (unknown)', { has_non_test_runtime_evidence: null }],
    ['lost its writer', { has_writer: false }],
    ['is RETIRED', { catalog_status: 'RETIRED' as const }],
  ])('v5 %s ⇒ NOT excluded, and the monitor sees it', (_name, over) => {
    const row = staged(V5, over as Partial<NirmanaRegistryContractRow>)
    expect(isNirmanaStagedInertCandidate(row)).toBe(false)
    expect(excludeNirmanaStagedInertCandidates([row])).toEqual([row])
    // the frozen comparisons now report the extra identity (the denominator view contains it)
    expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, [...population, row])).toThrow(/Frozen manifest contains 3 assets but the live registry contains 4/)
    expect(() => assertManifestMatchesRegistry(frozen().manifest, [...population, row])).toThrow(/Frozen manifest contains 3 assets but the live registry contains 4/)
  })

  it('an ACTIVE v5 in the baseline changes the candidate (the monitor classifies it as divergent, not in_sync)', () => {
    const active = staged(V5, { is_active: true, has_non_test_runtime_evidence: false, depends_on: ['bg_reference'] })
    const candidate = buildNirmanaBaselineCandidate([...population, staged(V41), active])
    expect(candidate.manifest.assets.map((a) => a.asset_id)).toContain(V5)
    expect(candidate.manifest.assets.map((a) => a.asset_id)).not.toContain(V41)                           // the still-inert one stays excluded
    expect(classifyNirmanaDivergence({ definition: definition(), candidate, observation: null }).status).not.toBe('in_sync')
  })

  it('a dependent asset makes the candidate part of the live DAG: it is NOT excluded', () => {
    const dependent = registryRow('bg_depends_on_v41', { depends_on: [V41], sort_order: 5 })
    const rows = excludeNirmanaStagedInertCandidates([staged(V41), dependent])
    expect(rows.map((r) => r.asset_id)).toEqual([V41, 'bg_depends_on_v41'])
  })

  it('NO broad inactive exclusion: an existing RETIRED identity is still in the baseline, and any other inactive asset survives the filter', () => {
    const candidate = buildNirmanaBaselineCandidate([...population, staged(V41), staged(V5)])
    const ids = candidate.manifest.assets.map((a) => a.asset_id)
    expect(ids).toContain('ka_gochara_sweep')                  // RETIRED: stays in the frozen population
    expect(ids).not.toContain(V41)
    expect(ids).not.toContain(V5)
    const dormant = registryRow('bg_dormant', { is_active: false, has_non_test_runtime_evidence: false })
    expect(excludeNirmanaStagedInertCandidates([...population, dormant, staged(V41)]).map((r) => r.asset_id)).toEqual(['bg_reference', 'bg_texts', 'ka_gochara_sweep', 'bg_dormant'])
    expect(isNirmanaStagedInertCandidate(population[2])).toBe(false)
    expect(isNirmanaStagedInertCandidate(dormant)).toBe(false)
  })

  it('DIGEST STABILITY: the new column enters no digest — a 128-row frozen population is byte-identical with and without has_non_test_runtime_evidence', () => {
    const rows128: NirmanaRegistryContractRow[] = Array.from({ length: 128 }, (_, i) => registryRow(`bg_asset_${String(i).padStart(3, '0')}`, {
      sort_order: i + 1, depends_on: i === 0 ? [] : [`bg_asset_${String(i - 1).padStart(3, '0')}`],
    }))
    const withColumn = rows128.map((r, i) => ({ ...r, has_non_test_runtime_evidence: i % 2 === 0 }))            // present, with varying values
    const withoutColumn = rows128.map((r) => ({ ...r }))                                                // absent
    for (let i = 0; i < 128; i++) {
      expect(registryContractFingerprintInput(withColumn[i])).toEqual(registryContractFingerprintInput(withoutColumn[i]))
      expect(canonicalRegistryContractDigest(registryContractFingerprintInput(withColumn[i])))
        .toBe(canonicalRegistryContractDigest(registryContractFingerprintInput(withoutColumn[i])))
    }
    const a = buildNirmanaBaselineCandidate(withColumn)
    const b = buildNirmanaBaselineCandidate(withoutColumn)
    expect(a.manifest.assets).toHaveLength(128)
    expect(JSON.stringify(a)).toBe(JSON.stringify(b))                                                    // manifest, labels and all four digests, byte for byte
    expect(JSON.stringify(a)).not.toContain('has_non_test_runtime_evidence')
  })

  it('ONE predicate: receipts OR build_run_assets that are NOT test-run evidence, only for the two ids (NULL otherwise); NO asset_throughput and NO function call', () => {
    const sql = runtimeEvidenceSql('registry')
    expect(sql).toContain("registry.asset_id IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5')")
    expect(sql).toContain('FROM public.asset_provenance_receipts rcpt WHERE rcpt.asset_id = registry.asset_id')
    expect(sql).toContain('FROM public.build_run_assets bra WHERE bra.asset_id = registry.asset_id')
    expect(sql).toContain('br.id = rcpt.build_id AND br.triggered_by = ANY')                       // a receipt is attributed to its run through build_id …
    expect(sql).toContain('br.id = bra.run_id AND br.triggered_by = ANY')                          // … a build_run_assets row through run_id
    expect(sql).toContain("WHEN 'ka_gochara_v5' THEN ARRAY['gochara-v5-small-test']::text[] ELSE ARRAY[]::text[] END")   // v5's declared test trigger; every other id: none
    expect(sql).not.toContain("'ka_gochara_v4_41_candidate' THEN")                                  // v4.1 declares no test trigger: ANY evidence is non-test
    expect(sql).toMatch(/AS has_non_test_runtime_evidence$/)
    expect(sql).not.toContain('asset_throughput')                                     // the control and ingress writers hold no SELECT on it; a refresh row is not a build
    expect(sql).not.toContain('ka_gochara_staged_candidate_has_runtime_evidence')     // the SECURITY DEFINER function is a LATER protected migration (draft)
  })

  it('the SQL equals the golden text the python 1243 test runs against a real PostgreSQL (one fixture, two readers: no drift)', () => {
    const golden = readFileSync(path.resolve(__dirname, 'fixtures/runtime_evidence_sql.golden.txt'), 'utf8').replace(/\n$/, '')
    expect(runtimeEvidenceSql('{a}')).toBe(golden)
  })

  it('EVERY registry loader (monitor, snapshot, and all five definitions loaders) selects the evidence column — one predicate everywhere', () => {
    const dir = path.resolve(__dirname, '..')
    const loaders: Array<[string, number]> = [['monitor.ts', 1], ['snapshot.ts', 1], ['definitions.ts', 5]]
    for (const [file, expected] of loaders) {
      const source = readFileSync(path.join(dir, file), 'utf8')
      const selects = [...source.matchAll(/SELECT[^`]*?dead_flag[^`]*?FROM asset_registry\b(?! registry)/g)].map((m) => m[0])
      expect(selects, file).toHaveLength(expected)
      for (const select of selects) expect(select, `${file}: ${select.slice(0, 60)}`).toContain("runtimeEvidenceSql('asset_registry')")
    }
  })

  describe('R20-2 — the candidate rule sees the COMPLETE registry before supporting writers are removed (actual callers)', () => {
    const grounding = (active: boolean, dependsOn: string[] = []) => registryRow('bo_grounding', { layer: 'bodha', sort_order: 25, catalog_status: 'DRAFT', is_active: active, depends_on: dependsOn })
    it.each([[V41, true], [V41, false], [V5, true], [V5, false]])('bo_grounding depending on %s (active=%s) keeps the candidate in the denominator: NOT excluded in the baseline or either comparison', (id, active) => {
      const rows = [...population, staged(id as string), grounding(active as boolean, [id as string])]
      expect(excludeNirmanaStagedInertCandidates(rows).map((r) => r.asset_id)).toContain(id)
      expect(() => buildNirmanaBaselineCandidate(rows)).toThrow()                                            // the candidate stays in the denominator ⇒ 'unresolved' ⇒ fails closed
      expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, rows)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 4/)
      expect(() => assertManifestMatchesRegistry(frozen().manifest, rows)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 4/)
    })
    it('a bo_grounding with NO dependency on a candidate stays OUT of the denominator and the inert candidates stay excluded', () => {
      const rows = [...population, staged(V41), staged(V5), grounding(true)]
      expect(buildNirmanaBaselineCandidate(rows)).toEqual(frozen())
      expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, rows)).not.toThrow()
      expect(() => assertManifestMatchesRegistry(frozen().manifest, rows)).not.toThrow()
      expect(buildNirmanaBaselineCandidate(rows).manifest.assets.map((a) => a.asset_id)).not.toContain('bo_grounding')
    })
    it('retired identities are retained alongside', () => {
      expect(buildNirmanaBaselineCandidate([...population, staged(V41), grounding(true)]).manifest.assets.map((a) => a.asset_id)).toContain('ka_gochara_sweep')
    })
  })
  // ── N-137 (Suvarṇa): v5 carries its TRUTHFUL dependencies and a declared test trigger; one rule for both ids ─────────────────────────────────────────
  describe('N-137 — the rule: inert, not retired, declared dependencies (or none), evidence only from declared test runs, nothing depends on it', () => {
    const PAIR = ['ga_positions', 'ga_dashas']
    const v5truthful = (over: Partial<NirmanaRegistryContractRow> = {}) => staged(V5, { depends_on: PAIR, ...over })

    it('the rule table: v5 = exactly the pair + the small-test trigger + decision N-137; v4.1 = no dependencies, no test trigger', () => {
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V5)).toEqual({ declaredDependsOn: ['ga_dashas', 'ga_positions'], emptyDependsOnAllowed: true, testTriggers: ['gochara-v5-small-test'], evidenceCutoff: null, dependents: 'none', reason: 'unsealed test candidate', decision: 'N-137' })
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V41)).toMatchObject({ declaredDependsOn: [], testTriggers: [] })
    })

    it('v5 with the truthful dependency pair (any order) and no non-test evidence is EXCLUDED: the baseline equals the frozen population and the monitor reads in_sync', () => {
      for (const deps of [PAIR, [...PAIR].reverse()]) {
        const rows = [...population, v5truthful({ depends_on: deps })]
        expect(isNirmanaStagedInertCandidate(rows[3])).toBe(true)
        expect(buildNirmanaBaselineCandidate(rows)).toEqual(frozen())
        expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, rows)).not.toThrow()
        expect(() => assertManifestMatchesRegistry(frozen().manifest, rows)).not.toThrow()
        expect(classifyNirmanaDivergence({ definition: definition(), candidate: buildNirmanaBaselineCandidate(rows), observation: null })).toMatchObject({ status: 'in_sync' })
      }
    })

    it('v5 with EMPTY dependencies (today\'s registry, before migration 1304) is excluded exactly as before', () => {
      expect(isNirmanaStagedInertCandidate(staged(V5))).toBe(true)
      expect(buildNirmanaBaselineCandidate([...population, staged(V5)])).toEqual(frozen())
    })

    // The mutation cases: each is a state the rule must refuse to hide — the row counts as a normal asset again and the baseline / comparisons THROW (fail closed).
    it.each([
      ['a NON-test evidence row (or one whose run is gone)', { has_non_test_runtime_evidence: true }],
      ['is_active true', { is_active: true }],
      ['an EXTRA dependency', { depends_on: [...PAIR, 'bg_reference'] }],
      ['a MISSING dependency (one of the pair)', { depends_on: ['ga_dashas'] }],
      ['a DIFFERENT dependency', { depends_on: ['ga_dashas', 'bg_reference'] }],
      ['a DUPLICATED dependency', { depends_on: ['ga_dashas', 'ga_dashas', 'ga_positions'] }],
      ['the evidence column unknown (null)', { has_non_test_runtime_evidence: null }],
      ['the evidence column absent', { has_non_test_runtime_evidence: undefined }],
    ])('MUTATION — v5 with %s ⇒ NOT excluded, visible to the monitor, and the baseline / comparisons throw', (_name, over) => {
      const row = v5truthful(over as Partial<NirmanaRegistryContractRow>)
      const rows = [...population, row]
      expect(isNirmanaStagedInertCandidate(row)).toBe(false)
      expect(excludeNirmanaStagedInertCandidates(rows).map((r) => r.asset_id)).toContain(V5)
      expect(excludedNirmanaStagedInertCandidates(rows)).toEqual([])
      expect(() => buildNirmanaBaselineCandidate(rows)).toThrow()                                                     // fails closed (an unresolved asset in the denominator)
      expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, rows)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 4/)
      expect(() => assertManifestMatchesRegistry(frozen().manifest, rows)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 4/)
    })

    it('v4.1 keeps its current rule through the same structure: no dependencies allowed (even v5\'s pair), and ANY evidence is non-test evidence', () => {
      expect(isNirmanaStagedInertCandidate(staged(V41))).toBe(true)
      expect(isNirmanaStagedInertCandidate(staged(V41, { depends_on: PAIR }))).toBe(false)             // the pair is v5's declared set, not v4.1's
      expect(isNirmanaStagedInertCandidate(staged(V41, { has_non_test_runtime_evidence: true }))).toBe(false)
      expect(() => buildNirmanaBaselineCandidate([...population, staged(V41, { depends_on: PAIR })])).toThrow()
    })

    it('a candidate with a DEPENDENT is still part of the live DAG: not excluded (v5 truthful or not)', () => {
      const dependent = registryRow('bg_depends_on_v5', { depends_on: [V5], sort_order: 5 })
      expect(excludeNirmanaStagedInertCandidates([v5truthful(), dependent]).map((r) => r.asset_id)).toEqual([V5, 'bg_depends_on_v5'])
      expect(excludedNirmanaStagedInertCandidates([v5truthful(), dependent])).toEqual([])
      // the candidate stays in the denominator, so the baseline and BOTH frozen-registry comparisons fail closed (F3: asserted, not implied)
      const rows = [...population, v5truthful(), dependent]
      expect(() => buildNirmanaBaselineCandidate(rows)).toThrow()
      expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, rows)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 5/)
      expect(() => assertManifestMatchesRegistry(frozen().manifest, rows)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 5/)
    })

    it('VISIBLE exclusion: each excluded id is NAMED with its reason and decision (not merely absent from the count); nothing is listed when nothing is excluded', () => {
      expect(excludedNirmanaStagedInertCandidates([...population, v5truthful(), staged(V41)])).toEqual([
        { asset_id: V41, reason: 'staged inert candidate', decision: 'PRAVAHA-2996 (migration 1243)' },
        { asset_id: V5, reason: 'unsealed test candidate', decision: 'N-137' },
      ])
      expect(excludedNirmanaStagedInertCandidates(population)).toEqual([])
      expect(excludedNirmanaStagedInertCandidates([...population, v5truthful({ is_active: true })])).toEqual([])
    })

    it('F1: with NO declared test trigger anywhere the SQL is still valid — an explicit empty array, never a CASE with no WHEN', () => {
      const none = new Map<string, NirmanaStagedInertCandidateRule>([['ka_gochara_v4_41_candidate', { ...BASE_RULE, reason: 'staged inert candidate', decision: 'D' }]])
      const sql = runtimeEvidenceSql('registry', none)
      expect(sql).toContain('br.triggered_by = ANY (ARRAY[]::text[])')
      expect(sql).not.toMatch(/CASE\s+registry\.asset_id\s+(ELSE|END)/)                                  // `CASE x ELSE … END` with no WHEN is a syntax error
      expect(sql).not.toMatch(/THEN ARRAY\[/)                                                                // no per-id trigger arm at all
      expect(sql).toMatch(/AS has_non_test_runtime_evidence$/)
      // the real table is unchanged by the rule parameter: still the golden text
      expect(runtimeEvidenceSql('{a}')).toBe(readFileSync(path.resolve(__dirname, 'fixtures/runtime_evidence_sql.golden.txt'), 'utf8').replace(/\n$/, ''))
    })

    describe('F2: the rule table is validated (at module load for the real table, and for any table handed to the SQL builder)', () => {
      const ok = (over: Partial<NirmanaStagedInertCandidateRule> = {}): ReadonlyMap<string, NirmanaStagedInertCandidateRule> =>
        new Map([['ka_x', { ...BASE_RULE, declaredDependsOn: ['ga_a'], testTriggers: ['t-1'], reason: 'unsealed test candidate', decision: 'N-1', ...over }]])
      it('the real table passes (this is the module-load check)', () => {
        expect(() => assertStagedInertCandidateRules(NIRMANA_STAGED_INERT_CANDIDATE_RULES)).not.toThrow()
        expect(() => assertStagedInertCandidateRules(ok())).not.toThrow()
      })
      it.each([
        ['an EMPTY-string test trigger (it would match triggered_by = \'\')', { testTriggers: [''] }],
        ['a whitespace-only test trigger', { testTriggers: ['   '] }],
        ['an untrimmed test trigger (it could never match)', { testTriggers: [' t-1'] }],
        ['a trailing-space test trigger', { testTriggers: ['t-1 '] }],
        ['a duplicated test trigger', { testTriggers: ['t-1', 't-1'] }],
        ['an empty declared dependency', { declaredDependsOn: [''] }],
        ['an untrimmed declared dependency', { declaredDependsOn: ['ga_a '] }],
        ['a duplicated declared dependency', { declaredDependsOn: ['ga_a', 'ga_a'] }],
        ['an empty reason', { reason: '' }],
        ['an empty decision', { decision: '  ' }],
      ])('refuses %s', (_name, over) => {
        const table = ok(over as Partial<NirmanaStagedInertCandidateRule>)
        expect(() => assertStagedInertCandidateRules(table)).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)
        expect(() => runtimeEvidenceSql('registry', table)).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)        // a bad table can never reach SQL
      })
      it('refuses an empty or untrimmed asset id', () => {
        expect(() => assertStagedInertCandidateRules(new Map([['', { ...BASE_RULE, reason: 'r', decision: 'd' }]]))).toThrow()
        expect(() => assertStagedInertCandidateRules(new Map([[' ka_x', { ...BASE_RULE, reason: 'r', decision: 'd' }]]))).toThrow()
      })
    })

    it('the exclusion list enters no digest: the candidate is byte-identical whether or not the visible list is asked for', () => {
      const rows = [...population, v5truthful(), staged(V41)]
      const before = JSON.stringify(buildNirmanaBaselineCandidate(rows))
      excludedNirmanaStagedInertCandidates(rows)
      expect(JSON.stringify(buildNirmanaBaselineCandidate(rows))).toBe(before)
      expect(before).not.toContain('N-137')
    })
  })


  // ── N-138 (Suvarṇa): the retirement-pending legacy century writer — the same rule, two EXPLICIT per-id differences: dependents inactive_only and evidence by DATE ──────────────
  describe('N-138 — ka_gochara_v3_century_materialize: inert, declared six dependencies, no ACTIVE dependent, no evidence newer than the audit instant', () => {
    const V3_DEPS = ['bg_sky_calendar', 'ka_gochara_resonance', 'ka_kota_chakra', 'ka_moorti_nirnaya', 'ka_tithi_pravesha', 'ka_vedha_gochara']
    const CUTOFF = '2026-10-04T13:31:57Z'
    const depRows = V3_DEPS.map((id, i) => registryRow(id, { layer: id.startsWith('bg_') ? 'brahmagyan' : 'kala', sort_order: 10 + i }))
    const base: NirmanaRegistryContractRow[] = [...population, ...depRows]
    /** v3 exactly as production reads it (2026-10-04): CURRENT, inactive, has a writer, the six dependencies, no evidence newer than the cutoff. */
    const v3 = (over: Partial<NirmanaRegistryContractRow> = {}) => registryRow(V3, {
      layer: 'kala', sort_order: 120, scope: 'per_chart', is_active: false, has_writer: true, depends_on: V3_DEPS, has_non_test_runtime_evidence: false, target_table: 'kala_gochara_windows_v2', ...over,
    })
    /** The END-STATE frozen manifest (a successor that matches reality: no v3) and the INTERIM one (the t3 manifest froze v3 as an ACTIVE build writer). */
    const endState = () => buildNirmanaBaselineCandidate(base)
    const interim = () => buildNirmanaBaselineCandidate([...base, v3({ is_active: true })])
    const defn = (c: ReturnType<typeof buildNirmanaBaselineCandidate>) => ({ definition_status: 'frozen' as const, manifest: c.manifest, manifest_sha256: c.manifest_sha256 })
    /** The state the rule must refuse to hide: v3 is NOT in the excluded list and the monitor can see it (the baseline throws, or the candidate carries v3 and is not in_sync). */
    const failsClosed = (rows: NirmanaRegistryContractRow[]) => {
      expect(excludedNirmanaStagedInertCandidates(rows).map((e) => e.asset_id)).not.toContain(V3)
      expect(excludeNirmanaStagedInertCandidates(rows).map((r) => r.asset_id)).toContain(V3)
      let candidate: ReturnType<typeof buildNirmanaBaselineCandidate> | null = null
      try { candidate = buildNirmanaBaselineCandidate(rows) } catch { return }                                     // an unresolved obligation: fails closed by throwing
      expect(candidate.manifest.assets.map((a) => a.asset_id)).toContain(V3)
      expect(classifyNirmanaDivergence({ definition: defn(endState()), candidate, observation: null }).status).not.toBe('in_sync')
    }

    it('the rule table entry: the six declared dependencies, no empty set, the cutoff instant, inactive_only dependents, decision N-138, a visible reason that names the end', () => {
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V3)).toEqual({
        declaredDependsOn: V3_DEPS, emptyDependsOnAllowed: false, testTriggers: [], evidenceCutoff: CUTOFF, dependents: 'inactive_only',
        reason: 'retirement-pending legacy century writer (interim: ends with the t3 successor manifest or the registry retirement)', decision: 'N-138',
      })
    })

    it('INERT ⇒ excluded: with production\'s shape the baseline CONSTRUCTS (it threw on the unresolved obligation before) and v3 is named in the visible list', () => {
      const rows = [...base, v3()]
      expect(isNirmanaStagedInertCandidate(rows[rows.length - 1])).toBe(true)
      expect(() => buildNirmanaBaselineCandidate(rows)).not.toThrow()
      expect(buildNirmanaBaselineCandidate(rows)).toEqual(endState())
      expect(excludedNirmanaStagedInertCandidates(rows)).toEqual([{ asset_id: V3, reason: NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V3)!.reason, decision: 'N-138' }])
    })

    it('WITHOUT the rule v3 is the reproduced defect: the same inactive, written, CURRENT shape under an unadjudicated id throws the unresolved-obligation error', () => {
      expect(() => buildNirmanaBaselineCandidate([...base, { ...v3(), asset_id: 'ka_gochara_v3_lookalike' }])).toThrow(/cannot retain an unresolved execution obligation/)
    })

    it('END STATE ≠ INTERIM: against a successor manifest without v3 the monitor reads in_sync; against the t3 manifest that froze v3 as ACTIVE it reports plan_adaptation_required NAMING v3 — the true state, never in_sync, never source_unavailable', () => {
      const rows = [...base, v3()]
      expect(classifyNirmanaDivergence({ definition: defn(endState()), candidate: buildNirmanaBaselineCandidate(rows), observation: null })).toMatchObject({ status: 'in_sync', affected_asset_ids: [] })
      const status = classifyNirmanaDivergence({ definition: defn(interim()), candidate: buildNirmanaBaselineCandidate(rows), observation: null })
      expect(status.status).toBe('plan_adaptation_required')
      expect(status.affected_asset_ids).toContain(V3)
    })

    // The four mutations of the ruling, each failing closed — and the neighbouring shapes the rule must not hide.
    it.each([
      ['NEW evidence after the audit instant (a run of any trigger)', { has_non_test_runtime_evidence: true }],
      ['the evidence column unknown (null)', { has_non_test_runtime_evidence: null }],
      ['the evidence column absent', { has_non_test_runtime_evidence: undefined }],
      ['is_active true', { is_active: true }],
      ['an EXTRA dependency', { depends_on: [...V3_DEPS, 'bg_reference'] }],
      ['a MISSING dependency', { depends_on: V3_DEPS.slice(1) }],
      ['a DIFFERENT dependency', { depends_on: [...V3_DEPS.slice(1), 'bg_reference'] }],
      ['a DUPLICATED dependency', { depends_on: [...V3_DEPS, V3_DEPS[0]] }],
      ['an EMPTY dependency set (v3 does not share v5\'s pre-migration allowance)', { depends_on: [] }],
      ['lost its writer', { has_writer: false }],
      ['is RETIRED', { catalog_status: 'RETIRED' as const, superseded_by: 'bg_reference', data_disposition: 'RETAINED_AS_CAPITAL' as const }],
    ])('MUTATION — v3 with %s ⇒ NOT excluded and visible to the monitor', (_name, over) => {
      const row = v3(over as Partial<NirmanaRegistryContractRow>)
      expect(isNirmanaStagedInertCandidate(row)).toBe(false)
      failsClosed([...base, row])
    })

    it('MUTATION — an ACTIVE dependent makes v3 part of the live DAG: NOT excluded (inactive_only)', () => {
      const dependent = registryRow('ka_active_dependent', { layer: 'kala', sort_order: 130, depends_on: [V3], is_active: true })
      expect(excludedNirmanaStagedInertCandidates([v3(), dependent])).toEqual([])
      expect(excludeNirmanaStagedInertCandidates([v3(), dependent]).map((r) => r.asset_id)).toEqual([V3, 'ka_active_dependent'])
      failsClosed([...base, v3(), dependent])
    })

    it.each([['null', null], ['undefined', undefined]])('MUTATION — a dependent whose is_active is %s (unknown) is NOT inactive: v3 is NOT excluded', (_name, unknown) => {
      const dependent = { ...registryRow('ka_unknown_dependent', { layer: 'kala', sort_order: 130, depends_on: [V3] }), is_active: unknown } as unknown as NirmanaRegistryContractRow
      expect(excludedNirmanaStagedInertCandidates([v3(), dependent])).toEqual([])
    })

    it('an INACTIVE dependent is allowed (the explicit per-id field): v3 stays excluded and the dependent stays in the kept rows; v4.1 / v5 keep their own `none` policy', () => {
      const inactiveDependent = registryRow('ka_inactive_dependent', { layer: 'kala', sort_order: 130, depends_on: [V3], is_active: false })
      expect(excludedNirmanaStagedInertCandidates([v3(), inactiveDependent]).map((e) => e.asset_id)).toEqual([V3])
      expect(excludeNirmanaStagedInertCandidates([v3(), inactiveDependent]).map((r) => r.asset_id)).toEqual(['ka_inactive_dependent'])
      // F3 (Suvarṇa Exec): `inactive_only` is partition-level only — at BASELINE level the inactive dependent itself is an unresolved asset whose dependency (the excluded v3) is
      // not in the manifest, so the baseline still fails closed. The allowance changes what the monitor reports as excluded, never what it can read as healthy.
      expect(() => buildNirmanaBaselineCandidate([...base, v3(), inactiveDependent])).toThrow()
      // the same inactive dependent does NOT free a `none` id
      const v5Dependent = registryRow('ka_inactive_on_v5', { layer: 'kala', sort_order: 131, depends_on: [V5], is_active: false })
      expect(excludedNirmanaStagedInertCandidates([staged(V5), v5Dependent])).toEqual([])
      const v41Dependent = registryRow('ka_inactive_on_v41', { layer: 'kala', sort_order: 132, depends_on: [V41], is_active: false })
      expect(excludedNirmanaStagedInertCandidates([staged(V41), v41Dependent])).toEqual([])
    })

    it('the supporting-writer path (R20-2) holds for v3: an ACTIVE bo_grounding that depends on v3 keeps v3 in the denominator', () => {
      const grounding = registryRow('bo_grounding', { layer: 'bodha', sort_order: 25, catalog_status: 'DRAFT', is_active: true, depends_on: [V3] })
      expect(excludeNirmanaStagedInertCandidates([...base, v3(), grounding]).map((r) => r.asset_id)).toContain(V3)
    })

    it('the dependency order of the declared set is irrelevant; the dependents of v3 in the production registry are NONE (audit fact)', () => {
      expect(isNirmanaStagedInertCandidate(v3({ depends_on: [...V3_DEPS].reverse() }))).toBe(true)
      const production = JSON.parse(readFileSync(path.join(__dirname, 'fixtures', 'production_asset_registry_2026_10_04.json'), 'utf8')) as { audited_at: string; rows: NirmanaRegistryContractRow[]; dependents_of_v3: string[] }
      expect(production.audited_at).toBe(CUTOFF)
      expect(production.dependents_of_v3).toEqual([])
      const prodV3 = production.rows.find((r) => r.asset_id === V3)!
      expect([...(prodV3.depends_on ?? [])].sort()).toEqual(V3_DEPS)
      expect(isNirmanaStagedInertCandidate(prodV3)).toBe(true)
    })

    it('PRODUCTION SHAPE (the registry as read read-only 2026-10-04, through the real predicate): the baseline CONSTRUCTS with 127 assets — 131 rows − v4.1 − v5 − v3 − bo_grounding — and exactly those three are named as excluded', () => {
      const production = JSON.parse(readFileSync(path.join(__dirname, 'fixtures', 'production_asset_registry_2026_10_04.json'), 'utf8')) as { rows: NirmanaRegistryContractRow[] }
      expect(production.rows).toHaveLength(131)
      const candidate = buildNirmanaBaselineCandidate(production.rows)
      const ids = candidate.manifest.assets.map((a) => a.asset_id)
      expect(ids).toHaveLength(127)
      for (const id of [V3, V5, V41, 'bo_grounding']) expect(ids).not.toContain(id)
      expect(excludedNirmanaStagedInertCandidates(production.rows).map((e) => `${e.asset_id}:${e.decision}`)).toEqual([`${V41}:PRAVAHA-2996 (migration 1243)`, `${V3}:N-138`, `${V5}:N-137`].sort())
      // the same registry with ONE new evidence row for v3 after the cutoff is the original failure again: fail closed, never a silent exclusion
      const withNewRun = production.rows.map((r) => (r.asset_id === V3 ? { ...r, has_non_test_runtime_evidence: true } : r))
      expect(() => buildNirmanaBaselineCandidate(withNewRun)).toThrow(/cannot retain an unresolved execution obligation/)
    })

    describe('the evidence predicate (cutoff mode) and the rule-table validation', () => {
      it('the SQL has the CUTOFF arm: STRICTLY newer, the row\'s own and its run\'s timestamps, and a row with no timestamp at all counts as newer (COALESCE … TRUE)', () => {
        const sql = runtimeEvidenceSql('registry')
        expect(sql).toContain("WHEN registry.asset_id IN ('ka_gochara_v3_century_materialize')")
        expect(sql).toContain("CASE registry.asset_id WHEN 'ka_gochara_v3_century_materialize' THEN '2026-10-04T13:31:57Z'::timestamptz END")
        expect(sql).toContain('COALESCE(GREATEST(rcpt.observed_at, br.created_at, br.started_at, br.ended_at) >')
        expect(sql).toContain('COALESCE(GREATEST(bra.started_at, bra.ended_at, br.created_at, br.started_at, br.ended_at) >')
        expect(sql.match(/, TRUE\)/g)).toHaveLength(2)
        expect(sql).toContain('LEFT JOIN public.build_runs br ON br.id = rcpt.build_id')
        expect(sql).toContain('LEFT JOIN public.build_runs br ON br.id = bra.run_id')
        expect(sql).not.toMatch(/>=\s*CASE/)                                                                        // strictly newer: evidence AT the cutoff is the audited history
        expect(sql).toMatch(/AS has_non_test_runtime_evidence$/)
      })
      it('the trigger arm lists ONLY the trigger-mode ids (v3 is never read as test evidence) and the golden text is the one the python test runs', () => {
        const sql = runtimeEvidenceSql('registry')
        expect(sql).toContain("WHEN registry.asset_id IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5')")
        expect(sql.indexOf('ka_gochara_v3_century_materialize')).toBeGreaterThan(sql.indexOf("'gochara-v5-small-test'"))
        expect(runtimeEvidenceSql('{a}')).toBe(readFileSync(path.resolve(__dirname, 'fixtures/runtime_evidence_sql.golden.txt'), 'utf8').replace(/\n$/, ''))
      })
      it('a table with ONLY a cutoff id still produces valid SQL (no empty trigger arm), and a table with none keeps the N-137 text', () => {
        const only = new Map<string, NirmanaStagedInertCandidateRule>([[V3, NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V3)!]])
        const sql = runtimeEvidenceSql('registry', only)
        expect(sql).toMatch(/^CASE WHEN registry\.asset_id IN \('ka_gochara_v3_century_materialize'\)/)
        expect(sql).not.toContain('triggered_by')
      })
      const okCut = (over: Partial<NirmanaStagedInertCandidateRule> = {}): ReadonlyMap<string, NirmanaStagedInertCandidateRule> =>
        new Map([['ka_x', { ...BASE_RULE, evidenceCutoff: CUTOFF, dependents: 'inactive_only' as const, reason: 'r', decision: 'N-1', ...over }]])
      it('a valid cutoff entry passes', () => {
        expect(() => assertStagedInertCandidateRules(okCut())).not.toThrow()
      })
      it.each([
        ['a date without a time', { evidenceCutoff: '2026-10-04' }],
        ['a time without the Z', { evidenceCutoff: '2026-10-04T13:31:57' }],
        ['a numeric offset instead of Z', { evidenceCutoff: '2026-10-04T13:31:57+00:00' }],
        ['fractional seconds', { evidenceCutoff: '2026-10-04T13:31:57.000Z' }],
        ['an impossible date', { evidenceCutoff: '2026-13-40T00:00:00Z' }],
        ['a rolled-over date (Feb 30)', { evidenceCutoff: '2026-02-30T00:00:00Z' }],
        ['a quote that would end the SQL literal', { evidenceCutoff: "2026-10-04T13:31:57Z'; DROP TABLE x; --" }],
        ['an untrimmed instant', { evidenceCutoff: ' 2026-10-04T13:31:57Z' }],
        ['an empty instant', { evidenceCutoff: '' }],
        ['a test trigger on a cutoff id (one evidence mode per id)', { testTriggers: ['t-1'] }],
        ['an unknown dependents policy', { dependents: 'any' as unknown as 'none' }],
        ['a missing dependents policy', { dependents: undefined as unknown as 'none' }],
        ['a non-boolean emptyDependsOnAllowed', { emptyDependsOnAllowed: 'yes' as unknown as boolean }],
      ])('refuses %s', (_name, over) => {
        const table = okCut(over as Partial<NirmanaStagedInertCandidateRule>)
        expect(() => assertStagedInertCandidateRules(table)).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)
        expect(() => runtimeEvidenceSql('registry', table)).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)
      })
    })

    it('the exclusion enters no digest: the candidate is byte-identical whether or not the visible list is asked for, and carries no N-138 text', () => {
      const rows = [...base, v3()]
      const before = JSON.stringify(buildNirmanaBaselineCandidate(rows))
      excludedNirmanaStagedInertCandidates(rows)
      expect(JSON.stringify(buildNirmanaBaselineCandidate(rows))).toBe(before)
      expect(before).not.toContain('N-138')
      expect(before).not.toContain(V3)
    })
  })

})
