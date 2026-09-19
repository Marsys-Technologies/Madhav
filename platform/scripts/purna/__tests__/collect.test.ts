import { describe, expect, it, vi } from 'vitest'
import { assertLiveEvidence, createCollectionArtifact, validateCollectionArtifact, type AcceptanceCase, type CollectedCase } from '../collection_types'
import type { AcceptanceCaseInput } from '../acceptance_cases'
import { collectManagedCase, collectPortalCase, collectRawCase, parsePortalSse } from '../channel_clients'

const test: AcceptanceCase = { id: 'wealth_mechanism_timing_contradiction', question: 'Explain wealth with supporting evidence.', scope_tuple: { intent: 'wealth_deepdive', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'near', intervention: 'none', entitlement: 'reference' }, requiredDimensions: ['wealth'], expected: 'supported_complete' }
const base = { test, expectedRevision: 'candidate-a', source: 'candidate' as const, chartId: '11111111-1111-4111-8111-111111111111' }

describe('Purna real three-door collector', () => {
  it('seals the exact suite case inputs and three door rows into a tamper-evident collection', () => {
    const input: AcceptanceCaseInput = {
      case_id: test.id, kind: 'beyond_acarya', question: test.question, scope_tuple: test.scope_tuple,
      deterministic_gates: ['immutable_case_input', 'source_acceptance_denominator'],
      required_dimensions: test.requiredDimensions, expected: test.expected,
    }
    const baseRow: CollectedCase = {
      caseId: test.id, door: 'portal', inquiryId: 'i-1', expectedRevision: 'candidate-a', observedRevision: 'candidate-a',
      snapshotHash: 'snapshot-a', chartBuildId: 'build-a', answer: 'answer', responseAccountability: null,
      receiptRefs: ['receipt-a'], materialFactIds: ['f1'], deliveredFactIds: ['f1'], unresolvedObligationIds: [],
      networkCallCount: 1, source: 'candidate', terminal: 'complete', diagnostic: null,
    }
    const artifact = createCollectionArtifact({
      suite: 'beyond_acarya', environment: 'candidate', expectedRevision: 'candidate-a',
      authorizationApprovalId: 'approval-1', caseInputs: [input],
      rows: (['portal', 'managed_mcp', 'raw_mcp'] as const).map((door) => ({ ...baseRow, door })),
    })
    expect(validateCollectionArtifact(artifact)).toEqual(artifact)
    expect(artifact.manifest_hash).toMatch(/^sha256:/)
    expect(artifact.collection_hash).toMatch(/^sha256:/)
    expect(() => validateCollectionArtifact({ ...artifact, rows: artifact.rows.map((row, index) => index ? row : { ...row, answer: 'forged' }) }))
      .toThrow('PURNA_COLLECTION_ARTIFACT_INVALID')
  })

  it('rejects a supposedly live answer with no real channel execution', () => {
    expect(() => assertLiveEvidence({ caseId: test.id, door: 'portal', inquiryId: 'test', expectedRevision: 'candidate-a', observedRevision: 'candidate-a', snapshotHash: 'snapshot-a', chartBuildId: 'build-a', answer: 'answer', responseAccountability: null, receiptRefs: ['receipt-a'], materialFactIds: ['f1'], deliveredFactIds: ['f1'], unresolvedObligationIds: [], networkCallCount: 0, source: 'live', terminal: 'complete', diagnostic: null })).toThrow('PURNA_COLLECTION_NOT_LIVE_EVIDENCE')
  })
  it('keeps a truncated SSE stream incomplete', async () => {
    const stream = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new TextEncoder().encode('data: {"type":"block.commit","text":"partial"}\n\n')); controller.close() } })
    await expect(parsePortalSse(stream)).resolves.toMatchObject({ truncated: true, answer: 'partial' })
  })
  it('retains receipt evidence when a later terminal event closes the SSE stream', async () => {
    const stream = new ReadableStream<Uint8Array>({ start(controller) {
      controller.enqueue(new TextEncoder().encode('data: {"type":"receipt.define","receipt":{"receipt_hash":"r-1"}}\n\ndata: {"type":"turn.close","status":"ok"}\n\n'))
      controller.close()
    } })
    await expect(parsePortalSse(stream)).resolves.toMatchObject({ truncated: false, payload: { receipt: { receipt_hash: 'r-1' } } })
  })
  it('records the Portal response revision as acceptance evidence', async () => {
    const stream = new ReadableStream<Uint8Array>({ start(controller) {
      controller.enqueue(new TextEncoder().encode('data: {"type":"turn.close","status":"ok"}\n\n'))
      controller.close()
    } })
    const row = await collectPortalCase({ ...base, endpoint: 'https://example.test', sessionCookie: 'session', fetchImpl: async () => new Response(stream, { headers: { 'x-madhav-source-revision': 'candidate-a' } }) })
    expect(row.observedRevision).toBe('candidate-a')
  })
  it('turns a stalled Portal connection into an explicit incomplete receipt', async () => {
    const fetchImpl: typeof fetch = async (_input, init) => await new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    })
    const row = await collectPortalCase({ ...base, endpoint: 'https://example.test', sessionCookie: 'session', timeoutMs: 1, fetchImpl })
    expect(row).toMatchObject({ terminal: 'transport_error', diagnostic: 'PORTAL_DEADLINE_EXCEEDED', networkCallCount: 1 })
  })
  it('enforces a managed polling deadline', async () => {
    const row = await collectManagedCase({ ...base, maxPolls: 2, wait: async () => {}, invoker: { call: async (name) => name === 'prashna_ask' ? { job_id: 'job-1' } : { status: 'running' } } })
    expect(row.diagnostic).toBe('MANAGED_JOB_POLL_DEADLINE')
    expect(row.networkCallCount).toBe(3)
  })
  it('projects the immutable corpus scope into the managed engine vocabulary', async () => {
    let askArgs: Record<string, unknown> | undefined
    const row = await collectManagedCase({ ...base, test: { ...test, scope_tuple: { intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive', horizon: 'multi_year', intervention: false, entitlement: 'native' } }, maxPolls: 1, wait: async () => {}, invoker: { call: async (name, args) => {
      if (name === 'prashna_ask') { askArgs = args; return { job_id: 'job-1' } }
      return { status: 'failed' }
    } } })
    expect(askArgs?.scope_tuple).toEqual({ intent: 'domain_assessment', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'far', intervention: 'none', entitlement: 'native' })
    expect(row.networkCallCount).toBe(2)
  })
  it('keeps an in-band managed tool error distinct from a missing job handle', async () => {
    const row = await collectManagedCase({ ...base, maxPolls: 1, wait: async () => {}, invoker: { call: async () => ({ __purna_tool_error: true }) } })
    expect(row.diagnostic).toBe('MANAGED_MCP_TOOL_ERROR')
  })
  it('records a managed MCP deadline without falling through to a missing job handle', async () => {
    const row = await collectManagedCase({ ...base, maxPolls: 1, wait: async () => {}, invoker: { call: async () => ({ __purna_timeout: true }) } })
    expect(row).toMatchObject({ terminal: 'transport_error', diagnostic: 'MANAGED_MCP_REQUEST_DEADLINE', networkCallCount: 1 })
  })
  it('retains the managed status response revision with its terminal result', async () => {
    const row = await collectManagedCase({ ...base, maxPolls: 1, wait: async () => {}, invoker: { call: async (name) => name === 'prashna_ask'
      ? { job_id: 'job-1' }
      : { status: 'complete', deployed_revision: 'candidate-a', result: { reading: 'complete response', receipt_refs: ['r-1'] } } } })
    expect(row).toMatchObject({ observedRevision: 'candidate-a', terminal: 'complete', receiptRefs: ['r-1'] })
  })
  it('retains the managed response-accountability envelope for independent assessment', async () => {
    const envelope = { accountability_version: 'inquiry-response-accountability-v1' }
    const row = await collectManagedCase({ ...base, maxPolls: 1, wait: async () => {}, invoker: { call: async (name) => name === 'prashna_ask'
      ? { job_id: 'job-1' }
      : { status: 'complete', deployed_revision: 'candidate-a', result: { reading: 'complete response', response_accountability: envelope } } } })
    expect(row.responseAccountability).toBe(envelope)
  })
  it('rejects raw lifecycle pagination that does not advance', async () => {
    const row = await collectRawCase({ ...base, maxActions: 3, invoker: { call: async (name) => name === 'inquiry_start' ? { inquiry_id: 'i-1', lifecycle_token: 'same', next_action_ids: ['item-001'] } : { lifecycle_token: 'same', next_action_ids: ['item-001'] } } })
    expect(row.diagnostic).toBe('RAW_PAGINATION_DID_NOT_ADVANCE')
  })
  it('records a raw MCP deadline at lifecycle start', async () => {
    const row = await collectRawCase({ ...base, maxActions: 1, invoker: { call: async () => ({ __purna_timeout: true }) } })
    expect(row).toMatchObject({ terminal: 'transport_error', diagnostic: 'RAW_MCP_REQUEST_DEADLINE', networkCallCount: 1 })
  })
  it('records a raw lifecycle closure as the terminal contract source', async () => {
    const row = await collectRawCase({ ...base, maxActions: 1, invoker: { call: async (name) => name === 'inquiry_start'
      ? { inquiry_id: 'i-1', lifecycle_token: 'token-1', next_action_ids: [] }
      : { closure: { status: 'INCOMPLETE', receipt_hash: 'r-1', chart_build_id: 'build-1' } } } })
    expect(row).toMatchObject({ terminal: 'incomplete', chartBuildId: 'build-1', receiptRefs: ['r-1'] })
  })
  it('collects a raw answer only from an explicit external synthesis bound to the terminal contract and raw payload', async () => {
    const terminalContract = { contract_id: 'contract-1', status: 'COMPLETE' }
    const envelope = { accountability_version: 'inquiry-response-accountability-v1' }
    const synthesize = vi.fn(async (input: { inquiryId: string; contract: unknown; evidencePayloads: readonly unknown[] }) => {
      expect(input).toMatchObject({ inquiryId: 'i-1', contract: terminalContract, evidencePayloads: [{ results: [{ fact: 'one' }] }] })
      return { answer: 'Grounded external answer.', responseAccountability: envelope as never }
    })
    const row = await collectRawCase({ ...base, maxActions: 1, synthesize, invoker: { call: async (name) => name === 'inquiry_start'
      ? { inquiry_id: 'i-1', lifecycle_token: 'token-1', next_action_ids: ['item-001'] }
      : name === 'inquiry_execute_next'
        ? { lifecycle_token: 'token-2', next_action_ids: [], raw_result: { results: [{ fact: 'one' }] } }
        : { deployed_revision: 'candidate-a', contract: terminalContract, closure: { status: 'COMPLETE', receipt_hash: 'r-1' } } } })
    expect(row).toMatchObject({ answer: 'Grounded external answer.', responseAccountability: envelope, terminal: 'complete', networkCallCount: 4 })
  })
  it('accepts a revision-bound honest insufficiency as live transport evidence for later protocol assessment', () => {
    expect(() => assertLiveEvidence({ caseId: test.id, door: 'raw_mcp', inquiryId: 'test', expectedRevision: 'candidate-a', observedRevision: 'candidate-a', snapshotHash: null, chartBuildId: null, answer: 'Evidence is insufficient.', responseAccountability: {}, receiptRefs: ['r-1'], materialFactIds: [], deliveredFactIds: [], unresolvedObligationIds: ['obl-1'], networkCallCount: 3, source: 'live', terminal: 'blocked', diagnostic: null })).not.toThrow()
  })
})
