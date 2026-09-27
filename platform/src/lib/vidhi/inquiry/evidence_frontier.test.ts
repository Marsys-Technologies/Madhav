import { describe, expect, it } from 'vitest'
import generatedCapabilityKnowledge from '../../../generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  closeInquiryForEvidenceSuccessor,
  compileInquiryContract,
  compileInquirySuccessorContract,
  recordInquiryExecution,
} from './compiler'
import { deriveEvidenceFrontier, EVIDENCE_FRONTIER_RULES } from './evidence_frontier'
import type { InquiryContract } from './types'

const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot

function contractWithout(targets: readonly string[]): { contract: InquiryContract; target: string } {
  const candidates = [
    { question: 'What is my current dasha?', scope: { intent: 'timing', domains: ['general'], width: 'narrow', depth: 'retrieval', horizon: 'current', intervention: 'none', entitlement: 'native' } },
    { question: 'Which planets are in which signs?', scope: { intent: 'chart_overview', domains: ['general'], width: 'narrow', depth: 'retrieval', horizon: 'natal', intervention: 'none', entitlement: 'native' } },
  ]
  for (const candidate of candidates) {
    const contract = compileInquiryContract({
      snapshot, chart_id: '482012f1-710e-4a25-994a-93821f5871aa', question: candidate.question,
      scope_tuple: candidate.scope as never, temporal_anchor_date: '2026-09-27',
    })
    const planned = new Set([...contract.obligations.flatMap((o) => o.scu_ids), ...contract.plan_items.map((i) => i.scu_id)])
    const target = targets.find((scuId) => !planned.has(scuId))
    if (target && contract.plan_items.some((item) => item.state === 'ready' && item.scu_id !== target)) return { contract, target }
  }
  throw new Error('no fixture contract leaves a rule target unplanned')
}

describe('evidence-driven cross-capability frontier (RC-5.4)', () => {
  it('declares only rules whose targets exist in the pinned snapshot', () => {
    const known = new Set(snapshot.scus.map((scu) => scu.scu_id))
    for (const rule of EVIDENCE_FRONTIER_RULES) for (const target of rule.target_scu_ids) expect(known.has(target)).toBe(true)
  })

  it('admits a successor item for a different SCU because of what an observation served', () => {
    const { contract, target } = contractWithout(['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query'])
    const source = contract.plan_items.find((item) => item.state === 'ready' && item.scu_id !== target)!
    const payload = { tool_name: 'observed', results: [{ content: JSON.stringify({ rows: [{ yoga: 'Raja', fired: true, bhanga_active: true }] }) }] }
    const evidenceFrontier = deriveEvidenceFrontier({ contract, item_id: source.item_id, evidence_payload: payload, snapshot })
    expect(evidenceFrontier.map((entry) => entry.scu_id)).toContain(target)

    let observed = recordInquiryExecution(contract, {
      item_id: source.item_id, disposition: 'served',
      evidence_refs: [`raw:${stableFingerprint(payload)}`],
      pagination: { semantics: 'none', exhausted: true, next: null },
      evidence_frontier: evidenceFrontier,
    })
    const discovered = observed.material_frontier.find((frontier) => frontier.scu_id === target)
    expect(discovered).toMatchObject({ discovered_from: source.item_id, disposition: 'open' })
    // Serve every other item so the parent can close; the discovered frontier keeps it open.
    for (const item of observed.plan_items.filter((candidate) => candidate.state === 'ready')) {
      observed = recordInquiryExecution(observed, {
        item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${item.item_id}`],
        pagination: { semantics: 'none', exhausted: true, next: null },
      })
    }
    if (discovered?.materiality === 'required') {
      const parent = closeInquiryForEvidenceSuccessor(observed)
      const successor = compileInquirySuccessorContract({ snapshot, parent_inquiry_id: 'parent-1', parent })
      expect(successor.obligations.flatMap((obligation) => obligation.scu_ids)).toContain(target)
      expect(successor.successor?.admitted_frontier.map((frontier) => frontier.discovered_from)).toContain(source.item_id)
    }
  })

  it('never proposes the observed SCU, an already-planned SCU, or a failed observation', () => {
    const { contract } = contractWithout(['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query'])
    const source = contract.plan_items[0]!
    const plannedTargets = contract.plan_items.map((item) => item.scu_id)
    const frontier = deriveEvidenceFrontier({ contract, item_id: source.item_id, evidence_payload: { bhanga_active: true, dignity_state: 'debilitated' }, snapshot })
    for (const entry of frontier) {
      expect(entry.scu_id).not.toBe(source.scu_id)
      expect(plannedTargets).not.toContain(entry.scu_id)
    }
    const failed = recordInquiryExecution(contract, {
      item_id: source.item_id, disposition: 'failed', evidence_refs: [], gap_reason: 'x',
      pagination: { semantics: 'none', exhausted: true, next: null }, evidence_frontier: frontier,
    })
    expect(failed.material_frontier.filter((item) => item.discovered_from === source.item_id)).toEqual([])
  })

  it('ignores prose that merely mentions a cancellation', () => {
    const { contract } = contractWithout(['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query'])
    const source = contract.plan_items[0]!
    expect(deriveEvidenceFrontier({ contract, item_id: source.item_id, evidence_payload: { results: [{ content: 'the bhanga_active yoga is debilitated' }] }, snapshot })).toEqual([])
  })
})
