import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import {
  assertManifestMatchesRegistry,
  assertManifestMatchesRegistryIdentity,
  assertStagedInertCandidateRules,
  excludedNirmanaStagedInertCandidates,
  isNirmanaStagedInertCandidate,
  nirmanaExecutionContractForRegistryRow,
  NIRMANA_NO_WRITER_INDEXES,
  NIRMANA_STAGED_INERT_CANDIDATES,
  NIRMANA_STAGED_INERT_CANDIDATE_RULES,
  partitionNirmanaStagedInertCandidates,
  runtimeEvidenceSql,
  type NirmanaRegistryContractRow,
  type NirmanaStagedInertCandidateRule,
} from '../definitions'
import { buildNirmanaBaselineCandidate, classifyNirmanaDivergence } from '../monitor'

/**
 * `ga_fact_identity` — N-141 and its END CONDITION (a).
 *
 * Migration 1262 (PR #3073) registered the Fact Identity Index as an active row with NO writer; N-141 excluded it from the denominator by a row of the
 * staged-candidate rule table, FAILING CLOSED if its shape changed. Migration 1333 gives it a REGISTERED WRITER (ga_fact_identity, depends on the 12 ga_* assets that
 * write chart_facts; bo_pratijna depends on it), which is exactly the rule's end condition (a): the entry is REMOVED in the same change, and the asset is an ordinary
 * `build` asset. This file pins (1) the post-1333 behaviour of the real table and of the baseline / frozen-manifest comparisons, including the honest consequence that a
 * definition frozen BEFORE the asset now reads as drift until a successor definition includes it, and (2) the generic `noWriterIndex` mechanism, which is kept and still
 * fully tested, over an INJECTED table that carries the old N-141 rule (no real row uses it now).
 */
const ID = 'ga_fact_identity'
const V3 = 'ka_gochara_v3_century_materialize'
const V41 = 'ka_gochara_v4_41_candidate'
const V5 = 'ka_gochara_v5'
// the 12 ga_* assets that write chart_facts (migration 1333's edges), sorted
const UPSTREAM = ['ga_ayurdaya', 'ga_condition', 'ga_dashas', 'ga_nakshatra', 'ga_panchanga', 'ga_positions', 'ga_sade_sati', 'ga_sensitive', 'ga_sensitive_degree', 'ga_strength', 'ga_structural', 'ga_vichara']

type Fixture = { read_at: string; rows: NirmanaRegistryContractRow[]; dependents_of_ga_fact_identity: string[] }
const load = (name: string) => JSON.parse(readFileSync(path.join(__dirname, 'fixtures', name), 'utf8'))
/** The registry as read 2026-10-05, AFTER migration 1262 and BEFORE migration 1333 (ga_fact_identity: no writer, no dependencies, nothing depends on it). */
const production = load('production_asset_registry_2026_10_05.json') as Fixture
const before1262 = load('production_asset_registry_2026_10_04.json') as { rows: NirmanaRegistryContractRow[] }

/** The same registry after migration 1333: ga_fact_identity has a writer and the 12 edges; bo_pratijna gains the edge. Nothing else moves. */
const post1333 = (): NirmanaRegistryContractRow[] => production.rows.map((r) => {
  if (r.asset_id === ID) return { ...r, has_writer: true, depends_on: [...UPSTREAM] }
  if (r.asset_id === 'bo_pratijna') return { ...r, depends_on: [...(r.depends_on ?? []), ID] }
  return r
})

/** The OLD N-141 rule, exactly as it stood, injected so the retained mechanism stays tested without any real row using it. */
const N141_RULE: NirmanaStagedInertCandidateRule = {
  declaredDependsOn: [], emptyDependsOnAllowed: true, testTriggers: [], evidenceCutoff: null, dependents: 'none',
  noWriterIndex: { layer: 'ganita', assetKind: 'data' },
  reason: 'registered index (kind data) with no writer and no build obligation: excluded from the denominator, fails closed if that shape changes', decision: 'N-141',
}
const RULES: ReadonlyMap<string, NirmanaStagedInertCandidateRule> = new Map([...NIRMANA_STAGED_INERT_CANDIDATE_RULES, [ID, N141_RULE]])

