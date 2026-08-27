import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import {
  assertNirmanaL0WriterInventoryMatchesConvergence,
  NIRMANA_L0_ANALYSIS_RECEIPT_COUNT,
  NIRMANA_L0_ANALYSIS_RECEIPTS,
  NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE,
} from '@/generated/nirmana-l0-analysis-receipts'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
const transactionQueryMock = vi.fn()
const transactionReleaseMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
  getPool: () => ({
    connect: async () => ({ query: (...args: unknown[]) => transactionQueryMock(...args), release: transactionReleaseMock }),
  }),
}))

const releaseStatusMock = vi.fn()
const ciRunMock = vi.fn()
vi.mock('../release', () => ({
  loadNirmanaReleaseStatus: (...args: unknown[]) => releaseStatusMock(...args),
  verifyNirmanaCiRun: (...args: unknown[]) => ciRunMock(...args),
}))

import {
  assertFreezableManifest,
  acceptNirmanaBaselineCandidate,
  assertNirmanaGitCommitMatchesDeployment,
  canonicalManifestDigest,
  canonicalNirmanaOptimizationVerdictDigest,
  canonicalNirmanaAssetAnalysisDigestForRegistryRow,
  canonicalNirmanaProbeContractDigest,
  canonicalRegistryContractDigest,
  createNirmanaElevationDefinition,
  freezeNirmanaElevationDefinition,
  recordNirmanaElevationEvidence,
  supersedeNirmanaElevationDefinition,
  type NirmanaRegistryContractRow,
} from '../definitions'
import { buildNirmanaBaselineCandidate } from '../monitor'

const registry_contract = {
  sort_order: 1,
  scope: 'global' as const,
  asset_kind: 'data' as const,
  catalog_status: 'CURRENT' as const,
  is_active: true,
  has_writer: true,
  target_table: 'bg_prashna_rules',
  count_sql: 'SELECT count(*) FROM bg_prashna_rules',
  integrity_check_sql: null,
  health_probe: null,
  natural_key_partition: null,
  superseded_by: null,
  data_disposition: null,
  dead_flag: null,
}
const manifestAsset = {
  asset_id: 'bg_prashna_rules',
  layer: 'L0' as const,
  wave_index: 0,
  execution_obligation: 'build' as const,
  depends_on: [],
  registry_contract,
  registry_fingerprint_sha256: canonicalRegistryContractDigest({
    asset_id: 'bg_prashna_rules',
    layer: 'L0',
    depends_on: [],
    registry_contract,
  }),
}
const manifest = {
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  assets: [manifestAsset],
}
const historicalT0Manifest = JSON.parse(readFileSync(
  new URL('../../../../../00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_0.json', import.meta.url),
  'utf8',
))
const reconciledT0Manifest = JSON.parse(readFileSync(
  new URL('../../../../../00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_1.json', import.meta.url),
  'utf8',
))

function registryRowsFor(candidate: typeof manifest | typeof reconciledT0Manifest) {
  const layerNames = { L0: 'brahmagyan', L1: 'ganita', L2: 'bodha', L3: 'kala', L4: 'phala', L5: 'mimamsa' } as const
  return candidate.assets.map((asset: typeof manifestAsset) => ({
    asset_id: asset.asset_id,
    layer: layerNames[asset.layer],
    depends_on: asset.depends_on,
    frozen_manifest_asset: asset,
    ...asset.registry_contract,
  }))
}

const baselineObservationId = '30303030-3030-4030-8030-303030303030'

function baselineObservationFor(
  candidate: ReturnType<typeof buildNirmanaBaselineCandidate>,
  overrides: Record<string, unknown> = {},
) {
  return {
    id: baselineObservationId,
    observed_at: '2026-08-26T05:00:01.000Z',
    status: 'baseline_missing',
    current_definition_sha256: null,
    candidate_definition_sha256: candidate.manifest_sha256,
    registry_identity_sha256: candidate.registry_identity_sha256,
    registry_contract_sha256: candidate.registry_contract_sha256,
    candidate_catalogue_sha256: candidate.catalogue_sha256,
    source_state: 'available',
    source_observed_at: '2026-08-26T05:00:00.000Z',
    freshness_state: 'fresh',
    freshness_deadline_at: '2026-08-26T05:15:00.000Z',
    source_error_code: null,
    currently_fresh: true,
    ...overrides,
  }
}

function useEvidenceTransaction({
  existing = [],
  current = true,
}: {
  existing?: unknown[]
  current?: boolean
} = {}) {
  transactionQueryMock.mockImplementation((sql: string, params?: unknown[]) => {
    const statement = String(sql)
    if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement) || statement.includes('pg_advisory_xact_lock')) {
      return Promise.resolve({ rows: [] })
    }
    if (statement.includes('SELECT campaign_id, definition_revision')) return Promise.resolve({ rows: existing })
    if (statement.includes('AS current')) return Promise.resolve({ rows: [{ current }] })
    return queryMock(sql, params)
  })
}

function currentRebuildReceipt() {
  const currentRegistryRow = registryRowsFor(manifest)[0]
  const binding = {
    registry_fingerprint_sha256: canonicalRegistryContractDigest({
      asset_id: currentRegistryRow.asset_id, layer: 'L0', depends_on: currentRegistryRow.depends_on,
      registry_contract: registry_contract,
    }),
    analysis_digest: canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', currentRegistryRow, manifestAsset),
  }
  const decision = {
    ...binding,
    verdict: 'optimize' as const,
    basis: {
      measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'optimize' as const, summary: 'A current change is required.', output_contract: 'digest_identical' as const },
  }
  const implementation = {
    ...binding,
    decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision),
    implementation_digest: 'c'.repeat(64),
  }
  return {
    currentRegistryRow,
    decision,
    implementation,
    payload: {
      ...binding,
      build_run_id: '482012f1-710e-4a25-994a-93821f5871aa',
      decision_digest: implementation.decision_digest,
      implementation_digest: implementation.implementation_digest,
      output_digest: 'a'.repeat(64), output_digest_spec_sha256: 'b'.repeat(64),
    },
  }
}

function mockCurrentRebuildEvidence(proven: boolean) {
  const receipt = currentRebuildReceipt()
  queryMock.mockImplementation((sql: string) => {
    const statement = String(sql)
    if (statement.includes('FROM asset_registry registry')) return Promise.resolve({ rows: [receipt.currentRegistryRow] })
    if (statement.includes('SELECT manifest, manifest_sha256')) return Promise.resolve({ rows: [{ manifest, manifest_sha256: canonicalManifestDigest(manifest), manifest_asset_count: 1 }] })
    if (statement.includes("event_type = 'optimization_verdict_accepted'")) return Promise.resolve({ rows: [{ evidence_payload: receipt.decision, source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}` }] })
    if (statement.includes("event_type = 'implementation_accepted'")) return Promise.resolve({ rows: [{ evidence_payload: receipt.implementation, source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}` }] })
    if (statement.includes('FROM build_runs run')) return Promise.resolve({ rows: [{ proven }] })
    if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [{ event_id: '1' }] })
    return Promise.resolve({ rows: [] })
  })
  return receipt.payload
}

