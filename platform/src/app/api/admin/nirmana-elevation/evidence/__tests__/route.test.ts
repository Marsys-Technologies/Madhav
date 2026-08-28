// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

// Keep the route's lifecycle fixtures executable when this checkout lacks the
// generated convergence inventory.  Only the definitions lookup is pinned;
// generated-inventory coverage remains tested independently.
vi.mock('@/generated/nirmana-l0-analysis-receipts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/generated/nirmana-l0-analysis-receipts')>()
  return {
    ...actual,
    getNirmanaL0AnalysisReceiptBase: (assetId: string) => assetId.startsWith('bg_')
      ? {
          schema_version: 'nirmana-asset-analysis-receipt-base/v1' as const,
          asset_id: assetId,
          layer: 'L0' as const,
          writer_digest_sha256: assetId === 'bg_prashna_rules' ? '1'.repeat(64) : null,
          grounding: {
            convergence_commit: actual.NIRMANA_L0_CONVERGENCE_COMMIT,
            frozen_manifest_source: 'nirmana_elevation_campaign_definitions.manifest' as const,
            writer_digest_ref: 'platform/src/generated/nirmana-writer-digests.json' as const,
          },
        }
      : undefined,
  }
})

const queryMock = vi.fn()
const transactionQueryMock = vi.fn()
const transactionReleaseMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
  getPool: () => ({
    connect: async () => ({ query: (...args: unknown[]) => transactionQueryMock(...args), release: transactionReleaseMock }),
  }),
}))
// Campaign definitions and non-server receipts intentionally use their own
// database principal.  Route behavior is still unit-tested against the same
// transaction fixture; credential separation is covered independently.
vi.mock('@/lib/nirmana-elevation/campaign-control-writer', () => ({
  getNirmanaCampaignControlWriterPool: async () => ({
    query: (...args: unknown[]) => queryMock(...args),
    connect: async () => ({ query: (...args: unknown[]) => transactionQueryMock(...args), release: transactionReleaseMock }),
  }),
}))
const authMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: () => authMock() }))
const auditMock = vi.fn()
vi.mock('@/lib/admin/audit', () => ({ writeAuditLog: (...args: unknown[]) => auditMock(...args) }))
const mutationRateLimitMock = vi.fn()
vi.mock('@/lib/mcp/rate_limiter', () => ({
  checkRateLimit: (...args: unknown[]) => mutationRateLimitMock(...args),
}))
const labelCatalogueRecorderMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/labels', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/lib/nirmana-elevation/labels')>(),
  recordNirmanaElevationLabelCatalogue: (...args: unknown[]) => labelCatalogueRecorderMock(...args),
}))

import {
  canonicalManifestDigest,
  canonicalNirmanaAssetAnalysisDigestForRegistryRow,
  canonicalNirmanaOptimizationVerdictDigest,
  canonicalNirmanaRunPlanManifestDigest,
  canonicalRegistryContractDigest,
} from '@/lib/nirmana-elevation/definitions'
import { canonicalLabelCatalogueDigest } from '@/lib/nirmana-elevation/labels'
import { buildNirmanaBaselineCandidate } from '@/lib/nirmana-elevation/monitor'

