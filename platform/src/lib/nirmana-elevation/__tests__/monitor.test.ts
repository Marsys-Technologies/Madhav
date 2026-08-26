import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import type { NirmanaRegistryContractRow } from '../definitions'
import { canonicalLabelCatalogueDigest } from '../labels'
import {
  buildNirmanaBaselineCandidate,
  classifyNirmanaDivergence,
} from '../monitor'

function registryRow(
  asset_id: string,
  overrides: Partial<NirmanaRegistryContractRow> = {},
): NirmanaRegistryContractRow {
  return {
    asset_id,
    layer: 'brahmagyan',
    depends_on: [],
    sort_order: 1,
    scope: 'global',
    asset_kind: 'data',
    catalog_status: 'CURRENT',
    is_active: true,
    has_writer: true,
    target_table: `${asset_id}_rows`,
    count_sql: `SELECT count(*) FROM ${asset_id}_rows`,
    integrity_check_sql: null,
    health_probe: null,
    natural_key_partition: null,
    superseded_by: null,
    data_disposition: null,
    dead_flag: null,
    sanskrit_name: null,
    english_name: null,
    english_description: null,
    ...overrides,
  }
}

const rows = [
  registryRow('bg_texts', {
    depends_on: ['bg_reference'],
    sort_order: 2,
    sanskrit_name: 'Grantha',
    english_name: 'Texts',
  }),
  registryRow('bg_reference', {
    sort_order: 1,
    english_name: 'Reference data',
    english_description: 'Authoritative reference values.',
  }),
]

function frozenDefinition(candidate = buildNirmanaBaselineCandidate(rows)) {
  return {
    definition_status: 'frozen' as const,
    manifest: candidate.manifest,
    manifest_sha256: candidate.manifest_sha256,
  }
}

describe('Nirmana elevation monitor baseline', () => {
  it('derives a freezable manifest, canonical digests, authoritative labels, and DAG waves', () => {
    const candidate = buildNirmanaBaselineCandidate(rows)

    expect(candidate.manifest.assets).toHaveLength(rows.length)
    expect(candidate.manifest.assets.map((asset) => [asset.asset_id, asset.wave_index])).toEqual([
      ['bg_reference', 0],
      ['bg_texts', 1],
    ])
    expect(candidate.manifest_sha256).toMatch(/^[a-f0-9]{64}$/)
    expect(candidate.catalogue_sha256).toMatch(/^[a-f0-9]{64}$/)
    expect(candidate.registry_identity_sha256).toMatch(/^[a-f0-9]{64}$/)
    expect(candidate.registry_contract_sha256).toMatch(/^[a-f0-9]{64}$/)
    expect(candidate.labels).toEqual(expect.arrayContaining([
      expect.objectContaining({
        asset_id: 'bg_reference',
        sanskrit_name: null,
        english_name: 'Reference data',
        description: 'Authoritative reference values.',
      }),
    ]))
    expect(candidate.catalogue_sha256).toBe(canonicalLabelCatalogueDigest(candidate.labels))
  })

  it('is independent of live registry row order', () => {
    const forward = buildNirmanaBaselineCandidate(rows)
    const reversed = buildNirmanaBaselineCandidate([...rows].reverse())

    expect(reversed).toEqual(forward)
  })

  it('keeps every absent human label null instead of synthesizing catalogue copy', () => {
    const candidate = buildNirmanaBaselineCandidate([
      registryRow('bg_uncatalogued', { sort_order: 1 }),
    ])

    expect(candidate.labels).toEqual([expect.objectContaining({
      asset_id: 'bg_uncatalogued',
      sanskrit_name: null,
      english_name: null,
      description: null,
    })])
    expect(candidate.catalogue_sha256).toMatch(/^[a-f0-9]{64}$/)
  })
})

