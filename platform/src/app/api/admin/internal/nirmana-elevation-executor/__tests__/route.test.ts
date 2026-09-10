// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'

vi.mock('server-only', () => ({}))

const { verifyOidcTokenMock } = vi.hoisted(() => ({ verifyOidcTokenMock: vi.fn() }))
vi.mock('@/lib/auth/oidc', () => ({ verifyOidcToken: verifyOidcTokenMock }))

const handleCommandMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/evidence-command', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/nirmana-elevation/evidence-command')>()),
  handleNirmanaEvidenceCommand: (...args: unknown[]) => handleCommandMock(...args),
}))

const executorOidcToken = 'executor-oidc-token'
const executorOidcAudience = 'https://amjis-web-938361928218.asia-south1.run.app'
const executorPrincipal = 'amjis-nirmana-executor@madhav-astrology.iam.gserviceaccount.com'
const verifierPrincipal = 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com'

const registry_contract = {
  sort_order: 1, scope: 'global' as const, asset_kind: 'data' as const, catalog_status: 'CURRENT' as const,
  is_active: true, has_writer: true, target_table: 'bg_prashna_rules',
  count_sql: 'SELECT count(*) FROM bg_prashna_rules', integrity_check_sql: null, health_probe: null,
  natural_key_partition: null, superseded_by: null, data_disposition: null, dead_flag: null,
}
const manifestAsset = {
  asset_id: 'bg_prashna_rules', layer: 'L0' as const, wave_index: 0, execution_obligation: 'build' as const,
  depends_on: [], registry_contract,
  registry_fingerprint_sha256: 'b'.repeat(64),
}
const manifest = { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', assets: [manifestAsset] }

// An executor-scoped command: no source_kind='server_reconstructed' involved.
const executorCommand = {
  command: 'record_definition',
  campaign_id: 'nirmana-elevation',
  definition_revision: 'rev-1',
  definition_status: 'reconciling',
  manifest,
  manifest_sha256: 'a'.repeat(64),
}

const lifecycleBinding = { registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64) }

// A verifier-scoped command: record_evidence with source_kind='server_reconstructed'
// (asset_frozen), matching exactly what the DB trigger already routes to the
// ingress writer role.
const verifierCommand = {
  command: 'record_evidence',
  campaign_id: 'nirmana-elevation',
  definition_revision: 'rev-1',
  idempotency_key: 'freeze-bg_prashna_rules-1',
  event_type: 'asset_frozen',
  entity_type: 'asset',
  entity_id: 'bg_prashna_rules',
  layer: 'L0',
  evidence_payload: { ...lifecycleBinding, lifecycle_digest: 'c'.repeat(64) },
  source_kind: 'server_reconstructed',
  source_ref: 'nirmana-elevation:freeze:bg_prashna_rules',
  observed_at: new Date().toISOString(),
}

