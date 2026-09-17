import { randomUUID } from 'node:crypto'
import type { AcceptanceCase, AcceptanceDoor, CollectedCase, CollectionTerminal, DoorClient } from './collection_types'

type Json = Record<string, unknown>

function record(value: unknown): Json { return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Json : {} }
function strings(value: unknown): string[] { return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [] }

/**
 * `prashna_ask` accepts the classifier vocabulary, while the immutable Vidhi
 * corpus carries compiler-family intents such as `wealth_deepdive`. The
 * domain/depth/horizon evidence remains unchanged; only this known namespace
 * boundary is adapted at the managed-engine door.
 */
function managedScopeTuple(scope: Record<string, unknown>): Record<string, unknown> {
  return { ...scope, intent: 'domain_assessment' }
}

function answerFrom(value: unknown): string {
  const data = record(value)
  for (const key of ['answer', 'reading', 'text', 'prose']) if (typeof data[key] === 'string') return data[key] as string
  const result = record(data.result)
  for (const key of ['answer', 'reading', 'text', 'prose']) if (typeof result[key] === 'string') return result[key] as string
  return ''
}

function revisionFrom(value: unknown): string | null {
  const data = record(value)
  for (const key of ['revision', 'source_revision', 'deployed_revision', 'git_sha']) if (typeof data[key] === 'string') return data[key] as string
  const receipt = record(data.receipt)
  return typeof receipt.revision === 'string' ? receipt.revision as string : typeof record(receipt.provenance).revision === 'string' ? record(receipt.provenance).revision as string : null
}

function receiptRefsFrom(value: unknown): string[] {
  const data = record(value)
  const receipt = record(data.receipt)
  const closure = record(data.closure)
  return [...strings(data.receipt_refs), ...strings(data.evidence_refs), ...strings(receipt.refs), ...[receipt.receipt_hash, closure.receipt_hash].filter((item): item is string => typeof item === 'string')]
}

function terminalFrom(value: unknown): CollectionTerminal {
  const data = record(value)
  const status = String(data.status ?? record(data.receipt).status ?? record(data.closure).status ?? record(data.contract ?? record(data.result).inquiry_contract).status ?? '').toLowerCase()
  if (status === 'complete' || status === 'ok') return 'complete'
  if (status.includes('block')) return 'blocked'
  return 'incomplete'
}

export interface McpInvoker { call(name: string, args: Json): Promise<unknown> }

export async function collectManagedCase(input: {
  readonly test: AcceptanceCase
  readonly expectedRevision: string
  readonly source: 'candidate' | 'live'
  readonly chartId: string
  readonly invoker: McpInvoker
  readonly maxPolls: number
  readonly wait: () => Promise<void>
}): Promise<CollectedCase> {
  let calls = 0
  const ask = record(await input.invoker.call('prashna_ask', {
    chart_id: input.chartId, question: input.test.question, scope_tuple: managedScopeTuple(input.test.scope_tuple), response_format: 'full',
  }))
  calls += 1
  if (ask.__purna_tool_error === true) return failed(input, 'managed_mcp', calls, 'MANAGED_MCP_TOOL_ERROR')
  const jobId = typeof ask.job_id === 'string' ? ask.job_id : typeof ask.managed_job_id === 'string' ? ask.managed_job_id : typeof record(ask.result).job_id === 'string' ? record(ask.result).job_id as string : null
  if (!jobId) return failed(input, 'managed_mcp', calls, 'MANAGED_JOB_ID_MISSING')
  for (let attempt = 0; attempt < input.maxPolls; attempt += 1) {
    const status = record(await input.invoker.call('prashna_status', { job_id: jobId }))
    calls += 1
    const state = String(status.status ?? '')
    if (state === 'complete' || state === 'failed') {
      return normalize(input, 'managed_mcp', { ...status, ...record(status.result) }, calls, jobId)
    }
    await input.wait()
  }
  return failed(input, 'managed_mcp', calls, 'MANAGED_JOB_POLL_DEADLINE')
}

export async function collectRawCase(input: {
  readonly test: AcceptanceCase
  readonly expectedRevision: string
  readonly source: 'candidate' | 'live'
  readonly chartId: string
  readonly invoker: McpInvoker
  readonly maxActions: number
}): Promise<CollectedCase> {
  let calls = 0
  let response = record(await input.invoker.call('inquiry_start', {
    chart_id: input.chartId, question: input.test.question, scope_tuple: input.test.scope_tuple,
  }))
  calls += 1
  let inquiryId = typeof response.inquiry_id === 'string' ? response.inquiry_id : null
  let token = typeof response.lifecycle_token === 'string' ? response.lifecycle_token : null
  if (!inquiryId || !token) return failed(input, 'raw_mcp', calls, 'RAW_LIFECYCLE_START_INVALID')
  const seen = new Set<string>()
  for (let step = 0; step < input.maxActions; step += 1) {
    const actionId = strings(response.next_action_ids)[0]
    if (!actionId) break
    const transition = `${token}:${actionId}`
    if (seen.has(transition)) return failed(input, 'raw_mcp', calls, 'RAW_PAGINATION_DID_NOT_ADVANCE', inquiryId)
    seen.add(transition)
    response = record(await input.invoker.call('inquiry_execute_next', { lifecycle_token: token, action_id: actionId }))
    calls += 1
    token = typeof response.lifecycle_token === 'string' ? response.lifecycle_token : null
    if (!token) return normalize(input, 'raw_mcp', response, calls, inquiryId)
  }
  if (!token) return failed(input, 'raw_mcp', calls, 'RAW_LIFECYCLE_TOKEN_MISSING', inquiryId)
  response = record(await input.invoker.call('inquiry_finalize', { lifecycle_token: token }))
  calls += 1
  return normalize(input, 'raw_mcp', response, calls, inquiryId)
}

