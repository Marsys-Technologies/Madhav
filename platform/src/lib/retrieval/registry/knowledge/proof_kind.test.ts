/**
 * Availability proof typing (Pūrṇa R3 / review RC-7, §4).
 *
 * Planning resources, dossiers, wiring projections and catalog discovery return no chart
 * evidence. Their correct proof is registration in the pinned snapshot, reported as
 * `resource_ok` and excluded from answer readiness — not dark for want of an evidence receipt
 * they can never have, and never admissible as answer evidence.
 */
import { describe, expect, it } from 'vitest'
import { getCatalog } from '../catalog'
import { compileCapabilityKnowledge, inspectCapabilityKnowledge } from './compiler'
import { loadChartCapabilityOverlay } from './overlay_loader'
import { compileInquiryContract } from '../../../vidhi/inquiry/compiler'
import type { CapabilityKnowledgeSnapshot, SemanticCapabilityUnit } from './types'

const catalog = getCatalog()
const snapshot = compileCapabilityKnowledge(catalog, '2026-09-27T00:00:00.000Z') as CapabilityKnowledgeSnapshot
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const NON_ANSWER = {
  'scu.catalog.intent_classify': ['plan', 'registered_in_pinned_snapshot'],
  'scu.catalog.route': ['plan', 'registered_in_pinned_snapshot'],
  'scu.catalog.maro_orchestrate': ['plan', 'registered_in_pinned_snapshot'],
  'scu.catalog.maro_mcp_surface': ['plan', 'registered_in_pinned_snapshot'],
  'scu.catalog.maro_profiles': ['resource', 'registered_in_pinned_snapshot'],
  'scu.catalog.channel_mcp_wiring': ['resource', 'registered_in_pinned_snapshot'],
  'scu.catalog.tool_search': ['discovery', 'index_compiled_from_pinned_catalog'],
} as const

function scu(scuId: string): SemanticCapabilityUnit {
  const found = snapshot.scus.find((candidate) => candidate.scu_id === scuId)
  if (!found) throw new Error(`missing ${scuId}`)
  return found
}

function replaceScu(next: SemanticCapabilityUnit): CapabilityKnowledgeSnapshot {
  return { ...snapshot, scus: snapshot.scus.map((candidate) => candidate.scu_id === next.scu_id ? next : candidate) }
}

async function overlayWithNoEvidence(target: CapabilityKnowledgeSnapshot = snapshot) {
  // No receipts, no probes, no source-query success: nothing chart-scoped can be proven.
  return loadChartCapabilityOverlay(target, CHART_ID, async () => ({ rows: [] }), new Date('2026-09-27T00:05:00.000Z'))
}