describe('Nirmana elevation definition repository', () => {
  const acceptedReceiptIt = NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE ? it : it.skip

  beforeEach(() => {
    queryMock.mockReset()
    transactionQueryMock.mockReset()
    transactionReleaseMock.mockReset()
    releaseStatusMock.mockReset()
    ciRunMock.mockReset()
  })

  it('derives one canonical SHA-256 digest for the validated manifest', () => {
    expect(canonicalManifestDigest(manifest)).toMatch(/^[a-f0-9]{64}$/)
  })

  it('accepts only the exact live baseline candidate and its label catalogue in one serializable transaction', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      sanskrit_name: 'Prashna Niyama',
      english_name: 'Prashna rules',
      english_description: 'Governed horary reference rules.',
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate)] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_definitions')) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes("SET definition_status = 'frozen'")) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes('SELECT definition_status, manifest')) {
        return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      }
      if (statement.includes('FROM nirmana_elevation_campaign_events')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT count(*)::int AS label_count')) {
        return Promise.resolve({ rows: [{ label_count: 0, digest_matches: false }] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_asset_labels')) {
        return Promise.resolve({ rowCount: candidate.labels.length, rows: [] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) {
        return Promise.resolve({ rowCount: 1, rows: [{ event_id: 'receipt-1' }] })
      }
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation',
      source_observation_id: baselineObservationId,
      definition_revision: 'ntap-v1',
      expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
      created_by: 'admin-1',
    })).resolves.toBe('created')

    const transactionSql = transactionQueryMock.mock.calls.map(([sql]) => String(sql))
    expect(transactionSql).toEqual(expect.arrayContaining([
      expect.stringContaining('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE'),
      expect.stringContaining('FROM nirmana_elevation_monitor_observations'),
      expect.stringContaining('INSERT INTO nirmana_elevation_campaign_definitions'),
      expect.stringContaining("SET definition_status = 'frozen'"),
      expect.stringContaining('INSERT INTO nirmana_elevation_asset_labels'),
      expect.stringContaining("'asset_label_catalogue_accepted'"),
    ]))
    expect(transactionSql.join('\n')).not.toContain('stage_transition_accepted')
    expect(transactionSql.join('\n')).not.toContain('asset_frozen')
    const receiptCall = transactionQueryMock.mock.calls.find(([sql]) =>
      String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))
    expect(JSON.parse(String(receiptCall?.[1]?.[4]))).toEqual({
      catalogue_sha256: candidate.catalogue_sha256,
      asset_count: candidate.labels.length,
      audit_provenance: 'normative',
      source_observation_id: baselineObservationId,
      source_observation_observed_at: '2026-08-26T05:00:01.000Z',
      source_snapshot_observed_at: '2026-08-26T05:00:00.000Z',
      source_freshness_deadline_at: '2026-08-26T05:15:00.000Z',
      candidate_manifest_sha256: candidate.manifest_sha256,
      registry_identity_sha256: candidate.registry_identity_sha256,
      registry_contract_sha256: candidate.registry_contract_sha256,
      candidate_catalogue_sha256: candidate.catalogue_sha256,
    })
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('accepts an all-null registry label using the deterministic catalogue placeholder', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      sanskrit_name: null,
      english_name: null,
      english_description: null,
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate)] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_definitions')) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes("SET definition_status = 'frozen'")) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes('SELECT definition_status, manifest')) {
        return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      }
      if (statement.includes('FROM nirmana_elevation_campaign_events')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT count(*)::int AS label_count')) {
        return Promise.resolve({ rows: [{ label_count: 0, digest_matches: false }] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_asset_labels')) {
        return Promise.resolve({ rowCount: candidate.labels.length, rows: [] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) {
        return Promise.resolve({ rowCount: 1, rows: [{ event_id: 'receipt-1' }] })
      }
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation',
      source_observation_id: baselineObservationId,
      definition_revision: 'ntap-v1',
      expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
      created_by: 'admin-1',
    })).resolves.toBe('created')

    const labelInsert = transactionQueryMock.mock.calls.find(([sql]) =>
      String(sql).includes('INSERT INTO nirmana_elevation_asset_labels'))
    expect(labelInsert?.[1]).toEqual(expect.arrayContaining([
      expect.stringContaining('Not yet catalogued'),
    ]))
  })

  it('rejects a stale baseline candidate digest after re-reading the live registry', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      english_name: 'Prashna rules',
      sanskrit_name: null,
      english_description: null,
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate)] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation', source_observation_id: baselineObservationId, definition_revision: 'ntap-v1',
      expected_candidate_sha256: 'f'.repeat(64),
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
      created_by: 'admin-1',
    })).rejects.toThrow(/candidate changed/i)
    expect(transactionQueryMock.mock.calls.map(([sql]) => String(sql))).toContain('ROLLBACK')
  })

  it('rejects a baseline candidate sourced from an observation that is no longer fresh', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      english_name: 'Prashna rules',
      sanskrit_name: null,
      english_description: null,
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate, { currently_fresh: false })] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_definitions')) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes("SET definition_status = 'frozen'")) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes('SELECT definition_status, manifest')) {
        return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      }
      if (statement.includes('FROM nirmana_elevation_campaign_events')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT count(*)::int AS label_count')) {
        return Promise.resolve({ rows: [{ label_count: 0, digest_matches: false }] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_asset_labels')) {
        return Promise.resolve({ rowCount: candidate.labels.length, rows: [] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) {
        return Promise.resolve({ rowCount: 1, rows: [{ event_id: 'receipt-1' }] })
      }
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation', source_observation_id: baselineObservationId,
      definition_revision: 'ntap-v1', expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256, created_by: 'admin-1',
    })).rejects.toThrow(/fresh/i)
    const transactionSql = transactionQueryMock.mock.calls.map(([sql]) => String(sql)).join('\n')
    expect(transactionSql).not.toContain('INSERT INTO nirmana_elevation_campaign_definitions')
    expect(transactionSql).not.toContain('INSERT INTO nirmana_elevation_asset_labels')
  })

  it('returns idempotent only for an exact frozen candidate and exact accepted catalogue receipt', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      english_name: 'Prashna rules',
      sanskrit_name: null,
      english_description: null,
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [{
          definition_revision: 'ntap-v1', definition_status: 'frozen',
          manifest: candidate.manifest, manifest_sha256: candidate.manifest_sha256,
          created_by: 'admin-1', superseded_at: null,
        }] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate)] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      if (statement.includes('SELECT definition_status, manifest')) {
        return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      }
      if (statement.includes('FROM nirmana_elevation_campaign_events')) {
        return Promise.resolve({ rows: [{
          event_type: 'asset_label_catalogue_accepted', entity_type: 'label_catalogue',
          entity_id: 'ntap-v1', layer: null,
          evidence_payload: {
            catalogue_sha256: candidate.catalogue_sha256,
            asset_count: candidate.labels.length,
            audit_provenance: 'normative',
            source_observation_id: baselineObservationId,
            source_observation_observed_at: '2026-08-26T05:00:01.000Z',
            source_snapshot_observed_at: '2026-08-26T05:00:00.000Z',
            source_freshness_deadline_at: '2026-08-26T05:15:00.000Z',
            candidate_manifest_sha256: candidate.manifest_sha256,
            registry_identity_sha256: candidate.registry_identity_sha256,
            registry_contract_sha256: candidate.registry_contract_sha256,
            candidate_catalogue_sha256: candidate.catalogue_sha256,
          },
          source_kind: 'governed_catalogue', source_ref: 'label_catalogue:ntap-v1',
        }] })
      }
      if (statement.includes('SELECT count(*)::int AS label_count')) {
        return Promise.resolve({ rows: [{ label_count: candidate.labels.length, digest_matches: true }] })
      }
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation', source_observation_id: baselineObservationId, definition_revision: 'ntap-v1',
      expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
      created_by: 'admin-1',
    })).resolves.toBe('idempotent')
    const transactionSql = transactionQueryMock.mock.calls.map(([sql]) => String(sql)).join('\n')
    expect(transactionSql).not.toContain('INSERT INTO nirmana_elevation_campaign_definitions')
    expect(transactionSql).not.toContain('INSERT INTO nirmana_elevation_asset_labels')
  })

  it('rejects an idempotency replay when the normative receipt names a different source observation', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      english_name: 'Prashna rules', sanskrit_name: null, english_description: null,
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [{
          definition_revision: 'ntap-v1', definition_status: 'frozen',
          manifest: candidate.manifest, manifest_sha256: candidate.manifest_sha256,
          created_by: 'admin-1', superseded_at: null,
        }] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate)] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      if (statement.includes('SELECT definition_status, manifest')) {
        return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      }
      if (statement.includes('FROM nirmana_elevation_campaign_events')) {
        return Promise.resolve({ rows: [{
          event_type: 'asset_label_catalogue_accepted', entity_type: 'label_catalogue',
          entity_id: 'ntap-v1', layer: null,
          evidence_payload: {
            catalogue_sha256: candidate.catalogue_sha256,
            asset_count: candidate.labels.length,
            audit_provenance: 'normative',
            source_observation_id: '40404040-4040-4040-8040-404040404040',
            source_observation_observed_at: '2026-08-26T05:00:01.000Z',
            source_snapshot_observed_at: '2026-08-26T05:00:00.000Z',
            source_freshness_deadline_at: '2026-08-26T05:15:00.000Z',
            candidate_manifest_sha256: candidate.manifest_sha256,
            registry_identity_sha256: candidate.registry_identity_sha256,
            registry_contract_sha256: candidate.registry_contract_sha256,
            candidate_catalogue_sha256: candidate.catalogue_sha256,
          },
          source_kind: 'governed_catalogue', source_ref: 'label_catalogue:ntap-v1',
        }] })
      }
      if (statement.includes('SELECT count(*)::int AS label_count')) {
        return Promise.resolve({ rows: [{ label_count: candidate.labels.length, digest_matches: true }] })
      }
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation', source_observation_id: baselineObservationId,
      definition_revision: 'ntap-v1', expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256, created_by: 'admin-1',
    })).rejects.toThrow(/exact accepted label catalogue/i)
    expect(transactionQueryMock.mock.calls.map(([sql]) => String(sql))).toContain('ROLLBACK')
  })

  it('loses a competing-current-definition race as a conflict without creating baseline state', async () => {
    const liveRows = registryRowsFor(manifest).map((row: NirmanaRegistryContractRow) => ({
      ...row,
      english_name: 'Prashna rules', sanskrit_name: null, english_description: null,
    }))
    const candidate = buildNirmanaBaselineCandidate(liveRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [{
          definition_revision: 'competing-v1', definition_status: 'frozen', manifest,
          manifest_sha256: canonicalManifestDigest(manifest), created_by: 'other-admin', superseded_at: null,
        }] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [baselineObservationFor(candidate)] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: liveRows })
      throw new Error(`Unexpected SQL: ${statement}`)
    })

    await expect(acceptNirmanaBaselineCandidate({
      campaign_id: 'nirmana-elevation', source_observation_id: baselineObservationId, definition_revision: 'ntap-v1',
      expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
      created_by: 'admin-1',
    })).rejects.toThrow(/different current campaign definition/i)
    const transactionSql = transactionQueryMock.mock.calls.map(([sql]) => String(sql)).join('\n')
    expect(transactionSql).not.toContain('INSERT INTO nirmana_elevation_campaign_definitions')
    expect(transactionSql).not.toContain('INSERT INTO nirmana_elevation_asset_labels')
    expect(transactionSql).toContain('ROLLBACK')
  })

  it('keeps grounded receipt bases all-or-none against the pinned convergence inventory', () => {
    if (NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE) {
      expect(Object.keys(NIRMANA_L0_ANALYSIS_RECEIPTS)).toHaveLength(NIRMANA_L0_ANALYSIS_RECEIPT_COUNT)
      expect(Object.keys(NIRMANA_L0_ANALYSIS_RECEIPTS).sort()).toEqual(
        reconciledT0Manifest.assets.filter((asset: typeof manifestAsset) => asset.layer === 'L0').map((asset: typeof manifestAsset) => asset.asset_id).sort(),
      )
      expect(NIRMANA_L0_ANALYSIS_RECEIPTS.bg_prashna_rules.writer_digest_sha256).toMatch(/^[a-f0-9]{64}$/)
      expect(NIRMANA_L0_ANALYSIS_RECEIPTS.bg_panchanga.writer_digest_sha256).toBeNull()
    } else {
      expect(NIRMANA_L0_ANALYSIS_RECEIPTS).toEqual({})
    }
  })

  it('rejects a same-count L0 writer substitution against the pinned convergence inventory', () => {
    const substituted = Object.fromEntries(Object.entries(writerDigestInventory.writers)
      .filter(([assetId]) => assetId.startsWith('bg_')))
    substituted.bg_prashna_rules = 'f'.repeat(64)

    expect(() => assertNirmanaL0WriterInventoryMatchesConvergence(substituted)).toThrow(/convergence inventory/i)
  })

  it('requires the frozen manifest to pin its campaign chart', () => {
    expect(() => canonicalManifestDigest({ assets: manifest.assets })).toThrow(/chart_id/i)
    expect(() => canonicalManifestDigest({ ...manifest, chart_id: '11111111-1111-4111-8111-111111111111' })).toThrow(/chart_id/i)
  })

  it('gives JSONB-equivalent manifests the same digest regardless of object-key order', () => {
    const reordered = {
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      assets: [{
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        registry_contract: { ...registry_contract },
        depends_on: [],
        execution_obligation: 'build',
        wave_index: 0,
        layer: 'L0',
        asset_id: 'bg_prashna_rules',
      }],
    }
    expect(canonicalManifestDigest(reordered)).toBe(canonicalManifestDigest(manifest))
  })

  it('accepts every formal non-build execution obligation in a frozen denominator', () => {
    const nonBuildManifest = {
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      assets: [
        { asset_id: 'bg_non_build_producer', layer: 'L0', execution_obligation: 'build' },
        ...['probe', 'static_acceptance', 'source_acceptance', 'empty_acceptance', 'retired_with_disposition'].map((execution_obligation, index) => ({
          asset_id: `bg_non_build_${index}`,
          layer: 'L0',
          execution_obligation,
        })),
        { asset_id: 'bg_non_build_covered', layer: 'L0', execution_obligation: 'producer_covered', producer_id: 'bg_non_build_producer' },
      ],
    }

    expect(() => canonicalManifestDigest(nonBuildManifest)).not.toThrow()
  })

  it('preserves the immutable historical T0 v1.0 definition bytes and digest', () => {
    expect(historicalT0Manifest.assets).toHaveLength(128)
    expect(canonicalManifestDigest(historicalT0Manifest)).toBe('c0097895ab6b5318e8b9a2c34de34f7fe685eedfe9b8fb2293abe78593a5a3c4')
    expect(() => assertFreezableManifest(historicalT0Manifest)).not.toThrow()
  })

  it('validates the full post-626 T0 v1.1 manifest, exact DAG waves, and registry fingerprints', async () => {
    expect(reconciledT0Manifest.assets).toHaveLength(128)
    expect(canonicalManifestDigest(reconciledT0Manifest)).toBe('faa4d6b08dcde6c64efedc11c56561f24f8832ec92d2b6680660ba94de85f4a8')
    expect(() => assertFreezableManifest(reconciledT0Manifest)).not.toThrow()

    const exactAssets = new Map(reconciledT0Manifest.assets.map((asset: typeof manifestAsset) => [asset.asset_id, asset]))
    expect(exactAssets.get('bg_gochara_arcs')).toMatchObject({ wave_index: 1, depends_on: ['bg_ephemeris'] })
    expect(exactAssets.get('bg_kp_sublord_division')).toMatchObject({ wave_index: 1, depends_on: ['bg_nakshatra'] })
    expect(exactAssets.get('bg_parihara_rules')).toMatchObject({ wave_index: 2, depends_on: ['bg_doshas', 'bg_texts'] })

    queryMock
      .mockResolvedValueOnce({ rows: registryRowsFor(reconciledT0Manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      definition_revision: 't0-v1',
      manifest: reconciledT0Manifest,
      manifest_sha256: canonicalManifestDigest(reconciledT0Manifest),
    })).resolves.toBe('frozen')
  })

  it('rejects a mismatched digest before attempting an insert or freeze', async () => {
    await expect(createNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      definition_status: 'reconciling',
      manifest,
      manifest_sha256: '0'.repeat(64),
      created_by: 'admin-1',
    })).rejects.toThrow(/digest/i)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('persists only a validated definition revision', async () => {
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    await expect(createNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      definition_status: 'reconciling',
      manifest,
      manifest_sha256: canonicalManifestDigest(manifest),
      created_by: 'admin-1',
    })).resolves.toBe('created')

    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(queryMock.mock.calls[0][0]).toContain('ON CONFLICT (campaign_id, definition_revision) DO NOTHING')
  })

  it('accepts an exact retried definition revision without overwriting its first receipt', async () => {
    queryMock
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{ definition_status: 'reconciling', manifest_sha256: canonicalManifestDigest(manifest) }] })

    await expect(createNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'reconciling', manifest,
      manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-2',
    })).resolves.toBe('idempotent')
    expect(queryMock).toHaveBeenCalledTimes(2)
  })

  it('freezes only the exact prior reconciling manifest and accepts an exact retry', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256: canonicalManifestDigest(manifest),
    })).resolves.toBe('frozen')

    queryMock
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{ definition_status: 'frozen', manifest_sha256: canonicalManifestDigest(manifest) }] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256: canonicalManifestDigest(manifest),
    })).resolves.toBe('idempotent')
  })

  it('atomically supersedes the exact current frozen definition with a live-registry-matched frozen revision', async () => {
    const oldDigest = 'c'.repeat(64)
    transactionQueryMock
      .mockResolvedValueOnce({}) // BEGIN
      .mockResolvedValueOnce({}) // SET TRANSACTION ISOLATION LEVEL SERIALIZABLE
      .mockResolvedValueOnce({}) // campaign/revision advisory lock
      .mockResolvedValueOnce({ rows: [{
        definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
        manifest, created_by: 'admin-0', superseded_at: null,
      }] })
      .mockResolvedValueOnce({}) // dispatcher wave advisory lock
      .mockResolvedValueOnce({}) // evidence/build_runs table locks
      .mockResolvedValueOnce({ rows: [{ event_count: 0, build_run_count: 0 }] })
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_revision: 'v1' }] })
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_revision: 'v2' }] })
      .mockResolvedValueOnce({}) // COMMIT

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      expected_current_revision: 'v1',
      expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2',
      new_manifest: manifest,
      new_manifest_sha256: canonicalManifestDigest(manifest),
      created_by: 'admin-1',
    })).resolves.toBe('superseded')

    expect(transactionQueryMock.mock.calls.map(([sql]) => String(sql).trim().split(/\s+/).slice(0, 2).join(' ')))
      .toEqual([
        'BEGIN', 'SET TRANSACTION', 'SELECT pg_advisory_xact_lock(hashtextextended($1,', 'SELECT definition_revision,', 'SELECT pg_advisory_xact_lock(hashtextextended($1,',
        'LOCK TABLE', 'SELECT (SELECT', 'SELECT asset_id,', 'UPDATE nirmana_elevation_campaign_definitions', 'INSERT INTO', 'COMMIT',
      ])
    expect(transactionQueryMock.mock.calls[2][1]).toEqual(['nirmana-elevation:nirmana-elevation:v1'])
    expect(transactionQueryMock.mock.calls[4][1]).toEqual(['nirmana-elevation:v1:L0:wave-0'])
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('treats only an exact completed supersession retry as idempotent', async () => {
    const oldDigest = 'c'.repeat(64)
    const newDigest = canonicalManifestDigest(manifest)
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [
        { definition_revision: 'v1', definition_status: 'superseded', manifest_sha256: oldDigest, manifest, created_by: 'admin-0', superseded_at: '2026-08-26T00:00:00.000Z' },
        { definition_revision: 'v2', definition_status: 'frozen', manifest_sha256: newDigest, manifest, created_by: 'admin-1', superseded_at: null },
      ] })
      .mockResolvedValueOnce({})

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2', new_manifest: manifest, new_manifest_sha256: newDigest, created_by: 'admin-2',
    })).resolves.toBe('idempotent')
    expect(transactionQueryMock).toHaveBeenCalledTimes(5)
    expect(String(transactionQueryMock.mock.calls[4][0])).toBe('COMMIT')
  })

  it('rolls back and leaves the old definition current when the replacement insert fails', async () => {
    const oldDigest = 'c'.repeat(64)
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{
        definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
        manifest, created_by: 'admin-0', superseded_at: null,
      }] })
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{ event_count: 0, build_run_count: 0 }] })
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_revision: 'v1' }] })
      .mockRejectedValueOnce(new Error('replacement insert failed'))
      .mockResolvedValueOnce({})

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2', new_manifest: manifest, new_manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-1',
    })).rejects.toThrow('replacement insert failed')
    expect(String(transactionQueryMock.mock.calls.at(-1)?.[0])).toBe('ROLLBACK')
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('refuses supersession when the expected frozen revision has campaign evidence', async () => {
    const oldDigest = 'c'.repeat(64)
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{
        definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
        manifest, created_by: 'admin-0', superseded_at: null,
      }] })
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{ event_count: 1, build_run_count: 0 }] })
      .mockResolvedValueOnce({})

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2', new_manifest: manifest, new_manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-1',
    })).rejects.toThrow(/already has campaign events/i)
    expect(String(transactionQueryMock.mock.calls.at(-1)?.[0])).toBe('ROLLBACK')
  })

  it('refuses supersession when a build-run manifest identifies the expected frozen revision', async () => {
    const oldDigest = 'c'.repeat(64)
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{
        definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
        manifest, created_by: 'admin-0', superseded_at: null,
      }] })
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{ event_count: 0, build_run_count: 1 }] })
      .mockResolvedValueOnce({})

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2', new_manifest: manifest, new_manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-1',
    })).rejects.toThrow(/already has build runs/i)
    const preconditionCall = transactionQueryMock.mock.calls[6]
    expect(String(preconditionCall[0])).toContain("plan_manifest #>> '{campaign_control,campaign_id}'")
    expect(String(preconditionCall[0])).toContain("plan_manifest #>> '{campaign_control,definition_revision}'")
    expect(preconditionCall[1]).toEqual(['nirmana-elevation', 'v1'])
    expect(String(transactionQueryMock.mock.calls.at(-1)?.[0])).toBe('ROLLBACK')
  })

  it('allows supersession when build runs belong to another campaign definition', async () => {
    const oldDigest = 'c'.repeat(64)
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{
        definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
        manifest, created_by: 'admin-0', superseded_at: null,
      }] })
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [{ event_count: 0, build_run_count: 0 }] })
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_revision: 'v1' }] })
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_revision: 'v2' }] })
      .mockResolvedValueOnce({})

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2', new_manifest: manifest, new_manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-1',
    })).resolves.toBe('superseded')
  })

  it('rejects reuse of an existing replacement revision before superseding the current definition', async () => {
    const oldDigest = 'c'.repeat(64)
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [
        {
          definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
          manifest, created_by: 'admin-0', superseded_at: null,
        },
        {
          definition_revision: 'v2', definition_status: 'superseded', manifest_sha256: 'd'.repeat(64),
          manifest, created_by: 'admin-other', superseded_at: '2026-08-26T00:00:00.000Z',
        },
      ] })
      .mockResolvedValueOnce({})

    await expect(supersedeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      new_definition_revision: 'v2', new_manifest: manifest, new_manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-1',
    })).rejects.toThrow(/revision already exists/i)
    expect(transactionQueryMock).toHaveBeenCalledTimes(5)
    expect(String(transactionQueryMock.mock.calls[4][0])).toBe('ROLLBACK')
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('refuses to freeze when any pinned registry contract differs from the live row', async () => {
    const driftedRows = registryRowsFor(manifest)
    driftedRows[0].count_sql = 'SELECT count(*) FROM a_different_table'
    queryMock.mockResolvedValueOnce({ rows: driftedRows })

    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest,
      manifest_sha256: canonicalManifestDigest(manifest),
    })).rejects.toThrow(/live registry contract/i)
    expect(queryMock).toHaveBeenCalledTimes(1)
  })

  it('locks the campaign revision before validation and records evidence on one dedicated connection', async () => {
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (statement === 'BEGIN' || statement === 'COMMIT') return Promise.resolve({})
      if (statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT campaign_id, definition_revision')) return Promise.resolve({ rows: [] })
      if (statement.includes('definition_status = \'frozen\'')) return Promise.resolve({ rows: [{ current: true }] })
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [{ event_id: 'event-1' }] })
      return Promise.resolve({ rows: [] })
    })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
      event_type: 'test_receipt',
      entity_type: 'test',
      entity_id: 'bg_prashna_rules',
      layer: 'L0',
      evidence_payload: { receipt: 'test' },
      source_kind: 'test',
      source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z',
      recorded_by: 'admin-1',
    })).resolves.toBe('created')

    expect(transactionQueryMock.mock.calls.map(([sql]) => String(sql).trim().split(/\s+/).slice(0, 2).join(' ')))
      .toEqual(['BEGIN', 'SELECT pg_advisory_xact_lock(hashtextextended($1,', 'SELECT campaign_id,', 'SELECT EXISTS', 'INSERT INTO', 'COMMIT'])
    expect(transactionQueryMock.mock.calls[1][1]).toEqual(['nirmana-elevation:nirmana-elevation:v1'])
    expect(queryMock).not.toHaveBeenCalled()
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('rolls back and releases the evidence transaction when validation fails', async () => {
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ current: false }] })
      .mockResolvedValueOnce({})

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:stale',
      event_type: 'test_receipt', entity_type: 'test', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { receipt: 'test' }, source_kind: 'test', source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/current frozen definition/i)
    expect(String(transactionQueryMock.mock.calls.at(-1)?.[0])).toBe('ROLLBACK')
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('rejects a syntactically valid asset-analysis digest that is not the deployed canonical receipt', async () => {
    useEvidenceTransaction()
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM asset_registry registry')) return Promise.resolve({ rows: registryRowsFor(manifest) })
      if (String(sql).includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [] })
      return Promise.resolve({ rows: [] })
    })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:analysis:forged',
      event_type: 'asset_analysis_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        analysis_digest: 'f'.repeat(64),
      },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE
      ? /canonical deployed analysis receipt/i
      : /reconstructable deployed analysis receipt/i)
    if (NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE) {
      expect(queryMock).toHaveBeenCalled()
    } else {
      expect(queryMock).not.toHaveBeenCalled()
    }
  })

  it('requires a configured production deployment SHA and matches the receipt source to it', () => {
    expect(() => assertNirmanaGitCommitMatchesDeployment(`git:${'a'.repeat(40)}`, {
      nodeEnv: 'production',
      deployedSha: undefined,
    })).toThrow(/NIRMANA_DEPLOYED_SHA/)

    expect(() => assertNirmanaGitCommitMatchesDeployment(`git:${'a'.repeat(40)}`, {
      nodeEnv: 'production',
      deployedSha: 'b'.repeat(40),
    })).toThrow(/currently deployed commit/i)

    expect(() => assertNirmanaGitCommitMatchesDeployment(`git:${'a'.repeat(40)}`, {
      nodeEnv: 'production',
      deployedSha: 'a'.repeat(40),
    })).not.toThrow()
  })

  it('permits an exact Git source in test/dev only when no deployment SHA is configured', () => {
    expect(() => assertNirmanaGitCommitMatchesDeployment(`git:${'a'.repeat(40)}`, {
      nodeEnv: 'test',
      deployedSha: undefined,
    })).not.toThrow()
    expect(() => assertNirmanaGitCommitMatchesDeployment(`git:${'a'.repeat(40)}`, {
      nodeEnv: 'development',
      deployedSha: 'not-a-sha',
    })).toThrow(/NIRMANA_DEPLOYED_SHA/)
  })

  acceptedReceiptIt('rejects an optimization verdict unless an exact accepted analysis binds the current contract', async () => {
    const currentRegistryRow = registryRowsFor(manifest)[0]
    const analysisDigest = canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', currentRegistryRow, manifestAsset)
    useEvidenceTransaction()
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM asset_registry registry')) return Promise.resolve({ rows: [currentRegistryRow] })
      if (String(sql).includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [] })
      return Promise.resolve({ rows: [] })
    })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:optimization:unbound',
      event_type: 'optimization_verdict_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        analysis_digest: analysisDigest,
        verdict: 'examined_and_already_efficient',
        basis: {
          measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
          evidence_refs: ['git:test-evidence'],
        },
        proposal: { action: 'no_change', summary: 'No measured hotspot warrants a change.', output_contract: 'digest_identical' },
      },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/matching accepted asset analysis/i)
    expect(queryMock).toHaveBeenCalled()
  })

  acceptedReceiptIt('records a strict optimization verdict when it binds the exact current accepted analysis', async () => {
    const currentRegistryRow = registryRowsFor(manifest)[0]
    const analysisDigest = canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', currentRegistryRow, manifestAsset)
    useEvidenceTransaction()
    queryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (statement.includes('FROM asset_registry registry')) return Promise.resolve({ rows: [currentRegistryRow] })
      if (statement.includes("event_type = 'asset_analysis_accepted'")) {
        return Promise.resolve({ rows: [{ accepted_count: 1 }] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [] })
      return Promise.resolve({ rows: [] })
    })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:optimization:accepted',
      event_type: 'optimization_verdict_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        analysis_digest: analysisDigest,
        verdict: 'examined_and_already_efficient',
        basis: {
          measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
          evidence_refs: ['git:test-evidence'],
        },
        proposal: { action: 'no_change', summary: 'No measured hotspot warrants a change.', output_contract: 'digest_identical' },
      },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).resolves.toBe('created')
    expect(queryMock.mock.calls.some(([sql]) => String(sql).includes("event_type = 'asset_analysis_accepted'"))).toBe(true)
  })

  acceptedReceiptIt('rejects an optimization verdict when current accepted analysis receipts are ambiguous', async () => {
    const currentRegistryRow = registryRowsFor(manifest)[0]
    const analysisDigest = canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', currentRegistryRow, manifestAsset)
    useEvidenceTransaction()
    queryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (statement.includes('FROM asset_registry registry')) return Promise.resolve({ rows: [currentRegistryRow] })
      if (statement.includes("event_type = 'asset_analysis_accepted'")) {
        return Promise.resolve({ rows: [{ accepted: true, accepted_count: 2 }] })
      }
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [] })
      return Promise.resolve({ rows: [] })
    })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:optimization:ambiguous',
      event_type: 'optimization_verdict_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        analysis_digest: analysisDigest,
        verdict: 'examined_and_already_efficient',
        basis: {
          measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
          evidence_refs: ['git:test-evidence'],
        },
        proposal: { action: 'no_change', summary: 'No measured hotspot warrants a change.', output_contract: 'digest_identical' },
      },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/ambiguous/i)
    expect(queryMock.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(false)
  })

  acceptedReceiptIt.each([
    ['registry fingerprint', 'f'.repeat(64), null],
    ['analysis digest', manifestAsset.registry_fingerprint_sha256, 'f'.repeat(64)],
  ])('rejects an optimization verdict with a stale or mismatched %s', async (_caseName, registryFingerprint, digestOverride) => {
    const currentRegistryRow = registryRowsFor(manifest)[0]
    const currentDigest = canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', currentRegistryRow, manifestAsset)
    useEvidenceTransaction()
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM asset_registry registry')) return Promise.resolve({ rows: [currentRegistryRow] })
      return Promise.resolve({ rows: [] })
    })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: `asset:bg_prashna_rules:optimization:${_caseName}`,
      event_type: 'optimization_verdict_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: registryFingerprint,
        analysis_digest: digestOverride ?? currentDigest,
        verdict: 'examined_and_already_efficient',
        basis: {
          measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
          evidence_refs: ['git:test-evidence'],
        },
        proposal: { action: 'no_change', summary: 'No measured hotspot warrants a change.', output_contract: 'digest_identical' },
      },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/does not match/i)
    expect(queryMock.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(false)
  })

  acceptedReceiptIt('uses the current live registry operational contract for a probe after a frozen T0 contract drifts', async () => {
    const frozenProbeContract = {
      ...registry_contract,
      asset_kind: 'service' as const,
      health_probe: { path: '/health/legacy', method: 'GET' },
    }
    const frozenProbeAsset = {
      ...manifestAsset,
      execution_obligation: 'probe' as const,
      registry_contract: frozenProbeContract,
      registry_fingerprint_sha256: canonicalRegistryContractDigest({
        asset_id: manifestAsset.asset_id, layer: 'L0', depends_on: [], registry_contract: frozenProbeContract,
      }),
    }
    const frozenProbeManifest = { ...manifest, assets: [frozenProbeAsset] }
    const liveProbeContract = { ...frozenProbeContract, health_probe: { path: '/health/current', method: 'GET' } }
    const liveRegistryRow = { ...registryRowsFor(frozenProbeManifest)[0], ...liveProbeContract, frozen_manifest_asset: frozenProbeAsset }
    const currentFingerprint = canonicalRegistryContractDigest({
      asset_id: liveRegistryRow.asset_id, layer: 'L0', depends_on: liveRegistryRow.depends_on, registry_contract: liveProbeContract,
    })
    const analysisDigest = canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', liveRegistryRow, frozenProbeAsset)
    useEvidenceTransaction()
    queryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (statement.includes('FROM asset_registry registry')) return Promise.resolve({ rows: [liveRegistryRow] })
      if (statement.includes('SELECT manifest, manifest_sha256')) return Promise.resolve({ rows: [{ manifest: frozenProbeManifest, manifest_sha256: canonicalManifestDigest(frozenProbeManifest), manifest_asset_count: 1 }] })
      if (statement.includes('INSERT INTO nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [{ event_id: '1' }] })
      return Promise.resolve({ rows: [] })
    })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:probe:live-contract',
      event_type: 'probe_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: currentFingerprint, analysis_digest: analysisDigest,
        probe_contract_sha256: canonicalNirmanaProbeContractDigest(liveProbeContract.health_probe), response_digest: 'a'.repeat(64),
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:health-probe:bg_prashna_rules',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).resolves.toBe('created')
  })

  acceptedReceiptIt('admits accepted rebuild evidence only after an exact completed run/asset and matching proven content receipt', async () => {
    useEvidenceTransaction()
    const evidence_payload = mockCurrentRebuildEvidence(true)
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:rebuild:1',
      event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload,
      source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).resolves.toBe('created')
    const rebuildQuery = queryMock.mock.calls.find(([sql]) => String(sql).includes('FROM build_runs run'))
    expect(rebuildQuery?.[0]).toContain("receipt.output_digest_spec_sha256 = $4")
    expect(rebuildQuery?.[0]).toContain("run.triggered_by <> 'nirmana-f0-machinery-canary'")
    expect(queryMock.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(true)
  })

  it('authorizes build runs only for execution-permitting manifest obligations', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ authorized: true }] })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'run:482012f1:authorization',
      event_type: 'build_run_authorized', entity_type: 'build_run', entity_id: '482012f1-710e-4a25-994a-93821f5871aa', layer: 'L0',
      evidence_payload: { wave_index: 0, asset_ids: ['bg_prashna_rules'], authorization_sha256: 'c'.repeat(64) },
      source_kind: 'campaign_authorization', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).resolves.toBe('created')

    expect(queryMock.mock.calls[0][0]).toContain("manifest_asset.value ->> 'execution_obligation' IN ('build', 'probe')")
  })

  acceptedReceiptIt('fails closed when the completed run has no matching proven receipt', async () => {
    useEvidenceTransaction()
    const evidence_payload = mockCurrentRebuildEvidence(false)
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:rebuild:missing',
      event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload,
      source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/matching proven content receipt/i)
    expect(queryMock.mock.calls.some(([sql]) => String(sql).includes('FROM build_runs run'))).toBe(true)
  })

  acceptedReceiptIt.each([
    ['build action', "run.action = 'rebuild'"],
    ['wrong canonical chart', 'run.chart_id = (definition.manifest ->> \'chart_id\')::uuid'],
    ['asset outside the frozen manifest', "manifest_asset.value ->> 'asset_id' = $2"],
    ['non-build manifest asset', "manifest_asset.value ->> 'execution_obligation' = 'build'"],
  ])('rejects accepted rebuild evidence for %s', async (_caseName, requiredGuard) => {
    useEvidenceTransaction()
    const evidence_payload = mockCurrentRebuildEvidence(false)
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: `asset:bg_prashna_rules:rebuild:${_caseName}`,
      event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload,
      source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/matching proven content receipt/i)
    expect(queryMock.mock.calls.find(([sql]) => String(sql).includes('FROM build_runs run'))?.[0]).toContain(requiredGuard)
  })

  it('rejects legacy or malformed rebuild evidence before it can query or append an event', async () => {
    useEvidenceTransaction()
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:rebuild:legacy',
      event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { output_digest: 'a'.repeat(64) }, source_kind: 'build_run', source_ref: 'build_run:not-a-uuid',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/output digest/i)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects a reused evidence idempotency key whose immutable receipt differs', async () => {
    useEvidenceTransaction({
      existing: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
        event_type: 'integrity_verified', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { receipt: 'first' }, source_kind: 'test', source_ref: 'test:receipt',
        observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
      }],
    })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
      event_type: 'integrity_verified', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { receipt: 'second' }, source_kind: 'test', source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/idempotency key/i)
  })

  it('rejects a conflicting lifecycle fact even when its idempotency key is different', async () => {
    const first = {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:test:first',
      event_type: 'test_receipt', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { receipt: 'first' }, source_kind: 'test', source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    }
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement) || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('idempotency_key = $3')) return Promise.resolve({ rows: [] })
      if (statement.includes("event_type = $3 AND entity_type = 'asset'")) return Promise.resolve({ rows: [first] })
      if (statement.includes('AS current')) return Promise.resolve({ rows: [{ current: true }] })
      return Promise.resolve({ rows: [] })
    })

    await expect(recordNirmanaElevationEvidence({
      ...first, idempotency_key: 'asset:bg_prashna_rules:test:second', evidence_payload: { receipt: 'second' },
    })).rejects.toThrow(/conflicting lifecycle receipt/i)
    expect(transactionQueryMock.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(false)
  })

  it('accepts an exact retried evidence receipt without overwriting the original actor', async () => {
    const input = {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
      event_type: 'integrity_verified', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { receipt: 'first' }, source_kind: 'test', source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    }
    transactionQueryMock
      .mockResolvedValueOnce({})
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [input] })
      .mockResolvedValueOnce({})
    await expect(recordNirmanaElevationEvidence(input)).resolves.toBe('idempotent')
    expect(transactionQueryMock).toHaveBeenCalledTimes(4)
    expect(String(transactionQueryMock.mock.calls[3][0])).toBe('COMMIT')
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })

  it('rejects a forged foundation census count before appending an evidence event', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ manifest_sha256: 'a'.repeat(64), manifest_asset_count: 1 }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'f0:A:forged',
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'A', layer: null,
      evidence_payload: {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'A', manifest_sha256: 'a'.repeat(64), asset_count: 2,
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:A',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/asset count/i)
    expect(transactionQueryMock.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(false)
  })

  it.each([
    ['stale', 'a'.repeat(40), 'a'.repeat(40), { main_sha: 'b'.repeat(40), deployed_sha: 'b'.repeat(40), deployed_revision: 'amjis-web-01799-abc', production_in_sync: true }],
    ['divergent', 'a'.repeat(40), 'b'.repeat(40), { main_sha: 'a'.repeat(40), deployed_sha: 'a'.repeat(40), deployed_revision: 'amjis-web-01799-abc', production_in_sync: true }],
  ])('rejects %s release identities before appending F0 release evidence', async (_caseName, main_sha, serving_sha, release) => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ manifest_sha256: 'a'.repeat(64), manifest_asset_count: 1 }] })
    releaseStatusMock.mockResolvedValue({ release })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: `f0:D:${_caseName}`,
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'D', layer: null,
      evidence_payload: {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'D', manifest_sha256: 'a'.repeat(64), main_sha, serving_sha,
        serving_revision: 'amjis-web-01799-abc', ci_run_id: '12345',
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:D',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/release receipt/i)
    expect(ciRunMock).not.toHaveBeenCalled()
  })

  it('rejects missing migration-ledger evidence before appending the evidence-control lane', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ manifest_sha256: 'a'.repeat(64), manifest_asset_count: 1 }] })
      .mockResolvedValueOnce({ rows: [{ applied: false }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'f0:E:missing-ledger',
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'E', layer: null,
      evidence_payload: {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'E',
        manifest_sha256: 'a'.repeat(64),
        migration_filename: '592_nirmana_elevation_campaign_evidence.sql', migration_sha256: '56a86201d15a0d91cf35455758416391e36960e71043cc84fbdb11ff3b72a53e',
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:E',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/migration-ledger/i)
  })

  it('rejects a typed stage receipt when the immediately preceding spine receipt is absent', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ manifest, manifest_sha256: 'a'.repeat(64), manifest_asset_count: 1 }] })
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ present: false }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'stage:T0:no-bootstrap',
      event_type: 'stage_transition_accepted', entity_type: 'campaign_stage', entity_id: 'T0_CENSUS', layer: null,
      evidence_payload: {
        schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: 'BOOTSTRAP', to_stage: 'T0_CENSUS', manifest_sha256: 'a'.repeat(64),
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/immediately preceding/i)
  })

  it('rejects a second logical foundation-lane receipt with a different idempotency key', async () => {
    useEvidenceTransaction()
    queryMock.mockResolvedValueOnce({ rows: [{ present: true }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'f0:A:conflicting-replay',
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'A', layer: null,
      evidence_payload: { schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'A', manifest_sha256: 'a'.repeat(64), asset_count: 1 },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:A',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/Foundation lane already/i)
  })

  it('rejects a lane-C receipt when its current registry fingerprint set diverges', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ manifest, manifest_sha256: canonicalManifestDigest(manifest), manifest_asset_count: 1 }] })
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ live_registry_asset_count: 1 }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'f0:C:stale-contract',
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'C', layer: null,
      evidence_payload: {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'C', manifest_sha256: canonicalManifestDigest(manifest),
        registry_fingerprint_set_sha256: 'f'.repeat(64), manifest_asset_count: 1, live_registry_asset_count: 1, invalidated_analysis_count: 0,
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:C',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/hash\/invalidation census/i)
  })

  it('rejects a noncanonical migration-592 hash even when the ledger reports an applied row', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ manifest_sha256: 'a'.repeat(64), manifest_asset_count: 1 }] })
      .mockResolvedValueOnce({ rows: [{ applied: true }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'f0:E:wrong-canonical-hash',
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'E', layer: null,
      evidence_payload: { schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'E', manifest_sha256: 'a'.repeat(64), migration_filename: '592_nirmana_elevation_campaign_evidence.sql', migration_sha256: 'f'.repeat(64) },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:E',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/migration-ledger/i)
  })

  it('fails closed on an L0 exit rather than trusting asset_frozen rows alone', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ manifest, manifest_sha256: canonicalManifestDigest(manifest), manifest_asset_count: 1 }] })
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ present: true }] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'stage:L1:freeze-presence',
      event_type: 'stage_transition_accepted', entity_type: 'campaign_stage', entity_id: 'L1', layer: null,
      evidence_payload: { schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: 'L0', to_stage: 'L1', manifest_sha256: canonicalManifestDigest(manifest) },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/fail-closed/i)
  })

  it('rejects BOOTSTRAP to T0 when the frozen denominator no longer has a canonical registry identity', async () => {
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ manifest, manifest_sha256: canonicalManifestDigest(manifest), manifest_asset_count: 1 }] })
      .mockResolvedValueOnce({ rows: [{ present: false }] })
      .mockResolvedValueOnce({ rows: [{ present: true }] })
      .mockResolvedValueOnce({ rows: [] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'stage:T0:registry-drift',
      event_type: 'stage_transition_accepted', entity_type: 'campaign_stage', entity_id: 'T0_CENSUS', layer: null,
      evidence_payload: { schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: 'BOOTSTRAP', to_stage: 'T0_CENSUS', manifest_sha256: canonicalManifestDigest(manifest) },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/canonical live registry gate/i)
  })

  it('keeps an exact typed foundation receipt retry idempotent without revalidating or overwriting it', async () => {
    const input = {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'f0:A:exact-retry',
      event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane', entity_id: 'A', layer: null,
      evidence_payload: {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'A', manifest_sha256: 'a'.repeat(64), asset_count: 1,
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:foundation-lane:A',
      observed_at: '2026-08-26T09:00:00.000Z', recorded_by: 'admin-1',
    }
    useEvidenceTransaction({ existing: [input] })
    await expect(recordNirmanaElevationEvidence(input)).resolves.toBe('idempotent')
    expect(queryMock).not.toHaveBeenCalled()
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
  })
})
