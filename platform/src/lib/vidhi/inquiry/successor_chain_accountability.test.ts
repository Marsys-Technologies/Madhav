/**
 * A successor continues its parent (Pūrṇa R2B.4b): the answer must account for everything the
 * whole chain obligated and observed, not only the successor's own evidence.
 */
import { describe, expect, it } from 'vitest'
import generatedCapabilityKnowledge from '../../../generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  closeInquiryForEvidenceSuccessor,
  compileInquiryContract,
  compileInquirySuccessorContract,
  finalizeInquiryContract,
  recordInquiryExecution,
} from './compiler'
import { deriveEvidenceFrontier } from './evidence_frontier'
import {
  buildInquiryFactRegister,
  buildStructuredResponseAccountability,
  inquiryCitationMarker,
  inquiryFindingCitationHandles,
  successorChain,
} from './response_accountability'
import type { InquiryContract } from './types'

const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
const TARGETS = ['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query']
const NONE = { semantics: 'none' as const, exhausted: true, next: null }

function served(contract: InquiryContract, itemId: string, payload: unknown, evidenceFrontier = [] as ReturnType<typeof deriveEvidenceFrontier>) {
  return recordInquiryExecution(contract, {
    item_id: itemId, disposition: 'served', evidence_refs: [`raw:${stableFingerprint(payload)}`],
    pagination: NONE, evidence_frontier: evidenceFrontier,
  })
}

function payloadFor(itemId: string, extra: Record<string, unknown> = {}) {
  return { tool_name: `observed-${itemId}`, results: [{ content: JSON.stringify({ rows: [{ finding: `row for ${itemId}`, ...extra }] }) }] }
}

/** A parent that serves everything, discovers one required cross-capability frontier, and a
 *  successor that serves the admitted capability. */
function chainFixture() {
  const candidates = [
    { question: 'What is my current dasha?', scope: { intent: 'timing', domains: ['general'], width: 'narrow', depth: 'retrieval', horizon: 'current', intervention: 'none', entitlement: 'native' } },
    { question: 'Which planets are in which signs?', scope: { intent: 'chart_overview', domains: ['general'], width: 'narrow', depth: 'retrieval', horizon: 'natal', intervention: 'none', entitlement: 'native' } },
  ]
  for (const candidate of candidates) {
    let parent = compileInquiryContract({
      snapshot, chart_id: '482012f1-710e-4a25-994a-93821f5871aa', question: candidate.question,
      scope_tuple: candidate.scope as never, temporal_anchor_date: '2026-09-27',
    })
    const planned = new Set([...parent.obligations.flatMap((o) => o.scu_ids), ...parent.plan_items.map((i) => i.scu_id)])
    const source = parent.plan_items.find((item) => item.state === 'ready'
      && parent.obligations.some((o) => item.obligation_ids.includes(o.obligation_id) && o.materiality === 'required'))
    if (!source || TARGETS.every((target) => planned.has(target))) continue

    const payloads: unknown[] = []
    const sourcePayload = payloadFor(source.item_id, { bhanga_active: true })
    payloads.push(sourcePayload)
    parent = served(parent, source.item_id, sourcePayload,
      deriveEvidenceFrontier({ contract: parent, item_id: source.item_id, evidence_payload: sourcePayload, snapshot }))
    for (const item of parent.plan_items.filter((candidateItem) => candidateItem.state === 'ready')) {
      const payload = payloadFor(item.item_id)
      payloads.push(payload)
      parent = served(parent, item.item_id, payload)
    }
    const parentFinal = closeInquiryForEvidenceSuccessor(parent)
    let successor = compileInquirySuccessorContract({ snapshot, parent_inquiry_id: 'parent-inquiry', parent: parentFinal })
    for (const item of successor.plan_items.filter((candidateItem) => candidateItem.state === 'ready')) {
      const payload = payloadFor(`successor-${item.item_id}`)
      payloads.push(payload)
      successor = served(successor, item.item_id, payload)
    }
    return { parentFinal, successorFinal: finalizeInquiryContract(successor), payloads }
  }
  throw new Error('no fixture yields a required evidence-admitted frontier')
}

function citingAnswer(contract: InquiryContract, payloads: readonly unknown[]): string {
  const register = buildInquiryFactRegister(contract, payloads, snapshot)
  return [...inquiryFindingCitationHandles(register).values()]
    .map((handle) => `This finding bears on the reading as described ${inquiryCitationMarker(handle)}.`)
    .join('\n\n')
}

describe('successor-chain accountability', () => {
  it('inherits the parent obligations and findings and absorbs the admitted frontier', () => {
    const { parentFinal, successorFinal, payloads } = chainFixture()
    expect(successorChain(successorFinal).map((member) => member.contract_id)).toEqual([successorFinal.contract_id, parentFinal.contract_id])

    const register = buildInquiryFactRegister(successorFinal, payloads, snapshot)
    const obligationFacts = register.facts.filter((fact) => fact.kind === 'obligation')
    expect(obligationFacts).toHaveLength(parentFinal.obligations.length + successorFinal.obligations.length)
    const admittedIds = successorFinal.successor!.admitted_frontier.map((frontier) => frontier.frontier_id)
    const admittedFacts = register.facts.filter((fact) => fact.kind === 'frontier' && admittedIds.includes(fact.frontier_id ?? ''))
    expect(admittedFacts.length).toBe(admittedIds.length)
    for (const fact of admittedFacts) expect(fact.meaning.disposition).toBe('absorbed')
    expect(register.validation_errors).toEqual([])
  })

  it('closes COMPLETE only when the answer covers the whole chain, and names a missing parent payload', () => {
    const { successorFinal, payloads } = chainFixture()
    expect(successorFinal.status).toBe('COMPLETE')
    const answer = citingAnswer(successorFinal, payloads)
    const complete = buildStructuredResponseAccountability(successorFinal, { response_text: answer, evidence_payloads: payloads, knowledge_snapshot: snapshot })
    expect(complete.response_coverage_receipt.status).toBe('COMPLETE')

    // Withhold the first parent payload: the parent obligation it evidenced is no longer delivered.
    const withheld = buildStructuredResponseAccountability(successorFinal, {
      response_text: answer, evidence_payloads: payloads.slice(1), knowledge_snapshot: snapshot,
    })
    expect(withheld.response_coverage_receipt.status).not.toBe('COMPLETE')
    expect(withheld.response_coverage_receipt.missing_required_fact_ids.length).toBeGreaterThan(0)
  })
})