describe('availability proof typing', () => {
  it.each(Object.entries(NON_ANSWER))('types %s by its proof kind with the snapshot proof as its sole contract', (scuId, [kind, proof]) => {
    const unit = scu(scuId)
    expect(unit.proof_kind).toBe(kind)
    expect(unit.availability_dispositions ?? []).toEqual([])
    expect(unit.availability_contracts).toEqual([{
      binding_id: `registry:${unit.primary_binding_uri}`,
      requirements: [expect.objectContaining({ kind: 'snapshot_resource', proof, scope: 'global' })],
    }])
  })

  it('leaves every answer capability untyped (answer by default)', () => {
    const typed = snapshot.scus.filter((unit) => unit.proof_kind !== undefined).map((unit) => unit.scu_id).sort()
    expect(typed).toEqual(Object.keys(NON_ANSWER).sort())
  })

  it('reports non-answer capabilities resource_ok, with no admissible bindings, even when no chart evidence exists', async () => {
    const overlay = await overlayWithNoEvidence()
    for (const scuId of Object.keys(NON_ANSWER)) {
      expect(overlay.availability.find((entry) => entry.scu_id === scuId)).toMatchObject({
        state: 'resource_ok', available_binding_ids: [], gaps: [],
      })
    }
    // An answer capability with the same absence of evidence stays dark.
    expect(overlay.availability.find((entry) => entry.scu_id === 'scu.catalog.query_contradictions')?.state).toBe('dark')
  })

  it('never admits a resource_ok capability into an inquiry plan', async () => {
    const overlay = await overlayWithNoEvidence()
    const contract = compileInquiryContract({
      snapshot, overlay, chart_id: CHART_ID, question: 'Which route and tools should answer my career question?',
      scope_tuple: { intent: 'domain_assessment', domains: ['career'], width: 'broad', depth: 'standard', horizon: 'natal', intervention: 'none', entitlement: 'native' },
      execution_channel: 'mcp_full', presentation_transport: 'raw_mcp',
      ai_proposal: {
        question_facets: [{ label: 'routing', terms: ['route_selection', 'capability_discovery', 'intent_classify', 'tool_search', 'route'], materiality: 'required' }],
        uncommon_adjacencies: [{ from_scu_id: 'scu.catalog.query_contradictions', to_scu_id: 'scu.catalog.route', rationale: 'route the question' }],
        hypotheses: [],
      },
    })
    // The proposal reaches the resource capabilities (non-vacuous), and each is blocked with a
    // typed reason rather than admitted or reported as missing evidence.
    for (const scuId of ['scu.catalog.intent_classify', 'scu.catalog.tool_search', 'scu.catalog.route']) {
      const item = contract.plan_items.find((candidate) => candidate.scu_id === scuId)
      expect(item, scuId).toMatchObject({
        state: 'blocked',
        blocked_reason: expect.stringContaining('never admitted as answer evidence'),
      })
    }
    const admitted = contract.plan_items.filter((item) => item.state === 'ready').map((item) => item.scu_id)
    for (const scuId of Object.keys(NON_ANSWER)) expect(admitted).not.toContain(scuId)
  })

  it('keeps the legacy chat-dispatch descriptor dark with a typed reason naming the real Portal door', () => {
    expect(scu('scu.catalog.channel_chat_dispatch').availability_dispositions).toEqual([expect.objectContaining({
      status: 'deliberately_dark',
      reason: expect.stringContaining('/api/pariprashna'),
    })])
  })

  describe('integrity', () => {
    const resourceScu = scu('scu.catalog.route')
    const answerScu = snapshot.scus.find((unit) => unit.scope === 'global' && !unit.proof_kind
      && unit.bindings.some((binding) => binding.executable)
      && (unit.availability_contracts?.length ?? 0) > 0)!
    const answerBinding = answerScu.availability_contracts![0]!.binding_id

    it('rejects a snapshot proof on an answer capability', () => {
      const report = inspectCapabilityKnowledge(catalog, replaceScu({
        ...answerScu,
        availability_contracts: [{ binding_id: answerBinding, requirements: [{
          kind: 'snapshot_resource', proof: 'registered_in_pinned_snapshot', scope: 'global', source_ref: 'fixture',
        }] }],
      }))
      expect(report.findings).toContainEqual(expect.objectContaining({
        code: 'BAD_BINDING_AVAILABILITY_CONTRACT', subject: `${answerScu.scu_id}:${answerBinding}`,
      }))
    })

    it('rejects chart evidence as the proof of a non-answer capability', () => {
      const bindingId = resourceScu.availability_contracts![0]!.binding_id
      const report = inspectCapabilityKnowledge(catalog, replaceScu({
        ...resourceScu,
        availability_contracts: [{ binding_id: bindingId, requirements: [{
          kind: 'derived', scope: 'global', required_binding_ids: [answerBinding], source_ref: 'fixture',
        }] }],
      }))
      expect(report.findings).toContainEqual(expect.objectContaining({
        code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
        subject: `${resourceScu.scu_id}:${bindingId}`,
        detail: expect.stringContaining('proven only by its snapshot registration'),
      }))
    })

    it('rejects a non-answer capability as a derived leg of an answer composite', () => {
      const resourceBinding = resourceScu.availability_contracts![0]!.binding_id
      const report = inspectCapabilityKnowledge(catalog, replaceScu({
        ...answerScu,
        availability_contracts: [{ binding_id: answerBinding, requirements: [{
          kind: 'derived', scope: 'global', required_binding_ids: [resourceBinding], source_ref: 'fixture',
        }] }],
      }))
      expect(report.findings).toContainEqual(expect.objectContaining({
        code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
        detail: expect.stringContaining('cannot evidence a composite answer'),
      }))
    })

    it('keeps an answer capability dark at runtime if a snapshot proof is smuggled onto it', async () => {
      const overlay = await overlayWithNoEvidence(replaceScu({
        ...answerScu,
        availability_contracts: [{ binding_id: answerBinding, requirements: [{
          kind: 'snapshot_resource', proof: 'registered_in_pinned_snapshot', scope: 'global', source_ref: 'fixture',
        }] }],
      }))
      expect(overlay.availability.find((entry) => entry.scu_id === answerScu.scu_id)).toMatchObject({
        state: 'dark', available_binding_ids: [],
      })
    })
  })
})
