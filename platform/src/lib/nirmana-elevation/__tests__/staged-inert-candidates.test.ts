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
  isNirmanaStagedInertCandidate,
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

function registryRow(asset_id: string, overrides: Partial<NirmanaRegistryContractRow> = {}): NirmanaRegistryContractRow {
  return {
    asset_id, layer: 'brahmagyan', depends_on: [], sort_order: 1, scope: 'global', asset_kind: 'data', catalog_status: 'CURRENT', is_active: true, has_writer: true,
    target_table: `${asset_id}_rows`, count_sql: `SELECT count(*) FROM ${asset_id}_rows`, integrity_check_sql: null, health_probe: null, natural_key_partition: null,
    superseded_by: null, data_disposition: null, dead_flag: null, sanskrit_name: null, english_name: null, english_description: null, ...overrides,
  }
}

/** A staged candidate exactly as migration 1243 leaves it (and as the loaders read it: has_runtime_evidence = false). */
const staged = (id: string, over: Partial<NirmanaRegistryContractRow> = {}) => registryRow(id, {
  layer: 'kala', sort_order: id === V5 ? 142 : 141, scope: 'per_chart', is_active: false, has_writer: true, depends_on: [], has_runtime_evidence: false,
  target_table: 'kala_gochara_windows', ...over,
})

/** The existing frozen population: ordinary assets, a dependent pair, and an already RETIRED identity (inactive, has a writer, no dependencies — the lookalike). */
const population: NirmanaRegistryContractRow[] = [
  registryRow('bg_reference', { sort_order: 1 }),
  registryRow('bg_texts', { sort_order: 2, depends_on: ['bg_reference'] }),
  registryRow('ka_gochara_sweep', { layer: 'kala', sort_order: 90, is_active: false, catalog_status: 'RETIRED', superseded_by: 'bg_reference', data_disposition: 'RETAINED_AS_CAPITAL', has_runtime_evidence: false }),
]
const frozen = () => buildNirmanaBaselineCandidate(population)
const definition = (c = frozen()) => ({ definition_status: 'frozen' as const, manifest: c.manifest, manifest_sha256: c.manifest_sha256 })

describe('staged inert Gochara candidates — excluded while inert, visible the moment the shape changes', () => {
  it('the rule names exactly the two ids', () => {
    expect([...NIRMANA_STAGED_INERT_CANDIDATES].sort()).toEqual([V41, V5])
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
    const notInert = [...population, staged(V41, { has_runtime_evidence: true }), staged(V5, { has_runtime_evidence: true })]
    expect(() => buildNirmanaBaselineCandidate(notInert)).toThrow()                                    // assertFreezableManifest: execution_obligation 'unresolved'
    expect(() => assertManifestMatchesRegistryIdentity(frozen().manifest, notInert)).toThrow(/Frozen manifest contains 3 assets but the live registry contains 5/)
  })

  it.each([
    ['activated', { is_active: true }],
    ['gains a dependency', { depends_on: ['bg_reference'] }],
    ['has a receipt / build-run row', { has_runtime_evidence: true }],
    ['the loader gave no evidence column', { has_runtime_evidence: undefined }],
    ['the evidence column is NULL (unknown)', { has_runtime_evidence: null }],
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
    const active = staged(V5, { is_active: true, has_runtime_evidence: false, depends_on: ['bg_reference'] })
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
    const dormant = registryRow('bg_dormant', { is_active: false, has_runtime_evidence: false })
    expect(excludeNirmanaStagedInertCandidates([...population, dormant, staged(V41)]).map((r) => r.asset_id)).toEqual(['bg_reference', 'bg_texts', 'ka_gochara_sweep', 'bg_dormant'])
    expect(isNirmanaStagedInertCandidate(population[2])).toBe(false)
    expect(isNirmanaStagedInertCandidate(dormant)).toBe(false)
  })

  it('DIGEST STABILITY: the new column enters no digest — a 128-row frozen population is byte-identical with and without has_runtime_evidence', () => {
    const rows128: NirmanaRegistryContractRow[] = Array.from({ length: 128 }, (_, i) => registryRow(`bg_asset_${String(i).padStart(3, '0')}`, {
      sort_order: i + 1, depends_on: i === 0 ? [] : [`bg_asset_${String(i - 1).padStart(3, '0')}`],
    }))
    const withColumn = rows128.map((r, i) => ({ ...r, has_runtime_evidence: i % 2 === 0 }))            // present, with varying values
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
    expect(JSON.stringify(a)).not.toContain('has_runtime_evidence')
  })

  it('ONE predicate: receipts OR build_run_assets, only for the two ids (NULL otherwise); NO asset_throughput and NO function call', () => {
    const sql = runtimeEvidenceSql('registry')
    expect(sql).toContain("registry.asset_id IN ('ka_gochara_v4_41_candidate', 'ka_gochara_v5')")
    expect(sql).toContain('FROM public.asset_provenance_receipts rcpt WHERE rcpt.asset_id = registry.asset_id')
    expect(sql).toContain('FROM public.build_run_assets bra WHERE bra.asset_id = registry.asset_id')
    expect(sql).toMatch(/AS has_runtime_evidence$/)
    expect(sql).not.toContain('asset_throughput')                                     // the control and ingress writers hold no SELECT on it; a refresh row is not a build
    expect(sql).not.toContain('ka_gochara_staged_candidate_has_runtime_evidence')     // the SECURITY DEFINER function is a LATER protected migration (draft)
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
})
