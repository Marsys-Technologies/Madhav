import { describe, expect, it } from 'vitest'
import generatedCapabilityKnowledge from '../../../src/generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../../src/lib/retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../../src/lib/retrieval/registry/knowledge/stable'
import {
  applyInquiryObservations,
  compileInquiryContract,
  finalizeInquiryContract,
} from '../../../src/lib/vidhi/inquiry/compiler'
import {
  annotateInquiryEvidenceForSynthesis,
  buildStructuredResponseAccountability,
  inquiryCitationMarker,
  visibleInquiryCitationHandles,
} from '../../../src/lib/vidhi/inquiry/response_accountability'
import type { InquiryResponseAccountability } from '../../../src/lib/vidhi/inquiry/types'
import type { AcceptanceCase } from '../collection_types'
import { collectManagedCase, collectPortalCase, collectRawCase } from '../channel_clients'
import { validateResponseAccountability } from '../acceptance_cases'

// RC-6.7: the omitted-fact regression existed only in memory. Here a complete, citation-mapped
// envelope and an omission-tampered copy travel each door's real wire format (Portal SSE grade
// frame, managed NDJSON job result, raw external synthesis) and the independent acceptance
// validator must accept the first and reject the second on every door.
const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
const test: AcceptanceCase = { id: 'wealth_mechanism_timing_contradiction', question: 'Explain wealth with supporting evidence.', scope_tuple: { intent: 'wealth_deepdive', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'near', intervention: 'none', entitlement: 'reference' }, requiredDimensions: ['wealth'], expected: 'supported_complete' }
const base = { test, expectedRevision: 'candidate-a', source: 'candidate' as const, chartId: '11111111-1111-4111-8111-111111111111' }

function completeReading(): { answer: string; envelope: InquiryResponseAccountability } {
  const initial = compileInquiryContract({
    snapshot, chart_id: base.chartId, question: 'Give me a complete wealth outlook',
    scope_tuple: { intent: 'domain_assessment', domains: ['wealth'], width: 'standard', depth: 'standard', horizon: 'natal', intervention: 'none', entitlement: 'native' } as never,
    temporal_anchor_date: '2026-09-27',
  })
  const payloads = initial.plan_items.map((item) => ({
    item_id: item.item_id,
    results: [{ content: `finding:${item.item_id}:primary` }, { content: `finding:${item.item_id}:counter` }],
  }))
  const contract = finalizeInquiryContract(applyInquiryObservations(initial, initial.plan_items.map((item, index) => ({
    item_id: item.item_id, disposition: 'served' as const,
    evidence_refs: [`retrieval:${item.item_id}:${stableFingerprint(payloads[index])}`],
  }))))
  const annotated = annotateInquiryEvidenceForSynthesis(contract, payloads)
  const visible = visibleInquiryCitationHandles(JSON.stringify(annotated.payloads, null, 2))
  const answer = visible.map((handle) => `This finding is interpreted in plain language ${inquiryCitationMarker(handle)}.`).join('\n\n')
  const envelope = buildStructuredResponseAccountability(contract, { response_text: answer, evidence_payloads: payloads, synthesis_visible_handles: visible })
  expect(envelope.response_coverage_receipt.status).toBe('COMPLETE')
  return { answer, envelope }
}

/** Drop one interpretation part while leaving the coverage receipt claiming COMPLETE. */
function omitOneFinding(envelope: InquiryResponseAccountability): InquiryResponseAccountability {
  const index = envelope.delivery_parts.findIndex((part) => part.kind === 'finding_interpretation' || part.kind === 'conjoint_interpretation')
  expect(index).toBeGreaterThanOrEqual(0)
  return { ...envelope, delivery_parts: envelope.delivery_parts.filter((_, partIndex) => partIndex !== index) }
}

async function viaPortal(answer: string, envelope: unknown) {
  const frames = [
    { type: 'turn.open', chart_id: base.chartId },
    { type: 'grade', subject: 'inquiry_contract', grade: 'COMPLETE', detail: 'closure' },
    { type: 'grade', subject: 'response_accountability', grade: 'COMPLETE', detail: JSON.stringify(envelope) },
    { type: 'grade', subject: 'inquiry_door_parity', grade: 'MATCH', detail: '{}' },
    { type: 'block.commit', text: answer },
    { type: 'turn.close', status: 'ok' },
  ]
  const stream = new ReadableStream<Uint8Array>({ start(controller) {
    controller.enqueue(new TextEncoder().encode(frames.map((frame) => `data: ${JSON.stringify(frame)}\n\n`).join('')))
    controller.close()
  } })
  return collectPortalCase({ ...base, endpoint: 'https://example.test', sessionCookie: 'session',
    fetchImpl: async () => new Response(stream, { headers: { 'x-madhav-source-revision': 'candidate-a' } }) })
}

async function viaManaged(answer: string, envelope: unknown) {
  // The managed job result crosses the MCP boundary as JSON.
  const result = JSON.parse(JSON.stringify({ reading: answer, response_accountability: envelope }))
  return collectManagedCase({ ...base, maxPolls: 1, wait: async () => {}, invoker: { call: async (name) =>
    name === 'prashna_ask' ? { job_id: 'job-1' } : { status: 'complete', result } } })
}

async function viaRaw(answer: string, envelope: unknown) {
  return collectRawCase({ ...base, maxActions: 1, invoker: { call: async (name) =>
    name === 'inquiry_start' ? { inquiry_id: 'i-1', lifecycle_token: 't-1', next_action_ids: [] } : { contract: { contract_id: 'c' } } },
  synthesize: async () => JSON.parse(JSON.stringify({ answer, responseAccountability: envelope })) })
}

describe('serialized omission regression on every door (RC-6.7)', () => {
  it.each([['portal', viaPortal], ['managed_mcp', viaManaged], ['raw_mcp', viaRaw]] as const)(
    '%s: accepts the complete envelope and rejects one with an omitted finding', async (_door, via) => {
      const { answer, envelope } = completeReading()

      const complete = await via(answer, envelope)
      expect(complete.answer).toBe(answer)
      expect(validateResponseAccountability(complete.responseAccountability, complete.answer).response_coverage_receipt.status)
        .toBe('COMPLETE')

      const tampered = await via(answer, omitOneFinding(envelope))
      expect(() => validateResponseAccountability(tampered.responseAccountability, tampered.answer))
        .toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
    })
})