const registry_contract = {
  sort_order: 1, scope: 'global' as const, asset_kind: 'data' as const, catalog_status: 'CURRENT' as const,
  is_active: true, has_writer: true, target_table: 'bg_prashna_rules',
  count_sql: 'SELECT count(*) FROM bg_prashna_rules', integrity_check_sql: null, health_probe: null,
  natural_key_partition: null, superseded_by: null, data_disposition: null, dead_flag: null,
}
const manifestAsset = {
  asset_id: 'bg_prashna_rules', layer: 'L0' as const, wave_index: 0, execution_obligation: 'build' as const,
  depends_on: [], registry_contract,
  registry_fingerprint_sha256: canonicalRegistryContractDigest({
    asset_id: 'bg_prashna_rules', layer: 'L0', depends_on: [], registry_contract,
  }),
}
const manifest = { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', assets: [manifestAsset] }
const manifest_sha256 = canonicalManifestDigest(manifest)
const baselineObservationId = '30303030-3030-4030-8030-303030303030'
const registryRows = [{
  asset_id: manifestAsset.asset_id, layer: 'brahmagyan' as const, depends_on: [], frozen_manifest_asset: manifestAsset,
  sanskrit_name: 'Prashna Niyama', english_name: 'Prashna rules', english_description: 'Governed horary rules.',
  ...registry_contract,
}]

function request(body: unknown) {
  return new Request('http://localhost/api/admin/nirmana-elevation/evidence', { method: 'POST', body: JSON.stringify(body) })
}

function superAdmin() {
  authMock.mockResolvedValue({ user: { uid: 'admin-1' }, profile: { id: 'admin-1', role: 'super_admin', status: 'active' } })
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

function rebuildPayload({ output_digest = 'a'.repeat(64) }: { output_digest?: string } = {}) {
  const binding = { registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64) }
  const decision = {
    ...binding,
    verdict: 'optimize' as const,
    basis: {
      measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'optimize' as const, summary: 'A governed change is required.', output_contract: 'digest_identical' as const },
  }
  return {
    ...binding,
    build_run_id: '482012f1-710e-4a25-994a-93821f5871aa',
    wave_index: 0,
    authorization_sha256: '9'.repeat(64),
    decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision),
    implementation_digest: 'c'.repeat(64),
    output_digest, output_digest_spec_sha256: 'b'.repeat(64),
  }
}

