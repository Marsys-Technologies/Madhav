// @vitest-environment node
//
// Isolates handleNirmanaEvidenceCommand's own dispatch/publish wiring from the
// already-exhaustively-tested business logic in definitions.ts (see
// definitions.test.ts + the evidence route's own __tests__/route.test.ts for
// the underlying acceptance-rule coverage). recordNirmanaElevationEvidence and
// supersedeNirmanaElevationDefinition are mocked to a controlled outcome here
// so these tests can assert, in isolation, exactly when
// publishCockpitEvent's underlying publishMessage fires -- once per successful
// capsule freeze / definition supersession, and never for any other outcome
// or event type.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const publishMessage = vi.fn().mockResolvedValue(undefined)
const topic = vi.fn(() => ({ publishMessage }))
class MockPubSub {
  topic = topic
}
vi.mock('@google-cloud/pubsub', () => ({ PubSub: MockPubSub }))

const auditMock = vi.fn()
vi.mock('@/lib/admin/audit', () => ({ writeAuditLog: (...args: unknown[]) => auditMock(...args) }))

const rateLimitMock = vi.fn()
vi.mock('@/lib/mcp/rate_limiter', () => ({
  checkRateLimit: (...args: unknown[]) => rateLimitMock(...args),
}))

const recordEvidenceMock = vi.fn()
const supersedeMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/definitions', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/nirmana-elevation/definitions')>()),
  recordNirmanaElevationEvidence: (...args: unknown[]) => recordEvidenceMock(...args),
  supersedeNirmanaElevationDefinition: (...args: unknown[]) => supersedeMock(...args),
}))

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const lifecycleBinding = {
  registry_fingerprint_sha256: 'a'.repeat(64),
  analysis_digest: 'b'.repeat(64),
}

function assetFrozenCommand(overrides: Record<string, unknown> = {}) {
  return {
    command: 'record_evidence' as const,
    campaign_id: 'nirmana-elevation' as const,
    definition_revision: 'v1',
    idempotency_key: 'asset:bg_prashna_rules:freeze:1',
    event_type: 'asset_frozen' as const,
    entity_type: 'asset' as const,
    entity_id: 'bg_prashna_rules',
    layer: 'L0' as const,
    evidence_payload: { ...lifecycleBinding, lifecycle_digest: 'c'.repeat(64) },
    source_kind: 'server_reconstructed',
    source_ref: 'nirmana-elevation:freeze:bg_prashna_rules',
    observed_at: '2026-08-25T09:00:00.000Z',
    ...overrides,
  }
}

function probeAcceptedCommand(overrides: Record<string, unknown> = {}) {
  return {
    command: 'record_evidence' as const,
    campaign_id: 'nirmana-elevation' as const,
    definition_revision: 'v1',
    idempotency_key: 'asset:bg_prashna_rules:probe:1',
    event_type: 'probe_accepted' as const,
    entity_type: 'asset' as const,
    entity_id: 'bg_prashna_rules',
    layer: 'L0' as const,
    evidence_payload: { ...lifecycleBinding, probe_contract_sha256: 'd'.repeat(64), response_digest: 'e'.repeat(64) },
    source_kind: 'server_reconstructed',
    source_ref: 'nirmana-elevation:health-probe:bg_prashna_rules',
    observed_at: '2026-08-25T09:00:00.000Z',
    ...overrides,
  }
}

function supersedeCommand(overrides: Record<string, unknown> = {}) {
  return {
    command: 'supersede_definition' as const,
    campaign_id: 'nirmana-elevation' as const,
    expected_current_revision: 'v1',
    expected_current_manifest_sha256: 'a'.repeat(64),
    source_observation_id: '30303030-3030-4030-8030-303030303030',
    expected_candidate_sha256: 'b'.repeat(64),
    expected_candidate_catalogue_sha256: 'c'.repeat(64),
    new_definition_revision: 'v2',
    ...overrides,
  }
}

describe('handleNirmanaEvidenceCommand cockpit publish wiring', () => {
  beforeEach(() => {
    publishMessage.mockClear()
    topic.mockClear()
    auditMock.mockReset().mockResolvedValue(undefined)
    rateLimitMock.mockReset().mockResolvedValue({ allowed: true })
    recordEvidenceMock.mockReset()
    supersedeMock.mockReset()
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    vi.stubEnv('PUBSUB_DISABLED', '')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('publishes nirmana.asset_frozen exactly once after a newly created asset_frozen receipt', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetFrozenCommand(), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: CANONICAL_CHART_ID, type: 'nirmana.asset_frozen' },
    }))
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({ chart_id: CANONICAL_CHART_ID, type: 'nirmana.asset_frozen', asset_id: 'bg_prashna_rules' })
  })

  it('does not publish for an idempotent asset_frozen replay', async () => {
    recordEvidenceMock.mockResolvedValue('idempotent')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetFrozenCommand(), 'admin-1')
    expect(response.status).toBe(200)
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('does not publish for a created receipt of a different event type', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(probeAcceptedCommand(), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('publishes nirmana.definition_superseded exactly once after a successful supersession', async () => {
    supersedeMock.mockResolvedValue('superseded')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(supersedeCommand(), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: CANONICAL_CHART_ID, type: 'nirmana.definition_superseded' },
    }))
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({ chart_id: CANONICAL_CHART_ID, type: 'nirmana.definition_superseded', definition_revision: 'v2' })
  })

  it('does not publish for an idempotent supersession replay', async () => {
    supersedeMock.mockResolvedValue('idempotent')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(supersedeCommand(), 'admin-1')
    expect(response.status).toBe(200)
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('never lets a publish failure change the HTTP response for a successful freeze', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    publishMessage.mockRejectedValueOnce(new Error('pubsub outage'))
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetFrozenCommand({ idempotency_key: 'asset:bg_prashna_rules:freeze:2' }), 'admin-1')
    expect(response.status).toBe(201)
    expect(await response.json()).toEqual({ outcome: 'created' })
  })
})