const indexRow = (): NirmanaRegistryContractRow => structuredClone(production.rows.find((r) => r.asset_id === ID)!)
const withIndex = (over: Partial<NirmanaRegistryContractRow>) => production.rows.map((r) => (r.asset_id === ID ? { ...r, ...over } : r))
const withDependent = (over: Partial<NirmanaRegistryContractRow> = {}) => [...production.rows, {
  ...production.rows.find((r) => r.asset_id === 'ga_positions')!, asset_id: 'ga_depends_on_index', sort_order: 999, depends_on: [ID], has_non_test_runtime_evidence: null, ...over,
}]

describe('after migration 1333 — ga_fact_identity is an ordinary build asset (N-141 end condition (a))', () => {
  it('the real rule table no longer names it: only the three staged writers remain, and no no-writer index', () => {
    expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.has(ID)).toBe(false)
    expect([...NIRMANA_STAGED_INERT_CANDIDATES].sort()).toEqual([V3, V41, V5])
    expect([...NIRMANA_NO_WRITER_INDEXES]).toEqual([])
    expect(() => assertStagedInertCandidateRules(NIRMANA_STAGED_INERT_CANDIDATE_RULES)).not.toThrow()
    expect(runtimeEvidenceSql('{a}')).not.toContain(ID)
  })

  it('the fixtures are what the test says: pre-1333 is the 1262 shape, and all 11 upstream ids exist as active per_chart writers', () => {
    expect(indexRow()).toMatchObject({ layer: 'ganita', asset_kind: 'data', catalog_status: 'CURRENT', is_active: true, has_writer: false, depends_on: [] })
    for (const id of UPSTREAM) expect(production.rows.find((r) => r.asset_id === id), id).toMatchObject({ is_active: true, has_writer: true, layer: 'ganita' })
    const after = post1333()
    expect(after.find((r) => r.asset_id === ID)).toMatchObject({ has_writer: true, depends_on: UPSTREAM })
    expect(after.find((r) => r.asset_id === 'bo_pratijna')!.depends_on).toEqual([...production.rows.find((r) => r.asset_id === 'bo_pratijna')!.depends_on!, ID])
  })

  it('its execution obligation is now `build` (the real obligation function), not `unresolved`', () => {
    expect(nirmanaExecutionContractForRegistryRow(post1333().find((r) => r.asset_id === ID)!).execution_obligation).toBe('build')
    expect(nirmanaExecutionContractForRegistryRow(indexRow()).execution_obligation).toBe('unresolved')
  })

  it('the baseline over the post-1333 registry CONSTRUCTS with ONE MORE asset than before (128 = 127 + ga_fact_identity), the three staged ids still excluded, ga_fact_identity NOT excluded', () => {
    const candidate = buildNirmanaBaselineCandidate(post1333())
    const ids = candidate.manifest.assets.map((a) => a.asset_id)
    expect(ids).toHaveLength(128)
    expect(ids).toContain(ID)
    for (const id of [V3, V5, V41, 'bo_grounding']) expect(ids).not.toContain(id)
    expect(excludedNirmanaStagedInertCandidates(post1333()).map((e) => e.asset_id)).toEqual([V41, V3, V5].sort())
    const asset = candidate.manifest.assets.find((a) => a.asset_id === ID)!
    expect(asset).toMatchObject({ execution_obligation: 'build', depends_on: UPSTREAM })
    const wave = (id: string) => candidate.manifest.assets.find((a) => a.asset_id === id)!.wave_index!
    expect(wave(ID)).toBeGreaterThan(Math.max(...UPSTREAM.map(wave)))              // it runs after every chart_facts writer
    // waves are per layer: its reader bo_pratijna (bodha) carries the edge in its own dependency set
    expect(candidate.manifest.assets.find((a) => a.asset_id === 'bo_pratijna')!.depends_on).toContain(ID)
  })

  it('the changes 1333 makes to the DAG are the ONLY manifest differences: every other asset keeps its dependency set and contract digest', () => {
    const afterIds = new Map(buildNirmanaBaselineCandidate(post1333()).manifest.assets.map((a) => [a.asset_id, a]))
    const beforeIds = new Map(buildNirmanaBaselineCandidate(before1262.rows).manifest.assets.map((a) => [a.asset_id, a]))
    const differing = [...afterIds.keys()].filter((id) => JSON.stringify(afterIds.get(id)) !== JSON.stringify(beforeIds.get(id)))
    // ga_fact_identity is new; bo_pratijna gained the edge; waves of the assets downstream of bo_pratijna may shift by the added level, but no dependency set or contract moves
    expect(differing).toContain(ID)
    expect(differing).toContain('bo_pratijna')
    for (const id of differing.filter((x) => x !== ID && x !== 'bo_pratijna')) {
      const a = afterIds.get(id)!, b = beforeIds.get(id)!
      expect({ depends_on: a.depends_on, fp: a.registry_fingerprint_sha256 }, id).toEqual({ depends_on: b.depends_on, fp: b.registry_fingerprint_sha256 })
    }
  })

  it('THE HONEST CONSEQUENCE: a definition frozen BEFORE the asset reads as drift against the post-1333 registry (count 127 vs 128; bo_pratijna dependency set) until a successor definition includes it', () => {
    const frozen = buildNirmanaBaselineCandidate(before1262.rows)
    expect(() => assertManifestMatchesRegistryIdentity(frozen.manifest, post1333())).toThrow(/127 assets.*128/)
    expect(() => assertManifestMatchesRegistry(frozen.manifest, post1333())).toThrow(/127 assets.*128/)
    const verdict = classifyNirmanaDivergence({
      definition: { definition_status: 'frozen', manifest: frozen.manifest, manifest_sha256: frozen.manifest_sha256 },
      candidate: buildNirmanaBaselineCandidate(post1333()), observation: null,
    })
    expect(verdict.status).not.toBe('in_sync')
    expect(verdict.affected_asset_ids).toContain(ID)
  })

  it('the one-deploy window: the pre-1333 registry (writer-less, active) without the rule makes the baseline fail closed, naming the unresolved obligation (code ahead of the migration)', () => {
    expect(() => buildNirmanaBaselineCandidate(production.rows)).toThrow(/unresolved execution obligation/)
    expect(excludedNirmanaStagedInertCandidates(production.rows).map((e) => e.asset_id)).not.toContain(ID)
  })
})