function mockCurrentRebuildEvidence(proven: boolean) {
  const currentRegistryRow = registryRows[0]
  const binding = {
    registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
    analysis_digest: canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', currentRegistryRow, manifestAsset),
  }
  const decision = {
    ...binding,
    verdict: 'optimize' as const,
    basis: {
      measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'optimize' as const, summary: 'A governed change is required.', output_contract: 'digest_identical' as const },
  }
  const implementation = { ...binding, decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision), implementation_digest: 'c'.repeat(64) }
  const payload = {
    ...implementation,
    build_run_id: '482012f1-710e-4a25-994a-93821f5871aa',
    wave_index: 0,
    authorization_sha256: '9'.repeat(64),
    output_digest: 'a'.repeat(64), output_digest_spec_sha256: 'b'.repeat(64),
  }
  const planManifest = {
    version: 'nirmana-run-manifest/v1', chart_id: manifest.chart_id, scope: 'asset_set', scope_target: 'bg_prashna_rules', action: 'rebuild',
    waves: [['bg_prashna_rules']], assets: [{ asset_id: 'bg_prashna_rules' }],
    campaign_control: { campaign_id: 'nirmana-elevation', definition_revision: 'v1', layer: 'L0', wave_index: 0, snapshot_ref: 'test:snapshot' },
  }
  queryMock.mockImplementation((sql: string) => {
    const statement = String(sql)
    if (statement.includes('FROM asset_registry registry')) return Promise.resolve({ rows: [currentRegistryRow] })
    if (statement.includes('SELECT manifest, manifest_sha256')) return Promise.resolve({ rows: [{ manifest, manifest_sha256, manifest_asset_count: 1 }] })
    if (statement.includes("event_type = 'optimization_verdict_accepted'")) return Promise.resolve({ rows: [{ evidence_payload: decision, source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: '2026-08-25T08:56:00.000Z', recorded_at: '2026-08-25T08:56:00.000Z' }] })
    if (statement.includes("event_type = 'implementation_accepted'")) return Promise.resolve({ rows: [{ evidence_payload: implementation, source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: '2026-08-25T08:57:00.000Z', recorded_at: '2026-08-25T08:57:00.000Z' }] })
    if (statement.includes("event_type = 'build_run_authorized'")) return Promise.resolve({ rows: [{ evidence_payload: { wave_index: 0, asset_ids: ['bg_prashna_rules'], authorization_sha256: '9'.repeat(64) }, source_kind: 'campaign_authorization', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa', observed_at: '2026-08-25T08:55:00.000Z', recorded_at: '2026-08-25T08:55:00.000Z' }] })
    if (statement.includes('FROM build_runs run')) return Promise.resolve({ rows: proven ? [{ plan_manifest: planManifest, plan_manifest_digest: canonicalNirmanaRunPlanManifestDigest(planManifest) }] : [] })
    if (statement.includes('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [{ event_id: '1' }] })
    return Promise.resolve({ rows: [] })
  })
  return payload
}

describe('POST /api/admin/nirmana-elevation/evidence', () => {
  const acceptedReceiptIt = it

  beforeEach(() => {
    vi.resetModules()
    queryMock.mockReset()
    transactionQueryMock.mockReset()
    // Most commands perform their mutation through the control-writer pool.
    // Keep legacy read fixtures reusable unless a test supplies a transaction
    // script explicitly with useEvidenceTransaction().
    transactionQueryMock.mockImplementation((...args: unknown[]) => queryMock(...args))
    transactionReleaseMock.mockReset()
    authMock.mockReset()
    auditMock.mockReset().mockResolvedValue(undefined)
    mutationRateLimitMock.mockReset().mockResolvedValue({
      allowed: true,
    })
    labelCatalogueRecorderMock.mockReset()
  })

  it('refuses an unauthenticated write before parsing or recording a receipt', async () => {
    authMock.mockResolvedValue(NextResponse.json({ error: 'forbidden' }, { status: 403 }))
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'record_evidence' }))
    expect(response.status).toBe(403)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('records a governed label catalogue with a server-derived actor and compact audit metadata', async () => {
    superAdmin()
    labelCatalogueRecorderMock.mockResolvedValue('created')
    const labels = [{
      asset_id: 'ka_smriti', sanskrit_name: 'Kala Smriti', english_name: 'Per-varsha digest',
      description: 'Produces a year-by-year digest of annual chart features.', legacy_aliases: [],
      source_ref: 'PARIKSHA/ASSET_REGISTRY.md#kala-smriti',
    }]
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_label_catalogue', campaign_id: 'nirmana-elevation', definition_revision: 'r1',
      catalogue_revision: 'labels-v1', labels, catalogue_sha256: canonicalLabelCatalogueDigest(labels),
    }))

    expect(response.status).toBe(201)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(labelCatalogueRecorderMock).toHaveBeenCalledWith({
      campaign_id: 'nirmana-elevation', definition_revision: 'r1', catalogue_revision: 'labels-v1', labels,
      catalogue_sha256: canonicalLabelCatalogueDigest(labels), recorded_by: 'admin-1',
    })
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_label_catalogue_recorded', null, {
      campaign_id: 'nirmana-elevation', definition_revision: 'r1', catalogue_revision: 'labels-v1',
      catalogue_sha256: canonicalLabelCatalogueDigest(labels), asset_count: 1, outcome: 'created',
    })
  })

  it('accepts the exact current baseline candidate atomically and audits no lifecycle progress', async () => {
    superAdmin()
    const candidate = buildNirmanaBaselineCandidate(registryRows)
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT definition_revision, definition_status, manifest, manifest_sha256')) {
        return Promise.resolve({ rows: [] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) {
        return Promise.resolve({ rows: [{
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
        }] })
      }
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: registryRows })
      if (statement.includes('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions')) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes("SET definition_status = 'frozen'")) {
        return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'ntap-v1' }] })
      }
      if (statement.includes('SELECT definition_status, manifest')) {
        return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      }
      if (statement.includes('FROM nirmana_evidence.nirmana_elevation_campaign_events')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT count(*)::int AS label_count')) {
        return Promise.resolve({ rows: [{ label_count: 0, digest_matches: false }] })
      }
      if (statement.includes('INSERT INTO nirmana_evidence.nirmana_elevation_asset_labels')) {
        return Promise.resolve({ rowCount: candidate.labels.length, rows: [] })
      }
      if (statement.includes('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events')) {
        return Promise.resolve({ rowCount: 1, rows: [{ event_id: 'receipt-1' }] })
      }
      throw new Error(`Unexpected SQL: ${statement}`)
    })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'accept_baseline_candidate', definition_revision: 'ntap-v1',
      source_observation_id: baselineObservationId,
      expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
    }))

    expect(response.status).toBe(201)
    expect(await response.json()).toEqual({ outcome: 'created' })
    const transactionSql = transactionQueryMock.mock.calls.map(([sql]) => String(sql))
    expect(transactionSql).toEqual(expect.arrayContaining([
      expect.stringContaining('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions'),
      expect.stringContaining("SET definition_status = 'frozen'"),
      expect.stringContaining('INSERT INTO nirmana_evidence.nirmana_elevation_asset_labels'),
    ]))
    expect(transactionSql.join('\n')).not.toContain('stage_transition_accepted')
    expect(transactionSql.join('\n')).not.toContain('asset_frozen')
    const sourceObservationQuery = transactionQueryMock.mock.calls.find(([sql]) =>
      String(sql).includes('FROM nirmana_elevation_monitor_observations'))
    expect(sourceObservationQuery?.[1]).toEqual([baselineObservationId])
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_definition_recorded', null, {
      command: 'accept_baseline_candidate',
      campaign_id: 'nirmana-elevation', definition_revision: 'ntap-v1',
      source_observation_id: baselineObservationId,
      candidate_manifest_sha256: candidate.manifest_sha256,
      candidate_catalogue_sha256: candidate.catalogue_sha256,
      outcome: 'created',
    })
  })

  it('rate-limits baseline acceptance per authenticated actor before opening its transaction', async () => {
    superAdmin()
    mutationRateLimitMock.mockResolvedValue({
      allowed: false, reason: 'rpm_exceeded', retry_after_seconds: 42,
    })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'accept_baseline_candidate', definition_revision: 'ntap-v1',
      source_observation_id: baselineObservationId,
      expected_candidate_sha256: 'a'.repeat(64),
      expected_candidate_catalogue_sha256: 'b'.repeat(64),
    }))

    expect(response.status).toBe(429)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(response.headers.get('Retry-After')).toBe('42')
    expect(await response.json()).toEqual({ error: 'baseline acceptance rate limit exceeded' })
    expect(mutationRateLimitMock).toHaveBeenCalledWith('admin:nirmana_accept_baseline_candidate:admin-1')
    expect(transactionQueryMock).not.toHaveBeenCalled()
    expect(auditMock).not.toHaveBeenCalled()
  })

  it('requires the exact monitor observation identity for baseline acceptance', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'accept_baseline_candidate', definition_revision: 'ntap-v1',
      expected_candidate_sha256: 'a'.repeat(64),
      expected_candidate_catalogue_sha256: 'b'.repeat(64),
    }))

    expect(response.status).toBe(400)
    expect(mutationRateLimitMock).not.toHaveBeenCalled()
    expect(transactionQueryMock).not.toHaveBeenCalled()
  })

  it('does not record a label catalogue for a non-super-admin request', async () => {
    authMock.mockResolvedValue(NextResponse.json({ error: 'forbidden' }, { status: 403 }))
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'record_label_catalogue' }))

    expect(response.status).toBe(403)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(labelCatalogueRecorderMock).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
  })

  acceptedReceiptIt('records a typed build receipt with actor attribution', async () => {
    superAdmin()
    useEvidenceTransaction()
    const evidence_payload = mockCurrentRebuildEvidence(true)
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:run-1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload, source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(201)
    const insertCall = transactionQueryMock.mock.calls.find(([sql]) =>
      String(sql).includes('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events'))
    expect(insertCall?.[1]).toContain('admin-1')
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_evidence_recorded', null, expect.objectContaining({ outcome: 'created' }))
  })

  it.each([
    'probe_accepted',
    'static_accepted',
    'source_accepted',
    'empty_accepted',
    'retired_with_disposition',
  ])('rejects generic unbound lifecycle evidence for %s before a database write', async (event_type) => {
    superAdmin()
    useEvidenceTransaction()
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: `bg:test:${event_type}`, event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { disposition: event_type }, source_kind: 'catalogue', source_ref: `catalogue:${event_type}`,
      observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects an unbound implementation acceptance milestone receipt', async () => {
    superAdmin()
    useEvidenceTransaction()
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:implementation', event_type: 'implementation_accepted', entity_type: 'asset',
      entity_id: 'bg_prashna_rules', layer: 'L0', evidence_payload: { change_ref: 'commit:abc123' },
      source_kind: 'review', source_ref: 'review:implementation', observed_at: '2026-08-25T09:00:00.000Z',
    }))

    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects an invalid campaign-stage transition payload before any database write', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'stage:test:t0', event_type: 'stage_transition_accepted', entity_type: 'campaign_stage',
      entity_id: 'T0_CENSUS', layer: null,
      evidence_payload: { from_stage: 'BOOTSTRAP', to_stage: 'T0_CENSUS', prerequisites_sha256: 'not-a-digest' },
      source_kind: 'campaign_gate', source_ref: 'stage:T0_CENSUS', observed_at: '2026-08-25T09:00:00.000Z',
    }))

    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
    expect(auditMock).not.toHaveBeenCalled()
  })

  it.each([
    {
      name: 'entity ID differs from the destination stage', entity_id: 'PLAN_FROZEN', layer: null,
      payload: { from_stage: 'BOOTSTRAP', to_stage: 'T0_CENSUS', prerequisites_sha256: 'a'.repeat(64) },
    },
    {
      name: 'a null source targets a non-bootstrap stage', entity_id: 'T0_CENSUS', layer: null,
      payload: { from_stage: null, to_stage: 'T0_CENSUS', prerequisites_sha256: 'a'.repeat(64) },
    },
    {
      name: 'the transition skips a canonical stage', entity_id: 'PLAN_FROZEN', layer: null,
      payload: { from_stage: 'BOOTSTRAP', to_stage: 'PLAN_FROZEN', prerequisites_sha256: 'a'.repeat(64) },
    },
    {
      name: 'the campaign-stage receipt carries a layer', entity_id: 'L0', layer: 'L0',
      payload: { from_stage: 'F0_FOUNDATION', to_stage: 'L0', prerequisites_sha256: 'a'.repeat(64) },
    },
  ])('rejects a stage transition when $name', async ({ entity_id, layer, payload }) => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: `stage:invalid:${entity_id}`, event_type: 'stage_transition_accepted',
      entity_type: 'campaign_stage', entity_id, layer, evidence_payload: payload,
      source_kind: 'campaign_gate', source_ref: `stage:${entity_id}`, observed_at: '2026-08-25T09:00:00.000Z',
    }))

    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
    expect(auditMock).not.toHaveBeenCalled()
  })

  it('rejects generic stage and foundation-lane hash claims before any database write', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const stage = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'stage:test:bootstrap', event_type: 'stage_transition_accepted', entity_type: 'campaign_stage',
      entity_id: 'BOOTSTRAP', layer: null,
      evidence_payload: { from_stage: null, to_stage: 'BOOTSTRAP', prerequisites_sha256: 'a'.repeat(64) },
      source_kind: 'campaign_gate', source_ref: 'stage:BOOTSTRAP', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    const lane = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'lane:test:A', event_type: 'foundation_lane_accepted', entity_type: 'foundation_lane',
      entity_id: 'A', layer: null, evidence_payload: { acceptance_sha256: 'b'.repeat(64) },
      source_kind: 'campaign_gate', source_ref: 'foundation:A', observed_at: '2026-08-25T09:00:00.000Z',
    }))

    expect(stage.status).toBe(400)
    expect(lane.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
    expect(auditMock).not.toHaveBeenCalled()
  })

  it('records an audited reconciling definition and freezes only its exact manifest', async () => {
    superAdmin()
    queryMock
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
      .mockResolvedValueOnce({ rows: registryRows })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const create = await POST(request({ command: 'record_definition', campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'reconciling', manifest, manifest_sha256 }))
    const freeze = await POST(request({ command: 'freeze_definition', campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256 }))
    expect(create.status).toBe(201)
    expect(freeze.status).toBe(201)
    expect(queryMock.mock.calls[2][0]).toContain("SET definition_status = 'frozen'")
    expect(auditMock).toHaveBeenLastCalledWith('admin-1', 'nirmana_definition_recorded', null, expect.objectContaining({ definition_status: 'frozen', outcome: 'frozen' }))
  })


