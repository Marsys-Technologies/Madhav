import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import {
  assertManifestMatchesRegistry,
  assertManifestMatchesRegistryIdentity,
  assertStagedInertCandidateRules,
  excludeNirmanaStagedInertCandidates,
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
 * N-141 — `ga_fact_identity` (migration 1262, PR #3073): a REGISTERED INDEX of kind data with NO writer and NO build obligation (hand-run script G-IDX, no @register()'d writer).
 * Migration 1262 made the monitor read source_unavailable (the row could not be given an execution obligation, so the baseline threw). Suvarna's ruling: the id is EXCLUDED FROM THE
 * DENOMINATOR, with a stated reason and the decision id, by a row of the SAME rule table as N-137/N-138 — and the exclusion FAILS CLOSED (throws) the moment the row's shape changes.
 */
const ID = 'ga_fact_identity'
const V3 = 'ka_gochara_v3_century_materialize'
const V41 = 'ka_gochara_v4_41_candidate'
const V5 = 'ka_gochara_v5'

type Fixture = { read_at: string; rows: NirmanaRegistryContractRow[]; dependents_of_ga_fact_identity: string[] }
const load = (name: string) => JSON.parse(readFileSync(path.join(__dirname, 'fixtures', name), 'utf8'))
const production = load('production_asset_registry_2026_10_05.json') as Fixture
const before1262 = load('production_asset_registry_2026_10_04.json') as { rows: NirmanaRegistryContractRow[] }

const indexRow = (): NirmanaRegistryContractRow => structuredClone(production.rows.find((r) => r.asset_id === ID)!)
const withIndex = (over: Partial<NirmanaRegistryContractRow>) => production.rows.map((r) => (r.asset_id === ID ? { ...r, ...over } : r))
const withDependent = (over: Partial<NirmanaRegistryContractRow> = {}) => [...production.rows, {
  ...production.rows.find((r) => r.asset_id === 'ga_positions')!, asset_id: 'ga_depends_on_index', sort_order: 999, depends_on: [ID], has_non_test_runtime_evidence: null, ...over,
}]

describe('N-141 — the registered no-writer index is excluded from the denominator, visibly, by the one rule table', () => {
  describe('the real production-shaped registry (read 2026-10-05, after migration 1262)', () => {
    it('the fixture is the registry as the monitor loader reads it: 132 rows = the 131 of 2026-10-04 plus ga_fact_identity (active, kind data, no writer, no dependencies, nothing depends on it)', () => {
      expect(production.rows).toHaveLength(132)
      expect(production.dependents_of_ga_fact_identity).toEqual([])
      expect(production.rows.filter((r) => (r.depends_on ?? []).includes(ID))).toEqual([])
      expect(production.rows.map((r) => r.asset_id).filter((id) => !before1262.rows.some((o) => o.asset_id === id))).toEqual([ID])
      expect(indexRow()).toMatchObject({ layer: 'ganita', asset_kind: 'data', catalog_status: 'CURRENT', is_active: true, has_writer: false, depends_on: [], superseded_by: null, data_disposition: null })
    })

    it('WITHOUT the rule the row breaks the baseline: it carries the unresolved execution obligation (the reproduced defect), and the main-before-N-141 rule table did not name it', () => {
      expect(nirmanaExecutionContractForRegistryRow(indexRow()).execution_obligation).toBe('unresolved')
      expect(NIRMANA_STAGED_INERT_CANDIDATES.has(ID)).toBe(false)
    })

    it('the baseline CONSTRUCTS: 132 rows − v4.1 − v5 − v3 − bo_grounding − ga_fact_identity = 127 assets, and exactly four ids are named as excluded, ga_fact_identity under N-141', () => {
      const candidate = buildNirmanaBaselineCandidate(production.rows)
      const ids = candidate.manifest.assets.map((a) => a.asset_id)
      expect(ids).toHaveLength(127)
      for (const id of [ID, V3, V5, V41, 'bo_grounding']) expect(ids).not.toContain(id)
      expect(excludedNirmanaStagedInertCandidates(production.rows).map((e) => `${e.asset_id}:${e.decision}`)).toEqual([`${V41}:PRAVAHA-2996 (migration 1243)`, `${ID}:N-141`, `${V3}:N-138`, `${V5}:N-137`].sort())
      expect(excludedNirmanaStagedInertCandidates(production.rows).find((e) => e.asset_id === ID)).toEqual({
        asset_id: ID,
        reason: 'registered index (kind data) with no writer and no build obligation: excluded from the denominator, fails closed if that shape changes',
        decision: 'N-141',
      })
    })

    it('DIGEST STABILITY: the baseline over the 132-row registry is byte-identical (manifest, labels and every digest) to the baseline over the 131 rows that never had the index — the rule adds nothing to any digest', () => {
      const withRow = buildNirmanaBaselineCandidate(production.rows)
      const withoutRow = buildNirmanaBaselineCandidate(before1262.rows)
      expect(JSON.stringify(withRow)).toBe(JSON.stringify(withoutRow))
      expect(withRow.manifest_sha256).toBe(withoutRow.manifest_sha256)
      const text = JSON.stringify(withRow)
      expect(text).not.toContain(ID)
      expect(text).not.toContain('N-141')
      // asking for the visible list changes nothing either
      excludedNirmanaStagedInertCandidates(production.rows)
      expect(JSON.stringify(buildNirmanaBaselineCandidate(production.rows))).toBe(text)
    })

    it('both frozen-registry comparisons pass and the monitor classifier reads in_sync for a definition frozen from the registry that never had the row', () => {
      const frozen = buildNirmanaBaselineCandidate(before1262.rows)
      expect(() => assertManifestMatchesRegistryIdentity(frozen.manifest, production.rows)).not.toThrow()
      expect(() => assertManifestMatchesRegistry(frozen.manifest, production.rows)).not.toThrow()
      expect(classifyNirmanaDivergence({
        definition: { definition_status: 'frozen', manifest: frozen.manifest, manifest_sha256: frozen.manifest_sha256 },
        candidate: buildNirmanaBaselineCandidate(production.rows), observation: null,
      })).toMatchObject({ status: 'in_sync', affected_asset_ids: [] })
    })

    it('the other three rows are untouched: v5, v4.1 and v3 keep EXACTLY their rule objects (no noWriterIndex key), and the staged set is still the three of N-137/N-138', () => {
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V5)).toEqual({ declaredDependsOn: ['ga_dashas', 'ga_positions'], emptyDependsOnAllowed: true, testTriggers: ['gochara-v5-small-test'], evidenceCutoff: null, dependents: 'none', reason: 'unsealed test candidate', decision: 'N-137' })
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V41)).toEqual({ declaredDependsOn: [], emptyDependsOnAllowed: true, testTriggers: [], evidenceCutoff: null, dependents: 'none', reason: 'staged inert candidate', decision: 'PRAVAHA-2996 (migration 1243)' })
      expect(Object.keys(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(V3)!).sort()).toEqual(['declaredDependsOn', 'decision', 'dependents', 'emptyDependsOnAllowed', 'evidenceCutoff', 'reason', 'testTriggers'].sort())
      expect([...NIRMANA_STAGED_INERT_CANDIDATES].sort()).toEqual([V3, V41, V5])
      expect([...NIRMANA_NO_WRITER_INDEXES]).toEqual([ID])
    })

    it('the rule row: no dependencies, no test trigger, no cutoff, nothing may depend on it, pinned to layer ganita and kind data, decision N-141', () => {
      expect(NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(ID)).toEqual({
        declaredDependsOn: [], emptyDependsOnAllowed: true, testTriggers: [], evidenceCutoff: null, dependents: 'none',
        noWriterIndex: { layer: 'ganita', assetKind: 'data' },
        reason: 'registered index (kind data) with no writer and no build obligation: excluded from the denominator, fails closed if that shape changes',
        decision: 'N-141',
      })
    })
  })

  describe('FAILS CLOSED — every change of the declared shape throws (never a silent inclusion, never a silent exclusion)', () => {
    const MUTATIONS: Array<[string, () => NirmanaRegistryContractRow[], RegExp]> = [
      ['has_writer becomes true (it gained a writer: it needs a build obligation now)', () => withIndex({ has_writer: true }), /has_writer/],
      ['has_writer is unknown (the loader supplied nothing)', () => withIndex({ has_writer: undefined as unknown as boolean }), /has_writer/],
      ['it gains a dependency', () => withIndex({ depends_on: ['ga_positions'] }), /depends_on/],
      ['it depends on itself', () => withIndex({ depends_on: [ID] }), /depends_on/],
      ['it gains a dependency that is not in the registry', () => withIndex({ depends_on: ['ga_nonexistent'] }), /depends_on/],
      ['an ACTIVE asset depends on it', () => withDependent(), /depended on/],
      ['an INACTIVE asset depends on it', () => withDependent({ is_active: false }), /depended on/],
      ['a RETIRED asset depends on it', () => withDependent({ is_active: false, catalog_status: 'RETIRED', superseded_by: 'ga_positions', data_disposition: 'RETAINED_AS_CAPITAL' }), /depended on/],
      ['its kind becomes service', () => withIndex({ asset_kind: 'service' }), /asset_kind/],
      ['its kind becomes artifact', () => withIndex({ asset_kind: 'artifact' }), /asset_kind/],
      ['its layer changes', () => withIndex({ layer: 'bodha' }), /layer/],
      ['it becomes inactive', () => withIndex({ is_active: false }), /is_active/],
      ['is_active is unknown', () => withIndex({ is_active: undefined as unknown as boolean }), /is_active/],
      ['it is RETIRED (with a successor and a disposition, as a retirement migration would leave it)', () => withIndex({ is_active: false, catalog_status: 'RETIRED', superseded_by: 'ga_positions', data_disposition: 'RETAINED_AS_CAPITAL' }), /catalog_status/],
      ['it is RETIRED but still flagged active', () => withIndex({ catalog_status: 'RETIRED' }), /catalog_status/],
      ['it is DRAFT', () => withIndex({ catalog_status: 'DRAFT' }), /catalog_status/],
      ['it gains a successor', () => withIndex({ superseded_by: 'ga_positions' }), /superseded_by/],
      ['it gains a data disposition', () => withIndex({ data_disposition: 'DROPPABLE' }), /data_disposition/],
    ]

    it.each(MUTATIONS)('%s', (_name, rows, message) => {
      const view = rows()
      expect(() => partitionNirmanaStagedInertCandidates(view)).toThrow(message)
      expect(() => excludedNirmanaStagedInertCandidates(view)).toThrow(/N-141/)
      expect(() => excludeNirmanaStagedInertCandidates(view)).toThrow(/NIRMANA_STAGED_INERT_CANDIDATE_RULES/)
      // every caller that sees the registry refuses: the baseline, and both frozen-registry comparisons
      expect(() => buildNirmanaBaselineCandidate(view)).toThrow(/ga_fact_identity/)
      const frozen = buildNirmanaBaselineCandidate(before1262.rows)
      expect(() => assertManifestMatchesRegistryIdentity(frozen.manifest, view)).toThrow(/ga_fact_identity/)
      expect(() => assertManifestMatchesRegistry(frozen.manifest, view)).toThrow(/ga_fact_identity/)
    })

    it('the refusal names the id, the decision, the failed conditions and the end condition (where to fix it) — and lists EVERY violated condition, not only the first', () => {
      let message = ''
      try { partitionNirmanaStagedInertCandidates(withIndex({ has_writer: true, depends_on: ['ga_positions'] })) } catch (error) { message = String((error as Error).message) }
      expect(message).toContain('ga_fact_identity')
      expect(message).toContain('N-141')
      expect(message).toContain('has_writer')
      expect(message).toContain('depends_on')
      expect(message).toMatch(/end condition/i)
    })

    it('row-level: isNirmanaStagedInertCandidate is false for each shape change and true only for the declared one (and never throws — the throw is the partition\'s)', () => {
      expect(isNirmanaStagedInertCandidate(indexRow())).toBe(true)
      for (const over of [{ has_writer: true }, { depends_on: ['ga_positions'] }, { asset_kind: 'service' as const }, { layer: 'bodha' as const }, { is_active: false }, { catalog_status: 'RETIRED' as const }, { superseded_by: 'x' }, { data_disposition: 'DROPPABLE' as const }]) {
        expect(isNirmanaStagedInertCandidate({ ...indexRow(), ...over })).toBe(false)
      }
    })

    it('a row that would ALREADY have an adjudicated execution obligation in code is not an index with no build obligation: the real obligation function is consulted (end condition: a successor that includes it)', () => {
      // lel_events has an adjudicated source_acceptance disposition in code; a table that (wrongly) declared it a no-writer index must refuse it
      const table = new Map<string, NirmanaStagedInertCandidateRule>([['lel_events', { ...NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(ID)!, noWriterIndex: { layer: 'mimamsa', assetKind: 'data' } }]])
      const row = { ...indexRow(), asset_id: 'lel_events', layer: 'mimamsa' as const }
      expect(nirmanaExecutionContractForRegistryRow(row).execution_obligation).not.toBe('unresolved')
      expect(isNirmanaStagedInertCandidate(row, table)).toBe(false)
      expect(() => partitionNirmanaStagedInertCandidates([row], table)).toThrow(/execution obligation/)
    })

    it('the evidence column is NOT consulted for this id (it is NULL for it by construction): null, false and true all leave it excluded — evidence of a build cannot exist for a row with no writer, and the other ids keep their own detector', () => {
      for (const evidence of [null, undefined, false, true]) {
        const view = withIndex({ has_non_test_runtime_evidence: evidence as boolean | null | undefined })
        expect(excludedNirmanaStagedInertCandidates(view).map((e) => e.asset_id)).toContain(ID)
      }
    })

    it('a registry WITHOUT the row is not an error (nothing to exclude; the denominator is unaffected): the list simply does not name it', () => {
      expect(() => partitionNirmanaStagedInertCandidates(before1262.rows)).not.toThrow()
      expect(excludedNirmanaStagedInertCandidates(before1262.rows).map((e) => e.asset_id)).not.toContain(ID)
      expect(excludedNirmanaStagedInertCandidates([]).map((e) => e.asset_id)).toEqual([])
    })

    it('an existing staged candidate keeps its OLD failure mode: a v5 with non-test evidence is simply kept in the denominator (and the baseline throws on it), no N-141 text', () => {
      const view = production.rows.map((r) => (r.asset_id === V5 ? { ...r, has_non_test_runtime_evidence: true } : r))
      expect(excludedNirmanaStagedInertCandidates(view).map((e) => e.asset_id)).not.toContain(V5)
      expect(() => buildNirmanaBaselineCandidate(view)).toThrow(/cannot retain an unresolved execution obligation/)
    })
  })

  describe('the rule table validation and the evidence SQL', () => {
    const base = () => NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(ID)!
    const table = (over: Partial<NirmanaStagedInertCandidateRule>) => new Map<string, NirmanaStagedInertCandidateRule>([['ga_x', { ...base(), ...over }]])

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

    it('SQL: the evidence predicate NEVER mentions ga_fact_identity (it has no evidence mode) and is byte-identical to the golden text the python 1243 test runs', () => {
      const sql = runtimeEvidenceSql('{a}')
      expect(sql).not.toContain(ID)
      expect(sql).toBe(readFileSync(path.resolve(__dirname, 'fixtures/runtime_evidence_sql.golden.txt'), 'utf8').replace(/\n$/, ''))
      // a table holding ONLY a no-writer index still yields valid, never-true SQL (a CASE with no arm would be a syntax error)
      const only = runtimeEvidenceSql('registry', new Map([[ID, NIRMANA_STAGED_INERT_CANDIDATE_RULES.get(ID)!]]))
      expect(only).toMatch(/AS has_non_test_runtime_evidence$/)
      expect(only).not.toContain(ID)
      expect(only).toBe('NULL::boolean AS has_non_test_runtime_evidence')
    })
  })
})
