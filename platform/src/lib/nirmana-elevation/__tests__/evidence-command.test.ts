// @vitest-environment node
//
// Isolates handleNirmanaEvidenceCommand's own dispatch/publish wiring from the
// already-exhaustively-tested business logic in definitions.ts (see
// definitions.test.ts + the evidence route's own __tests__/route.test.ts for
// the underlying acceptance-rule coverage). recordNirmanaElevationEvidence and
// supersedeNirmanaElevationDefinition are mocked to a controlled outcome here
// so these tests can assert, in isolation, exactly when
// publishCockpitEvent's underlying publishMessage fires -- once per newly
// created evidence receipt (any event_type) / definition supersession, and
// never for an idempotent replay.
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
const midCampaignSupersedeMock = vi.fn()
vi.mock('@/lib/nirmana-elevation/definitions', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/nirmana-elevation/definitions')>()),
  recordNirmanaElevationEvidence: (...args: unknown[]) => recordEvidenceMock(...args),
  supersedeNirmanaElevationDefinition: (...args: unknown[]) => supersedeMock(...args),
  supersedeNirmanaElevationDefinitionMidCampaign: (...args: unknown[]) => midCampaignSupersedeMock(...args),
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

function assetAnalysisAcceptedCommand(overrides: Record<string, unknown> = {}) {
  return {
    command: 'record_evidence' as const,
    campaign_id: 'nirmana-elevation' as const,
    definition_revision: 'v1',
    idempotency_key: 'asset:bg_prashna_rules:analysis:1',
    event_type: 'asset_analysis_accepted' as const,
    entity_type: 'asset' as const,
    entity_id: 'bg_prashna_rules',
    layer: 'L0' as const,
    evidence_payload: { ...lifecycleBinding },
    source_kind: 'git_commit',
    source_ref: `git:${'f'.repeat(40)}`,
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

  it('publishes nirmana.evidence_accepted exactly once after a newly created asset_frozen receipt', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetFrozenCommand(), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: CANONICAL_CHART_ID, type: 'nirmana.evidence_accepted' },
    }))
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({
      chart_id: CANONICAL_CHART_ID,
      type: 'nirmana.evidence_accepted',
      event_type: 'asset_frozen',
      entity_type: 'asset',
      entity_id: 'bg_prashna_rules',
      asset_id: 'bg_prashna_rules',
      layer: 'L0',
    })
  })

  it('publishes nirmana.evidence_accepted exactly once after a newly created asset_analysis_accepted receipt', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetAnalysisAcceptedCommand(), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: CANONICAL_CHART_ID, type: 'nirmana.evidence_accepted' },
    }))
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({
      chart_id: CANONICAL_CHART_ID,
      type: 'nirmana.evidence_accepted',
      event_type: 'asset_analysis_accepted',
      entity_type: 'asset',
      entity_id: 'bg_prashna_rules',
      asset_id: 'bg_prashna_rules',
      layer: 'L0',
    })
  })

  it('does not publish for an idempotent asset_frozen replay', async () => {
    recordEvidenceMock.mockResolvedValue('idempotent')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetFrozenCommand(), 'admin-1')
    expect(response.status).toBe(200)
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('does not publish for an idempotent asset_analysis_accepted replay', async () => {
    recordEvidenceMock.mockResolvedValue('idempotent')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(assetAnalysisAcceptedCommand(), 'admin-1')
    expect(response.status).toBe(200)
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('publishes for any newly created receipt regardless of event type', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(probeAcceptedCommand(), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({
      chart_id: CANONICAL_CHART_ID,
      type: 'nirmana.evidence_accepted',
      event_type: 'probe_accepted',
      entity_type: 'asset',
      entity_id: 'bg_prashna_rules',
      asset_id: 'bg_prashna_rules',
      layer: 'L0',
    })
  })

  it('publishes a campaign-stage receipt using entity_type/entity_id, never a bogus asset_id', async () => {
    recordEvidenceMock.mockResolvedValue('created')
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const stageCommand = {
      command: 'record_evidence' as const,
      campaign_id: 'nirmana-elevation' as const,
      definition_revision: 'v1',
      idempotency_key: 'stage:F0_FOUNDATION:1',
      event_type: 'stage_transition_accepted' as const,
      entity_type: 'campaign_stage' as const,
      entity_id: 'F0_FOUNDATION' as const,
      layer: null,
      evidence_payload: {
        schema_version: 'nirmana-stage-transition-receipt/v1' as const,
        from_stage: 'DENOMINATOR_FROZEN' as const,
        to_stage: 'F0_FOUNDATION' as const,
        manifest_sha256: 'a'.repeat(64),
      },
      source_kind: 'server_reconstructed' as const,
      source_ref: 'nirmana-elevation:stage-spine' as const,
      observed_at: '2026-08-25T09:00:00.000Z',
    }
    const response = await handleNirmanaEvidenceCommand(stageCommand, 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({
      chart_id: CANONICAL_CHART_ID,
      type: 'nirmana.evidence_accepted',
      event_type: 'stage_transition_accepted',
      entity_type: 'campaign_stage',
      entity_id: 'F0_FOUNDATION',
      layer: null,
    })
    expect(payload).not.toHaveProperty('asset_id')
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

// --- D-NATIVE-13 mid-campaign supersession command wiring -------------------
// The underlying flip semantics (zero in-flight runs, live-registry snapshot,
// identical denominator, t0 immutability, dry-run rollback) are exhaustively
// covered in definitions.test.ts. These tests cover ONLY the command seam:
// schema admission, rate-limit fail-closed, dispatch, audit, cockpit publish,
// and conflict mapping.

function midCampaignSupersedeCommand(overrides: Record<string, unknown> = {}) {
  return {
    command: 'supersede_definition_mid_campaign' as const,
    campaign_id: 'nirmana-elevation' as const,
    expected_current_revision: 't0-2026-09-01-0e5b06fb',
    expected_current_manifest_sha256: 'a'.repeat(64),
    new_definition_revision: 't1-2026-09-08-ffffffff',
    native_authorization: 'D-NATIVE-13' as const,
    mode: 'dry_run' as const,
    ...overrides,
  }
}

function midCampaignReport(overrides: Record<string, unknown> = {}) {
  return {
    outcome: 'dry_run_ok' as const,
    superseded_revision: 't0-2026-09-01-0e5b06fb',
    new_definition_revision: 't1-2026-09-08-ffffffff',
    new_manifest_sha256: 'b'.repeat(64),
    new_catalogue_sha256: 'c'.repeat(64),
    asset_count: 128,
    bound_event_count: 500,
    bound_build_run_count: 91,
    ...overrides,
  }
}

describe('supersede_definition_mid_campaign command seam', () => {
  beforeEach(() => {
    publishMessage.mockClear()
    topic.mockClear()
    auditMock.mockReset().mockResolvedValue(undefined)
    rateLimitMock.mockReset().mockResolvedValue({ allowed: true })
    recordEvidenceMock.mockReset()
    supersedeMock.mockReset()
    midCampaignSupersedeMock.mockReset()
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    vi.stubEnv('PUBSUB_DISABLED', '')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('admits a well-formed command and rejects any weakening of the authorization contract', async () => {
    const { nirmanaEvidenceCommand } = await import('../evidence-command')
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand()).success).toBe(true)
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand({ mode: 'execute' })).success).toBe(true)
    // The literal D-NATIVE-13 reference is REQUIRED — absent, null, or any
    // other string must be refused at the schema boundary, before dispatch.
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand({ native_authorization: undefined })).success).toBe(false)
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand({ native_authorization: 'D-NATIVE-12' })).success).toBe(false)
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand({ mode: 'commit' })).success).toBe(false)
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand({ expected_current_manifest_sha256: 'nope' })).success).toBe(false)
    // .strict(): unknown keys must be refused, not silently dropped.
    expect(nirmanaEvidenceCommand.safeParse(midCampaignSupersedeCommand({ force: true })).success).toBe(false)
  })

  it('dispatches a dry run to the mid-campaign path, returns the full report, and never publishes', async () => {
    midCampaignSupersedeMock.mockResolvedValue(midCampaignReport())
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(midCampaignSupersedeCommand(), 'admin-1')
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ outcome: 'dry_run_ok', report: midCampaignReport() })
    expect(midCampaignSupersedeMock).toHaveBeenCalledTimes(1)
    expect(midCampaignSupersedeMock).toHaveBeenCalledWith(expect.objectContaining({
      campaign_id: 'nirmana-elevation',
      expected_current_revision: 't0-2026-09-01-0e5b06fb',
      native_authorization: 'D-NATIVE-13',
      mode: 'dry_run',
      created_by: 'admin-1',
    }))
    expect(publishMessage).not.toHaveBeenCalled()
    expect(auditMock).toHaveBeenCalledWith('admin-1', 'nirmana_definition_recorded', null, expect.objectContaining({
      command: 'supersede_definition_mid_campaign',
      native_authorization: 'D-NATIVE-13',
      mode: 'dry_run',
      outcome: 'dry_run_ok',
    }))
  })

  it('publishes nirmana.definition_superseded exactly once after an executed flip', async () => {
    midCampaignSupersedeMock.mockResolvedValue(midCampaignReport({ outcome: 'superseded' }))
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(midCampaignSupersedeCommand({ mode: 'execute' }), 'admin-1')
    expect(response.status).toBe(201)
    expect(publishMessage).toHaveBeenCalledTimes(1)
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: CANONICAL_CHART_ID, type: 'nirmana.definition_superseded' },
    }))
    const [[call]] = publishMessage.mock.calls
    const payload = JSON.parse(Buffer.from(call.data).toString('utf-8'))
    expect(payload).toEqual({ chart_id: CANONICAL_CHART_ID, type: 'nirmana.definition_superseded', definition_revision: 't1-2026-09-08-ffffffff' })
  })

  it('does not publish for an idempotent flip retry', async () => {
    midCampaignSupersedeMock.mockResolvedValue(midCampaignReport({ outcome: 'idempotent' }))
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(midCampaignSupersedeCommand({ mode: 'execute' }), 'admin-1')
    expect(response.status).toBe(200)
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('fails closed with 503 when the rate limiter is unavailable, without opening the flip path', async () => {
    rateLimitMock.mockRejectedValue(new Error('limiter down'))
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(midCampaignSupersedeCommand(), 'admin-1')
    expect(response.status).toBe(503)
    expect(midCampaignSupersedeMock).not.toHaveBeenCalled()
  })

  it('returns 429 when rate limited, without opening the flip path', async () => {
    rateLimitMock.mockResolvedValue({ allowed: false, retry_after_seconds: 30 })
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(midCampaignSupersedeCommand(), 'admin-1')
    expect(response.status).toBe(429)
    expect(response.headers.get('Retry-After')).toBe('30')
    expect(midCampaignSupersedeMock).not.toHaveBeenCalled()
  })

  it('maps a definition conflict from the flip path to 409', async () => {
    const { NirmanaElevationDefinitionConflictError } = await import('../definitions')
    midCampaignSupersedeMock.mockRejectedValue(new NirmanaElevationDefinitionConflictError('in-flight build runs present'))
    const { handleNirmanaEvidenceCommand } = await import('../evidence-command')
    const response = await handleNirmanaEvidenceCommand(midCampaignSupersedeCommand({ mode: 'execute' }), 'admin-1')
    expect(response.status).toBe(409)
    expect(await response.json()).toEqual({ error: 'in-flight build runs present' })
    expect(publishMessage).not.toHaveBeenCalled()
  })
})