function request(body: unknown, headers: Record<string, string> = {}): Request {
  return new Request('https://madhav.example/api/admin/internal/nirmana-elevation-executor', {
    method: 'POST',
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

function authedRequest(body: unknown): Request {
  return request(body, { Authorization: `Bearer ${executorOidcToken}` })
}

describe('POST /api/admin/internal/nirmana-elevation-executor', () => {
  beforeEach(() => {
    vi.resetModules()
    handleCommandMock.mockReset().mockResolvedValue(
      NextResponse.json({ outcome: 'created' }, { status: 201 }),
    )
    verifyOidcTokenMock.mockReset().mockResolvedValue({ email: executorPrincipal, sub: 'executor-subject' })
  })

  it('rejects an unauthenticated request before parsing the body or dispatching a command', async () => {
    const { POST } = await import('../route')
    const response = await POST(request(executorCommand))
    expect(response.status).toBe(401)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(verifyOidcTokenMock).not.toHaveBeenCalled()
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('rejects an invalid OIDC token before dispatching a command', async () => {
    verifyOidcTokenMock.mockResolvedValueOnce(null)
    const { POST } = await import('../route')
    const response = await POST(authedRequest(executorCommand))
    expect(response.status).toBe(403)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(verifyOidcTokenMock).toHaveBeenCalledWith(executorOidcToken, { expectedAudience: executorOidcAudience })
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('rejects an OIDC verification failure before dispatching a command', async () => {
    verifyOidcTokenMock.mockRejectedValueOnce(new Error('TokenExpiredError'))
    const { POST } = await import('../route')
    const response = await POST(authedRequest(executorCommand))
    expect(response.status).toBe(403)
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('rejects a validly-signed token for a principal outside the fixed two-identity set', async () => {
    verifyOidcTokenMock.mockResolvedValueOnce({ email: 'someone-else@madhav-astrology.iam.gserviceaccount.com', sub: 'other' })
    const { POST } = await import('../route')
    const response = await POST(authedRequest(executorCommand))
    expect(response.status).toBe(403)
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('rejects an unparseable JSON body before dispatching a command', async () => {
    const { POST } = await import('../route')
    const response = await POST(new Request('https://madhav.example/api/admin/internal/nirmana-elevation-executor', {
      method: 'POST',
      headers: { Authorization: `Bearer ${executorOidcToken}` },
      body: '{not json',
    }))
    expect(response.status).toBe(400)
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('rejects a command that fails schema validation before dispatching it', async () => {
    const { POST } = await import('../route')
    const response = await POST(authedRequest({ command: 'not_a_real_command' }))
    expect(response.status).toBe(400)
    const body = await response.json()
    expect(body.error).toBe('invalid Nirmana evidence command')
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('dispatches an executor-scoped command from the executor principal', async () => {
    const { POST } = await import('../route')
    const response = await POST(authedRequest(executorCommand))
    expect(response.status).toBe(201)
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(await response.json()).toEqual({ outcome: 'created' })
    expect(handleCommandMock).toHaveBeenCalledOnce()
    expect(handleCommandMock).toHaveBeenCalledWith(
      expect.objectContaining({ command: 'record_definition', definition_revision: 'rev-1' }),
      `nirmana-executor:${executorPrincipal}`,
    )
  })

  it('rejects an executor-scoped command submitted by the verifier principal', async () => {
    verifyOidcTokenMock.mockResolvedValueOnce({ email: verifierPrincipal, sub: 'verifier-subject' })
    const { POST } = await import('../route')
    const response = await POST(authedRequest(executorCommand))
    expect(response.status).toBe(403)
    const body = await response.json()
    expect(body.error).toBe('principal not authorized for this command')
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('dispatches a verifier-scoped (server_reconstructed) command from the verifier principal', async () => {
    verifyOidcTokenMock.mockResolvedValueOnce({ email: verifierPrincipal, sub: 'verifier-subject' })
    const { POST } = await import('../route')
    const response = await POST(authedRequest(verifierCommand))
    expect(response.status).toBe(201)
    expect(handleCommandMock).toHaveBeenCalledOnce()
    expect(handleCommandMock).toHaveBeenCalledWith(
      expect.objectContaining({ command: 'record_evidence', event_type: 'asset_frozen', source_kind: 'server_reconstructed' }),
      `nirmana-executor:${verifierPrincipal}`,
    )
  })

  it('rejects a verifier-scoped (server_reconstructed) command submitted by the executor principal', async () => {
    const { POST } = await import('../route')
    const response = await POST(authedRequest(verifierCommand))
    expect(response.status).toBe(403)
    const body = await response.json()
    expect(body.error).toBe('principal not authorized for this command')
    expect(handleCommandMock).not.toHaveBeenCalled()
  })

  it('routes every record_evidence event_type whose schema requires source_kind=server_reconstructed to the verifier principal only, by checking submitted source_kind rather than a hardcoded event_type list', async () => {
    // integrity_verified is a different verifier-scoped event_type than
    // asset_frozen; both share source_kind='server_reconstructed', which is
    // what requiredPrincipalFor actually keys off.
    const integrityCommand = {
      ...verifierCommand,
      idempotency_key: 'integrity-bg_prashna_rules-1',
      event_type: 'integrity_verified',
      evidence_payload: { ...lifecycleBinding, integrity_contract_sha256: 'd'.repeat(64), result_digest: 'e'.repeat(64) },
      source_ref: 'nirmana-elevation:integrity:bg_prashna_rules',
    }
    const { POST } = await import('../route')
    const executorAttempt = await POST(authedRequest(integrityCommand))
    expect(executorAttempt.status).toBe(403)
    expect(handleCommandMock).not.toHaveBeenCalled()

    verifyOidcTokenMock.mockResolvedValueOnce({ email: verifierPrincipal, sub: 'verifier-subject' })
    const verifierAttempt = await POST(authedRequest(integrityCommand))
    expect(verifierAttempt.status).toBe(201)
    expect(handleCommandMock).toHaveBeenCalledOnce()
  })
})
