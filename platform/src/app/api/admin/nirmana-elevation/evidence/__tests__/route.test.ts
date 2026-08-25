// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))
const authMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: () => authMock() }))
const auditMock = vi.fn()
vi.mock('@/lib/admin/audit', () => ({ writeAuditLog: (...args: unknown[]) => auditMock(...args) }))

import { canonicalManifestDigest, canonicalRegistryContractDigest } from '@/lib/nirmana-elevation/definitions'

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
const registryRows = [{ asset_id: manifestAsset.asset_id, layer: 'brahmagyan', depends_on: [], ...registry_contract }]

function request(body: unknown) {
  return new Request('http://localhost/api/admin/nirmana-elevation/evidence', { method: 'POST', body: JSON.stringify(body) })
}

function superAdmin() {
  authMock.mockResolvedValue({ user: { uid: 'admin-1' }, profile: { id: 'admin-1', role: 'super_admin', status: 'active' } })
}

describe('POST /api/admin/nirmana-elevation/evidence', () => {
  beforeEach(() => {
    vi.resetModules()
    queryMock.mockReset()
    authMock.mockReset()
    auditMock.mockReset().mockResolvedValue(undefined)
  })

  it('refuses an unauthenticated write before parsing or recording a receipt', async () => {
    authMock.mockResolvedValue(NextResponse.json({ error: 'forbidden' }, { status: 403 }))
    const { POST } = await import('../route')
    const response = await POST(request({ command: 'record_evidence' }))
    expect(response.status).toBe(403)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('records a typed build receipt with actor attribution', async () => {
    superAdmin()
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:run-1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { run: 'run-1' }, source_kind: 'build_run', source_ref: 'build_run:run-1', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(201)
    expect(queryMock.mock.calls[0][1]).toContain('admin-1')
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_evidence_recorded', null, expect.objectContaining({ outcome: 'created' }))
  })

  it.each([
    'probe_accepted',
    'static_accepted',
    'source_accepted',
    'empty_accepted',
    'retired_with_disposition',
  ])('records the permitted non-build disposition receipt %s', async (event_type) => {
    superAdmin()
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: `bg:test:${event_type}`, event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { disposition: event_type }, source_kind: 'catalogue', source_ref: `catalogue:${event_type}`,
      observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(201)
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

  it('maps a conflicting immutable evidence replay to 409 rather than reporting idempotent success', async () => {
    superAdmin()
    queryMock
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'bg:test:run-1',
        event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { run: 'different-run' }, source_kind: 'build_run', source_ref: 'build_run:run-1',
        observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
      }] })
    const { POST } = await import('../route')
    const response = await POST(request({
      command: 'record_evidence', campaign_id: 'nirmana-elevation', definition_revision: 'v1',
      idempotency_key: 'bg:test:run-1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { run: 'run-1' }, source_kind: 'build_run', source_ref: 'build_run:run-1', observed_at: '2026-08-25T09:00:00.000Z',
    }))
    expect(response.status).toBe(409)
    expect(auditMock).not.toHaveBeenCalled()
  })
})