export async function collectPortalCase(input: {
  readonly test: AcceptanceCase
  readonly expectedRevision: string
  readonly source: 'candidate' | 'live'
  readonly chartId: string
  readonly endpoint: string
  readonly sessionCookie: string
  readonly fetchImpl?: typeof fetch
}): Promise<CollectedCase> {
  const fetcher = input.fetchImpl ?? fetch
  const requestId = randomUUID()
  try {
    const response = await fetcher(`${input.endpoint.replace(/\/$/, '')}/api/pariprashna`, {
      method: 'POST', headers: { 'content-type': 'application/json', cookie: `__session=${input.sessionCookie}` },
      body: JSON.stringify({ chartId: input.chartId, reading_depth: 'auto', length_tier: 'standard', messages: [{ id: `${requestId}-user`, role: 'user', parts: [{ type: 'text', text: input.test.question }] }] }),
    })
    if (!response.ok || !response.body) return failed(input, 'portal', 1, `PORTAL_HTTP_${response.status}`)
    const parsed = await parsePortalSse(response.body)
    if (parsed.truncated) return failed(input, 'portal', 1, 'PORTAL_SSE_TRUNCATED', parsed.inquiryId)
    return normalize(input, 'portal', {
      ...parsed.payload,
      ...(response.headers.get('x-madhav-source-revision')
        ? { deployed_revision: response.headers.get('x-madhav-source-revision') }
        : {}),
    }, 1, parsed.inquiryId, parsed.answer)
  } catch (error) { return failed(input, 'portal', 1, `PORTAL_TRANSPORT:${error instanceof Error ? error.message : 'UNKNOWN'}`) }
}

export async function parsePortalSse(stream: ReadableStream<Uint8Array>): Promise<{ truncated: boolean; inquiryId: string | null; answer: string; payload: Json }> {
  const reader = stream.getReader(); const decoder = new TextDecoder(); let buffer = ''; let answer = ''; let inquiryId: string | null = null; let closed = false; let payload: Json = {}
  while (true) {
    const chunk = await reader.read(); if (chunk.done) break
    buffer += decoder.decode(chunk.value, { stream: true })
    const frames = buffer.split('\n\n'); buffer = frames.pop() ?? ''
    for (const frame of frames) {
      const line = frame.split('\n').find((candidate) => candidate.startsWith('data: ')); if (!line) continue
      let event: Json; try { event = record(JSON.parse(line.slice(6))) } catch { continue }
      // The terminal event is intentionally minimal. Preserve receipt and other
      // evidence emitted earlier rather than replacing the accumulated payload.
      payload = event.receipt && typeof event.receipt === 'object'
        ? { ...payload, ...event, receipt: event.receipt }
        : { ...payload, ...event }
      if (event.type === 'block.commit' && typeof event.text === 'string') answer += `${answer ? '\n\n' : ''}${event.text}`
      if (event.type === 'turn.commit' && typeof event.conversation_id === 'string') inquiryId = event.conversation_id
      if (event.type === 'turn.close') closed = event.status === 'ok'
    }
  }
  return { truncated: !closed, inquiryId, answer, payload }
}

function normalize(input: { test: AcceptanceCase; expectedRevision: string; source: 'candidate' | 'live' }, door: AcceptanceDoor, payload: unknown, calls: number, inquiryId: string | null, answerOverride?: string): CollectedCase {
  const data = record(payload)
  const closure = record(data.closure)
  return { caseId: input.test.id, door, inquiryId, expectedRevision: input.expectedRevision, observedRevision: revisionFrom(data), snapshotHash: typeof data.snapshot_hash === 'string' ? data.snapshot_hash : null, chartBuildId: typeof data.chart_build_id === 'string' ? data.chart_build_id : typeof closure.chart_build_id === 'string' ? closure.chart_build_id as string : null, answer: answerOverride ?? answerFrom(data), receiptRefs: receiptRefsFrom(data), materialFactIds: strings(data.material_fact_ids), deliveredFactIds: strings(data.delivered_fact_ids), unresolvedObligationIds: strings(data.unresolved_obligation_ids), networkCallCount: calls, source: input.source, terminal: terminalFrom(data), diagnostic: null }
}

function failed(input: { test: AcceptanceCase; expectedRevision: string; source: 'candidate' | 'live' }, door: AcceptanceDoor, calls: number, diagnostic: string, inquiryId: string | null = null): CollectedCase {
  return { caseId: input.test.id, door, inquiryId, expectedRevision: input.expectedRevision, observedRevision: null, snapshotHash: null, chartBuildId: null, answer: '', receiptRefs: [], materialFactIds: [], deliveredFactIds: [], unresolvedObligationIds: [], networkCallCount: calls, source: input.source, terminal: 'transport_error', diagnostic }
}

export function clientsForRun(clients: Record<AcceptanceDoor, DoorClient>): readonly DoorClient[] { return Object.values(clients) }
