import { beforeEach, describe, expect, it, vi } from 'vitest'

const flagState = { injection: false }
vi.mock('@/lib/config/index', () => ({
  configService: {
    getFlag: (name: string) => name === 'PARIPRASHNA_INJECTION_CONTAINMENT' ? flagState.injection : false,
    getValue: () => undefined,
  },
}))
vi.mock('@/lib/pariprashna/summaries/splice', () => ({ getConversationSummaryForSplice: async () => null }))

import generatedCapabilityKnowledge from '../../../../generated/capability_knowledge.snapshot.json'
import { assembleSynthesisContext } from '../synthesis_stage'
import { INJECTION_CONTAINMENT_CLAUSE } from '../../injection/delimit'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import type { CapabilityKnowledgeSnapshot } from '@/lib/retrieval/registry/knowledge/types'
import { applyInquiryObservations, compileInquiryContract, finalizeInquiryContract } from '@/lib/vidhi/inquiry/compiler'
import { buildInquiryFactRegister, inquiryFindingCitationHandles } from '@/lib/vidhi/inquiry/response_accountability'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { UIMessage } from 'ai'

const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
const MESSAGES = [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'the current question' }] }] as unknown as UIMessage[]
const PLAN = { synthesis_guidance: null } as unknown as PipelinePlan

function admitted() {
  const initial = compileInquiryContract({
    snapshot, chart_id: '482012f1-710e-4a25-994a-93821f5871aa', question: 'Give me a complete wealth outlook',
    scope_tuple: { intent: 'domain_assessment', domains: ['wealth'], width: 'standard', depth: 'standard', horizon: 'natal', intervention: 'none', entitlement: 'native' } as never,
    temporal_anchor_date: '2026-09-27',
  })
  const payloads = initial.plan_items.map((item) => ({
    tool_name: `tool_${item.item_id}`, item_id: item.item_id,
    results: [{ content: `finding:${item.item_id}:primary` }],
  })) as unknown as ToolBundle[]
  const contract = finalizeInquiryContract(applyInquiryObservations(initial, initial.plan_items.map((item, index) => ({
    item_id: item.item_id, disposition: 'served' as const,
    evidence_refs: [`retrieval:${item.item_id}:${stableFingerprint(payloads[index])}`],
  }))))
  return { contract, payloads }
}

async function build(withEvidence: boolean) {
  const evidence = admitted()
  const context = await assembleSynthesisContext({
    messages: MESSAGES, bundle: { assets: [{ content: 'Classical passage.' }] }, plan: PLAN, orientation: null, conversationId: 'c-1',
    ...(withEvidence ? { admittedEvidence: { contract: evidence.contract, payloads: evidence.payloads, snapshot } } : {}),
  })
  return { context, evidence }
}

beforeEach(() => { flagState.injection = false })

describe('Portal synthesis sees the admitted, register-annotated evidence (R2C.1 Portal)', () => {
  it('shows every register finding with its handle and asks for citations', async () => {
    const { context, evidence } = await build(true)
    const handles = [...inquiryFindingCitationHandles(buildInquiryFactRegister(evidence.contract, evidence.payloads, snapshot)).values()].sort()
    expect(handles.length).toBeGreaterThan(0)
    expect(context.visibleCitationHandles).toEqual(handles)
    expect(context.systemContentWithSummary).toContain('ADMITTED INQUIRY EVIDENCE')
    expect(context.systemContentWithSummary).toContain('EVIDENCE CITATIONS')
    for (const handle of handles) expect(context.systemContentWithSummary).toContain(`"_cite": "${handle}"`)
  })

  it('keeps the admitted evidence contained and upstream of the injection clause', async () => {
    flagState.injection = true
    const { context } = await build(true)
    const prompt = context.systemContentWithSummary
    const evidenceAt = prompt.indexOf('ADMITTED INQUIRY EVIDENCE')
    expect(evidenceAt).toBeGreaterThan(-1)
    expect(prompt.lastIndexOf('<untrusted_retrieved_evidence>', evidenceAt)).toBeGreaterThan(-1)
    expect(prompt.indexOf(INJECTION_CONTAINMENT_CLAUSE)).toBeGreaterThan(evidenceAt)
  })

  it('leaves the prompt unchanged and reports no handles without admitted evidence', async () => {
    const { context } = await build(false)
    expect(context.visibleCitationHandles).toBeNull()
    expect(context.registerHandleLabels).toBeNull()
    expect(context.systemContentWithSummary).not.toContain('ADMITTED INQUIRY EVIDENCE')
  })

  it('teaches the model the bracket-cite form the live citation stream actually resolves (R2C.3b)', async () => {
    const { context } = await build(true)
    expect(context.systemContentWithSummary).toContain('\u27E6cite: F7\u27E7')
    expect(context.systemContentWithSummary).not.toMatch(/as \[\[F7\]\]/)
  })

  it('gives every visible handle a real reader label and materiality-graded resolution, keyed for the live citation stream (R2C.3b)', async () => {
    const { context, evidence } = await build(true)
    const register = buildInquiryFactRegister(evidence.contract, evidence.payloads, snapshot)
    const handles = context.visibleCitationHandles!
    expect(context.registerHandleLabels).not.toBeNull()
    expect(context.registerHandleLabels!.size).toBe(handles.length)
    for (const [factId, handle] of inquiryFindingCitationHandles(register)) {
      if (!handles.includes(handle)) continue
      const fact = register.facts.find((f) => f.fact_id === factId)!
      const label = context.registerHandleLabels!.get(handle)!
      expect(label.reader_label).toBe(fact.meaning.label)
      expect(label.rationale).toBe(fact.meaning.rationale)
      expect(label.materiality).toBe(fact.materiality)
    }
  })
})