describe('the retained `noWriterIndex` mechanism (generic; exercised over an INJECTED table carrying the old N-141 rule)', () => {
  describe('the declared shape', () => {
    it('the injected rule excludes exactly the declared shape (the pre-1333 production-shaped row), with the stated reason and decision', () => {
      expect(isNirmanaStagedInertCandidate(indexRow(), RULES)).toBe(true)
      expect(partitionNirmanaStagedInertCandidates(production.rows, RULES).excluded.find((e) => e.asset_id === ID)).toEqual({ asset_id: ID, reason: N141_RULE.reason, decision: 'N-141' })
    })

    it('the staged rows beside it keep EXACTLY their rule objects (no noWriterIndex key)', () => {
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V5)).toEqual({ declaredDependsOn: ['ga_dashas', 'ga_positions'], emptyDependsOnAllowed: true, testTriggers: ['gochara-v5-small-test'], evidenceCutoff: null, dependents: 'none', reason: 'unsealed test candidate', decision: 'N-137' })
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V41)).toEqual({ declaredDependsOn: [], emptyDependsOnAllowed: true, testTriggers: [], evidenceCutoff: null, dependents: 'none', reason: 'staged inert candidate', decision: 'PRAVAHA-2996 (migration 1243)' })
      expect(Object.keys(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V3)!).sort()).toEqual(['declaredDependsOn', 'decision', 'dependents', 'emptyDependsOnAllowed', 'evidenceCutoff', 'reason', 'testTriggers'].sort())
    })
  })

  describe('FAILS CLOSED — every change of the declared shape throws (never a silent inclusion, never a silent exclusion)', () => {
    const MUTATIONS: Array<[string, () => NirmanaRegistryContractRow[], RegExp]> = [
      ['has_writer becomes true (it gained a writer: it needs a build obligation now)', () => withIndex({ has_writer: true }), /has_writer/],
      ['has_writer is unknown (the loader supplied nothing)', () => withIndex({ has_writer: undefined as unknown as boolean }), /has_writer/],
      ['it gains a dependency', () => withIndex({ depends_on: ['ga_positions'] }), /depends_on/],
      ['it depends on itself', () => withIndex({ depends_on: [ID] }), /depends_on/],
      ['an ACTIVE asset depends on it', () => withDependent(), /depended on/],
      ['an INACTIVE asset depends on it', () => withDependent({ is_active: false }), /depended on/],
      ['its kind becomes service', () => withIndex({ asset_kind: 'service' }), /asset_kind/],
      ['its layer changes', () => withIndex({ layer: 'bodha' }), /layer/],
      ['it becomes inactive', () => withIndex({ is_active: false }), /is_active/],
      ['it is DRAFT', () => withIndex({ catalog_status: 'DRAFT' }), /catalog_status/],
      ['it gains a successor', () => withIndex({ superseded_by: 'ga_positions' }), /superseded_by/],
      ['it gains a data disposition', () => withIndex({ data_disposition: 'DROPPABLE' }), /data_disposition/],
    ]

    it.each(MUTATIONS)('%s', (_name, rows, message) => {
      const view = rows()
      expect(() => partitionNirmanaStagedInertCandidates(view, RULES)).toThrow(message)
      expect(() => partitionNirmanaStagedInertCandidates(view, RULES)).toThrow(/N-141/)
    })

    it('the refusal names the id, the decision, the failed conditions and the end condition — and lists EVERY violated condition, not only the first', () => {
      let message = ''
      try { partitionNirmanaStagedInertCandidates(withIndex({ has_writer: true, depends_on: ['ga_positions'] }), RULES) } catch (error) { message = String((error as Error).message) }
      for (const needle of ['ga_fact_identity', 'N-141', 'has_writer', 'depends_on']) expect(message).toContain(needle)
      expect(message).toMatch(/end condition/i)
    })

    it('row-level: isNirmanaStagedInertCandidate is false for each shape change and true only for the declared one (and never throws — the throw is the partition\'s)', () => {
      expect(isNirmanaStagedInertCandidate(indexRow(), RULES)).toBe(true)
      for (const over of [{ has_writer: true }, { depends_on: ['ga_positions'] }, { asset_kind: 'service' as const }, { layer: 'bodha' as const }, { is_active: false }, { catalog_status: 'RETIRED' as const }, { superseded_by: 'x' }, { data_disposition: 'DROPPABLE' as const }]) {
        expect(isNirmanaStagedInertCandidate({ ...indexRow(), ...over }, RULES)).toBe(false)
      }
    })

    it('a row that would ALREADY have an adjudicated execution obligation in code is not an index with no build obligation: the real obligation function is consulted', () => {
      const table = new Map<string, NirmanaStagedInertCandidateRule>([['lel_events', { ...N141_RULE, noWriterIndex: { layer: 'mimamsa', assetKind: 'data' } }]])
      const row = { ...indexRow(), asset_id: 'lel_events', layer: 'mimamsa' as const }
      expect(nirmanaExecutionContractForRegistryRow(row).execution_obligation).not.toBe('unresolved')
      expect(isNirmanaStagedInertCandidate(row, table)).toBe(false)
      expect(() => partitionNirmanaStagedInertCandidates([row], table)).toThrow(/execution obligation/)
    })

    it('the evidence column is NOT consulted for a no-writer index: null, false and true all leave it excluded', () => {
      for (const evidence of [null, undefined, false, true]) {
        const view = withIndex({ has_non_test_runtime_evidence: evidence as boolean | null | undefined })
        expect(partitionNirmanaStagedInertCandidates(view, RULES).excluded.map((e) => e.asset_id)).toContain(ID)
      }
    })

    it('a registry WITHOUT the row is not an error (nothing to exclude)', () => {
      expect(() => partitionNirmanaStagedInertCandidates(before1262.rows, RULES)).not.toThrow()
      expect(partitionNirmanaStagedInertCandidates(before1262.rows, RULES).excluded.map((e) => e.asset_id)).not.toContain(ID)
    })

    it('an existing staged candidate keeps its OLD failure mode: a v5 with non-test evidence is simply kept in the denominator (and the baseline throws on it), no N-141 text', () => {
      const view = post1333().map((r) => (r.asset_id === V5 ? { ...r, has_non_test_runtime_evidence: true } : r))
      expect(excludedNirmanaStagedInertCandidates(view).map((e) => e.asset_id)).not.toContain(V5)
      expect(() => buildNirmanaBaselineCandidate(view)).toThrow(/cannot retain an unresolved execution obligation/)
    })
  })

  describe('the rule table validation and the evidence SQL', () => {
    const table = (over: Partial<NirmanaStagedInertCandidateRule>) => new Map<string, NirmanaStagedInertCandidateRule>([['ga_x', { ...N141_RULE, ...over }]])

    it('the real table and a valid no-writer-index entry pass the validation', () => {
      expect(() => assertStagedInertCandidateRules(NIRMANA_STAGED_INERT_CANDIDATE_RULES)).not.toThrow()
      expect(() => assertStagedInertCandidateRules(table({}))).not.toThrow()
    })

    it.each([
      ['a declared dependency', { declaredDependsOn: ['ga_positions'] }],
      ['a test trigger', { testTriggers: ['t-1'] }],
      ['an evidence cutoff', { evidenceCutoff: '2026-10-04T13:31:57Z' }],
      ['the inactive_only dependents policy', { dependents: 'inactive_only' as const }],
      ['emptyDependsOnAllowed false', { emptyDependsOnAllowed: false }],
      ['an unknown layer', { noWriterIndex: { layer: 'nowhere' as 'ganita', assetKind: 'data' as const } }],
      ['kind service', { noWriterIndex: { layer: 'ganita' as const, assetKind: 'service' as 'data' } }],
      ['a missing layer', { noWriterIndex: { assetKind: 'data' as const } as unknown as NirmanaStagedInertCandidateRule['noWriterIndex'] }],
      ['a non-object noWriterIndex', { noWriterIndex: true as unknown as NirmanaStagedInertCandidateRule['noWriterIndex'] }],
    ])('refuses a no-writer-index entry with %s (one meaning per row: the predicate is exact)', (_name, over) => {
      expect(() => assertStagedInertCandidateRules(table(over as Partial<NirmanaStagedInertCandidateRule>))).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)
      expect(() => runtimeEvidenceSql('registry', table(over as Partial<NirmanaStagedInertCandidateRule>))).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)
    })

    it('SQL: the evidence predicate is byte-identical to the golden text the python 1243 test runs, and a table holding ONLY a no-writer index yields valid, never-true SQL', () => {
      expect(runtimeEvidenceSql('{a}')).toBe(readFileSync(path.resolve(__dirname, 'fixtures/runtime_evidence_sql.golden.txt'), 'utf8').replace(/\n$/, ''))
      const only = runtimeEvidenceSql('registry', new Map([[ID, N141_RULE]]))
      expect(only).not.toContain(ID)
      expect(only).toBe('NULL::boolean AS has_non_test_runtime_evidence')
    })
  })
})