it('accepts a typed atomic definition-supersession command without accepting a caller manifest', async () => {
    superAdmin()
    const oldDigest = 'c'.repeat(64)
    const candidate = buildNirmanaBaselineCandidate(registryRows)
    const sourceObservation = {
      id: baselineObservationId, observed_at: '2026-08-26T05:00:01.000Z',
      status: 'plan_adaptation_required', current_definition_sha256: oldDigest,
      candidate_definition_sha256: candidate.manifest_sha256,
      registry_identity_sha256: candidate.registry_identity_sha256,
      registry_contract_sha256: candidate.registry_contract_sha256,
      candidate_catalogue_sha256: candidate.catalogue_sha256,
      source_state: 'available', source_observed_at: '2026-08-26T05:00:00.000Z',
      freshness_state: 'fresh', freshness_deadline_at: '2026-08-26T05:15:00.000Z',
      source_error_code: null, release_state: 'in_sync', runtime_liveness: 'quiet', currently_fresh: true,
    }
    transactionQueryMock.mockImplementation((sql: string) => {
      const statement = String(sql)
      if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(statement)
        || statement.includes('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        || statement.includes('pg_advisory_xact_lock')
        || statement.startsWith('LOCK TABLE')) return Promise.resolve({ rows: [] })
      if (statement.includes('FROM nirmana_evidence.nirmana_elevation_campaign_definitions')
        && statement.includes('ORDER BY definition_revision')) {
        return Promise.resolve({ rows: [{
          definition_revision: 'v1', definition_status: 'frozen', manifest_sha256: oldDigest,
          manifest, created_by: 'admin-0', superseded_at: null,
        }] })
      }
      if (statement.includes('FROM nirmana_elevation_monitor_observations')) return Promise.resolve({ rows: [sourceObservation] })
      if (statement.includes('AS event_count')) return Promise.resolve({ rows: [{ event_count: 0, build_run_count: 0 }] })
      if (statement.includes('FROM asset_registry')) return Promise.resolve({ rows: registryRows })
      if (statement.startsWith('UPDATE nirmana_evidence.nirmana_elevation_campaign_definitions')) return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'v1' }] })
      if (statement.startsWith('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions')) return Promise.resolve({ rowCount: 1, rows: [{ definition_revision: 'v2' }] })
      if (statement.includes('SELECT definition_status, manifest FROM nirmana_evidence')) return Promise.resolve({ rows: [{ definition_status: 'frozen', manifest: candidate.manifest }] })
      if (statement.includes('SELECT event_type, entity_type, entity_id, layer')) return Promise.resolve({ rows: [] })
      if (statement.includes('SELECT count(*)::int AS label_count')) return Promise.resolve({ rows: [{ label_count: 0, digest_matches: false }] })
      if (statement.includes('INSERT INTO nirmana_evidence.nirmana_elevation_asset_labels')) return Promise.resolve({ rowCount: candidate.labels.length, rows: [] })
      if (statement.includes('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events')) return Promise.resolve({ rowCount: 1, rows: [{ event_id: 'receipt-1' }] })
      throw new Error(`Unexpected SQL: ${statement}`)
    })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'supersede_definition', campaign_id: 'nirmana-elevation',
      expected_current_revision: 'v1', expected_current_manifest_sha256: oldDigest,
      source_observation_id: baselineObservationId,
      expected_candidate_sha256: candidate.manifest_sha256,
      expected_candidate_catalogue_sha256: candidate.catalogue_sha256,
      new_definition_revision: 'v2',
    }))
    expect(response.status).toBe(201)
    expect(await response.json()).toEqual({ outcome: 'superseded' })
    expect(mutationRateLimitMock).toHaveBeenCalledWith('admin:nirmana_supersede_definition:admin-1')
    expect(transactionReleaseMock).toHaveBeenCalledOnce()
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_definition_recorded', null, expect.objectContaining({
      command: 'supersede_definition', expected_current_revision: 'v1', new_definition_revision: 'v2',
      candidate_manifest_sha256: candidate.manifest_sha256, outcome: 'superseded',
    }))
  })

 it('rejects a malformed frozen manifest before it can transition state', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'freeze_definition', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      manifest: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', assets: [{ asset_id: 'ga_wrong_layer', layer: 'L0', execution_obligation: 'build' }] }, manifest_sha256,
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects a rebuild receipt without an exact build-run reference', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:run-1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {}, source_kind: 'build_run', source_ref: 'run-1', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects producer coverage without an exact build-run UUID reference', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:coverage', event_type: 'producer_covered', entity_type: 'asset', entity_id: 'bg_sign_medical', layer: 'L0',
      evidence_payload: {}, source_kind: 'build_run', source_ref: 'build_run:not-a-uuid', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('accepts a typed definition-scoped build-run authorization receipt', async () => {
    superAdmin()
    useEvidenceTransaction()
    queryMock
      .mockResolvedValueOnce({ rows: [{ authorized: true }] })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const runId = '33333333-3333-4333-8333-333333333333'
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: `run:${runId}:authorization`, event_type: 'build_run_authorized', entity_type: 'build_run', entity_id: runId, layer: 'L0',
      evidence_payload: { wave_index: 2, asset_ids: ['bg_prashna_rules'], authorization_sha256: 'c'.repeat(64) },
      source_kind: 'campaign_authorization', source_ref: `build_run:${runId}`, observed_at: '2026-08-25T09:00:00.000Z',
    }))

    expect(response.status).toBe(201)
    expect(queryMock.mock.calls[0][0]).toContain("run.triggered_by <> 'nirmana-f0-machinery-canary'")
    expect(queryMock.mock.calls[0][0]).toContain("execution_obligation' IN ('build', 'probe')")
    expect(queryMock.mock.calls[0][0]).toContain('FROM unnest($6::text[]) AS authorized_asset(asset_id)')
    expect(queryMock.mock.calls[0][0]).toContain("manifest_asset.value ->> 'execution_obligation' IN ('build', 'probe')")
    expect(queryMock.mock.calls[1][0]).toContain('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events')
  })

  it('rejects legacy rebuild evidence without both reviewed content hashes', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:legacy', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { output_digest: 'a'.repeat(64) }, source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects asset-analysis evidence that does not pin the current registry contract and analysis artifact', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:analysis', event_type: 'asset_analysis_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {}, source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects an untyped optimization verdict before it can query or append evidence', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:optimization-untyped', event_type: 'optimization_verdict_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { verdict: 'looks-good' }, source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('rejects a typed optimization verdict whose proposal contradicts its verdict', async () => {
    superAdmin()
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:optimization-contradiction', event_type: 'optimization_verdict_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: {
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        analysis_digest: 'a'.repeat(64),
        verdict: 'examined_and_already_efficient',
        basis: {
          measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
          evidence_refs: ['git:test-evidence'],
        },
        proposal: { action: 'correct', summary: 'Contradictory action.', output_contract: 'correctness_change' },
      },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  acceptedReceiptIt('records asset analysis only after the server re-derives the pinned current registry fingerprint', async () => {
    superAdmin()
    useEvidenceTransaction()
    const analysisDigest = canonicalNirmanaAssetAnalysisDigestForRegistryRow('bg_prashna_rules', registryRows[0], manifestAsset)
    queryMock
      .mockResolvedValueOnce({ rows: registryRows })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:analysis', event_type: 'asset_analysis_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256, analysis_digest: analysisDigest },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(201)
    expect(transactionQueryMock.mock.calls[2][0]).toContain('FROM nirmana_evidence.nirmana_elevation_campaign_events')
    expect(queryMock.mock.calls[0][0]).toContain('FROM asset_registry registry')
    expect(transactionQueryMock.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events'))).toBe(true)
  })

  it('rejects a stale asset-analysis fingerprint without appending evidence', async () => {
    superAdmin()
    useEvidenceTransaction()
    queryMock.mockResolvedValueOnce({ rows: registryRows })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:analysis-stale', event_type: 'asset_analysis_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { registry_fingerprint_sha256: 'c'.repeat(64), analysis_digest: 'b'.repeat(64) },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(409)
    expect(await response.json()).toEqual({ error: 'asset_analysis_accepted registry fingerprint does not match the current live contract.' })
    expect(queryMock).toHaveBeenCalledTimes(1)
  })

  it('keeps an exact asset-analysis retry idempotent after the live registry contract evolves', async () => {
    superAdmin()
    const priorReceipt = {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'bg:test:analysis-retry',
      event_type: 'asset_analysis_accepted', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256, analysis_digest: 'b'.repeat(64) },
      source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`,
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    }
    useEvidenceTransaction({ existing: [priorReceipt] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', ...priorReceipt,
    }))

    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ outcome: 'idempotent' })
    expect(queryMock).not.toHaveBeenCalled()
    expect(transactionQueryMock.mock.calls[2][0]).toContain('FROM nirmana_evidence.nirmana_elevation_campaign_events')
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_evidence_recorded', null, expect.objectContaining({ outcome: 'idempotent' }))
  })

  it('maps a conflicting immutable evidence replay to 409 rather than reporting idempotent success', async () => {
    superAdmin()
    useEvidenceTransaction({
      existing: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'bg:test:run-1',
        event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: rebuildPayload({ output_digest: 'c'.repeat(64) }), source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa',
        observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
      }],
    })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:run-1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: rebuildPayload(), source_kind: 'build_run', source_ref: 'build_run:482012f1-710e-4a25-994a-93821f5871aa', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(409)
    expect(auditMock).not.toHaveBeenCalled()
  })
})