describe('Nirmana elevation monitor divergence', () => {
  it('reports an absent accepted definition as a missing baseline', () => {
    const candidate = buildNirmanaBaselineCandidate(rows)

    expect(classifyNirmanaDivergence({ definition: null, candidate, observation: null })).toMatchObject({
      status: 'baseline_missing',
      affected_asset_ids: [],
      current_definition_sha256: null,
      candidate_definition_sha256: candidate.manifest_sha256,
    })
  })

  it('reports identity or DAG changes as plan adaptation with sorted affected assets', () => {
    const current = buildNirmanaBaselineCandidate(rows)
    const changedDag = buildNirmanaBaselineCandidate([
      registryRow('bg_texts', {
        depends_on: [],
        sort_order: 2,
        sanskrit_name: 'Grantha',
        english_name: 'Texts',
      }),
      registryRow('bg_archive', { sort_order: 3, english_name: 'Archive' }),
    ])

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(current),
      candidate: changedDag,
      observation: null,
    })).toMatchObject({
      status: 'plan_adaptation_required',
      affected_asset_ids: ['bg_archive', 'bg_reference', 'bg_texts'],
    })
  })

  it('reports mutable registry-contract changes as evidence refresh, not plan adaptation', () => {
    const current = buildNirmanaBaselineCandidate(rows)
    const changedContract = buildNirmanaBaselineCandidate(rows.map((row) => row.asset_id === 'bg_texts'
      ? { ...row, integrity_check_sql: 'SELECT true' }
      : row))

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(current),
      candidate: changedContract,
      observation: null,
    })).toMatchObject({
      status: 'evidence_refresh_required',
      affected_asset_ids: ['bg_texts'],
    })
  })

  it('treats dependency-array order alone as the same DAG and registry contract', () => {
    const dependencyRows = [
      registryRow('bg_alpha', { sort_order: 1, english_name: 'Alpha' }),
      registryRow('bg_beta', { sort_order: 2, english_name: 'Beta' }),
      registryRow('bg_target', {
        depends_on: ['bg_alpha', 'bg_beta'],
        sort_order: 3,
        english_name: 'Target',
      }),
    ]
    const current = buildNirmanaBaselineCandidate(dependencyRows)
    const reordered = buildNirmanaBaselineCandidate(dependencyRows.map((row) => row.asset_id === 'bg_target'
      ? { ...row, depends_on: ['bg_beta', 'bg_alpha'] }
      : row))

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(current),
      candidate: reordered,
      observation: null,
    })).toMatchObject({ status: 'in_sync', affected_asset_ids: [] })
    expect(reordered.manifest_sha256).toBe(current.manifest_sha256)
    expect(reordered.registry_contract_sha256).toBe(current.registry_contract_sha256)
  })

  it('reports an unchanged definition and registry as in sync', () => {
    const candidate = buildNirmanaBaselineCandidate(rows)

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(candidate),
      candidate,
      observation: null,
    })).toMatchObject({ status: 'in_sync', affected_asset_ids: [] })
  })

  it('reports a source read failure without presenting the last comparison as in sync', () => {
    const candidate = buildNirmanaBaselineCandidate(rows)

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(candidate),
      candidate,
      observation: { source_error_code: 'NIRMANA_SOURCE_UNAVAILABLE' },
    })).toMatchObject({ status: 'source_unavailable', affected_asset_ids: [] })
  })

  it('reports incomplete or drifted governed labels separately from plan identity', () => {
    const candidate = buildNirmanaBaselineCandidate(rows)

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(candidate),
      candidate,
      observation: {
        selected_catalogue_sha256: candidate.catalogue_sha256,
        selected_catalogue_asset_ids: ['bg_reference', 'bg_texts'],
        incomplete_label_asset_ids: ['bg_texts'],
      },
    })).toMatchObject({ status: 'label_refresh_required', affected_asset_ids: ['bg_texts'] })
  })

  it('reports release divergence separately from registry and evidence drift', () => {
    const candidate = buildNirmanaBaselineCandidate(rows)

    expect(classifyNirmanaDivergence({
      definition: frozenDefinition(candidate),
      candidate,
      observation: { release_in_sync: false },
    })).toMatchObject({ status: 'release_attention', affected_asset_ids: [] })
  })
})
