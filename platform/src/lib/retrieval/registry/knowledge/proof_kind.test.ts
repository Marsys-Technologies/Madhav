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
import { loadChartCapabilityOverlay, type OverlayQueryRow } from './overlay_loader'
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

  // R3 boundary ("genuine per-mode proof typing"): one capability reporting independently
  // provable modes, exercised against the real get_av_transit_gating SCU (sav_bav_gating
  // statically proven, kakshya_windows honestly dispositioned dark) plus synthetic compiler
  // fixtures for the well-formedness rules a real descriptor can't easily violate on its own.
  describe('per-mode proof typing', () => {
    const avTransitGating = scu('scu.catalog.get_av_transit_gating')
    const savBavBindingId = 'registry:marsys://tool/L1/get_av_transit_gating'
    const kakshyaBindingId = 'registry:marsys://tool/L1/get_av_transit_gating#kakshya_windows'

    it('declares two independent bindings for one descriptor, not two SCUs', () => {
      const matches = snapshot.scus.filter((unit) => unit.scu_id === 'scu.catalog.get_av_transit_gating')
      expect(matches).toHaveLength(1)
      expect(avTransitGating.bindings.map((binding) => binding.binding_id).sort()).toEqual(
        [savBavBindingId, kakshyaBindingId].sort(),
      )
    })

    it("kakshya_windows's own selector and dispositioned-dark status never appear on sav_bav_gating's binding", () => {
      const kakshya = avTransitGating.bindings.find((binding) => binding.binding_id === kakshyaBindingId)!
      const savBav = avTransitGating.bindings.find((binding) => binding.binding_id === savBavBindingId)!
      expect(kakshya.mode_selector).toEqual([{ argument: 'mode', equals: 'kakshya_windows' }])
      expect(kakshya.fixed_args).toEqual({ mode: 'kakshya_windows' })
      expect(savBav.mode_selector ?? []).toEqual([])
      expect(avTransitGating.availability_dispositions).toEqual([expect.objectContaining({
        binding_id: kakshyaBindingId, status: 'deliberately_dark',
      })])
    })

    it('resource_ok/plan proof never becomes answer evidence for either binding', () => {
      // Both are answer-type (kakshya_windows is genuinely chart evidence, just unproven) —
      // proof_kind is untouched at the SCU level, matching "leaves every answer capability
      // untyped" above.
      expect(avTransitGating.proof_kind).toBeUndefined()
    })

    function servedGenerationAnchorRow(): OverlayQueryRow {
      return {
        partition_key: '__whole_asset__', receipt_build_id: 'build-per-mode-fixture', rows_build_id: 'build-per-mode-fixture',
        spec_active: true, receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build',
        asset_id: 'ga_served_generation_anchor', chart_id: CHART_ID, build_id: 'build-per-mode-fixture',
        receipt_version: 'per-mode-probe-fixture', receipt_state: 'proven', output_digest_spec_sha256: 'f'.repeat(64),
        observed_at: '2026-09-27T00:00:00.000Z', freshness_state: 'fresh', unknown_reasons: [], freshness_reasons: [],
      }
    }

    it('resolves sav_bav_gating available and kakshya_windows dark independently — an unavailable optional mode never darkens the proven default', async () => {
      let initialQuery = true
      const overlay = await loadChartCapabilityOverlay(snapshot, CHART_ID, async () => {
        if (initialQuery) { initialQuery = false; return { rows: [servedGenerationAnchorRow()] } }
        return { rows: [] }
      }, new Date('2026-09-27T00:05:00.000Z'))
      const availability = overlay.availability.find((entry) => entry.scu_id === 'scu.catalog.get_av_transit_gating')
      expect(availability).toMatchObject({ state: 'available', available_binding_ids: [savBavBindingId] })
      expect(availability!.available_binding_ids).not.toContain(kakshyaBindingId)
      expect(availability!.gaps.some((gap) => gap.includes('kakshya_windows') && gap.includes('deliberately dark'))).toBe(true)
    })

    it('the planner admits sav_bav_gating (the default mode) and blocks nothing for a missing kakshya_windows mode it never requested', async () => {
      let initialQuery = true
      const overlay = await loadChartCapabilityOverlay(snapshot, CHART_ID, async () => {
        if (initialQuery) { initialQuery = false; return { rows: [servedGenerationAnchorRow()] } }
        return { rows: [] }
      }, new Date('2026-09-27T00:05:00.000Z'))
      const contract = compileInquiryContract({
        snapshot, overlay, chart_id: CHART_ID, question: 'How do current transits gate against this chart\'s ashtakavarga?',
        scope_tuple: { intent: 'domain_assessment', domains: ['career'], width: 'broad', depth: 'standard', horizon: 'natal', intervention: 'none', entitlement: 'native' },
        execution_channel: 'mcp_full', presentation_transport: 'raw_mcp',
        ai_proposal: {
          question_facets: [{ label: 'transit gating', terms: ['get_av_transit_gating', 'sav_bav_gating'], materiality: 'required' }],
          uncommon_adjacencies: [],
          hypotheses: [],
        },
      })
      const item = contract.plan_items.find((candidate) => candidate.scu_id === 'scu.catalog.get_av_transit_gating')
      expect(item).toMatchObject({ state: 'ready', binding_id: savBavBindingId })
    })

    describe('synergy_pipeline: dry_run (plan) vs executed (answer) are genuinely different proof kinds', () => {
      const synergyPipeline = scu('scu.catalog.synergy_pipeline')
      const executedBindingId = 'registry:marsys://tool/synergy/pipeline'
      const dryRunBindingId = 'registry:marsys://tool/synergy/pipeline#dry_run'

      it('declares dry_run as plan and the executed default as answer, on one SCU', () => {
        const dryRun = synergyPipeline.bindings.find((binding) => binding.binding_id === dryRunBindingId)!
        const executed = synergyPipeline.bindings.find((binding) => binding.binding_id === executedBindingId)!
        expect(dryRun.proof_kind).toBe('plan')
        expect(dryRun.mode_selector).toEqual([{ argument: 'dry_run', equals: true }])
        expect(dryRun.fixed_args).toEqual({ dry_run: true })
        expect(executed.proof_kind).toBeUndefined() // inherits 'answer' via bindingProofKind's default
        expect(executed.mode_selector ?? []).toEqual([])
      })

      it('dry_run is proven by snapshot registration alone, never by chart evidence', () => {
        const contract = synergyPipeline.availability_contracts!.find((c) => c.binding_id === dryRunBindingId)!
        expect(contract.requirements).toEqual([expect.objectContaining({
          kind: 'snapshot_resource', proof: 'registered_in_pinned_snapshot', scope: 'global',
        })])
      })

      // Independent review finding: the first version of this contract listed only 6 legs,
      // omitting query_convergence_windows and query_life_arc — runTemporalStep
      // (synergy/orchestrator.ts) dispatches all THREE L3 temporal legs for queryClass
      // 'holistic' (the mode synergy_pipeline's executed binding actually runs), not
      // query_temporal_activation alone. A contract under-declaring real dependencies would
      // certify the executed binding 'available' even while two of its three temporal legs
      // were dark — exactly the availability/reality mismatch a derived contract exists to
      // prevent.
      it("the executed mode's derived contract names all three L3 temporal legs runTemporalStep actually dispatches for queryClass 'holistic', not query_temporal_activation alone", () => {
        const contract = synergyPipeline.availability_contracts!.find((c) => c.binding_id === executedBindingId)!
        const requirement = contract.requirements[0] as { required_binding_ids: readonly string[] }
        expect(requirement.required_binding_ids).toEqual(expect.arrayContaining([
          'registry:marsys://tool/L3/query_temporal_activation',
          'registry:marsys://tool/L3/query_convergence_windows',
          'registry:marsys://tool/L3/query_life_arc',
        ]))
      })

      it('dry_run (plan) reads resource_ok and is NEVER admitted as answer evidence, even with zero chart evidence', async () => {
        const overlay = await overlayWithNoEvidence()
        const availability = overlay.availability.find((entry) => entry.scu_id === synergyPipeline.scu_id)!
        expect(availability.available_binding_ids).not.toContain(dryRunBindingId)
      })

      it('a missing/unavailable executed (mandatory answer) mode still prevents complete composite status, regardless of dry_run', async () => {
        // Zero chart evidence anywhere: the executed mode's six-leg derived contract cannot
        // pass, so the SCU must read dark/incomplete overall — dry_run's own always-passing
        // plan proof must not paper over that.
        const overlay = await overlayWithNoEvidence()
        const availability = overlay.availability.find((entry) => entry.scu_id === synergyPipeline.scu_id)!
        expect(availability.state).not.toBe('available')
        expect(availability.available_binding_ids).not.toContain(executedBindingId)
      })

      it("the planner never admits dry_run's plan proof as answer evidence for the executed obligation", async () => {
        const overlay = await overlayWithNoEvidence()
        const contract = compileInquiryContract({
          snapshot, overlay, chart_id: CHART_ID, question: 'Run the full synergy pipeline for this chart.',
          scope_tuple: { intent: 'domain_assessment', domains: ['career'], width: 'broad', depth: 'standard', horizon: 'natal', intervention: 'none', entitlement: 'native' },
          execution_channel: 'mcp_full', presentation_transport: 'raw_mcp',
          ai_proposal: {
            question_facets: [{ label: 'synergy', terms: ['synergy_pipeline'], materiality: 'required' }],
            uncommon_adjacencies: [],
            hypotheses: [],
          },
        })
        const item = contract.plan_items.find((candidate) => candidate.scu_id === synergyPipeline.scu_id)
        expect(item).toMatchObject({ state: 'blocked' })
        expect(item!.binding_id).not.toBe(dryRunBindingId)
      })
    })

    // R3 boundary requirement: "Portal, managed MCP and raw MCP must expose the same
    // mode-specific truth." All three channels compile through this same
    // compileInquiryContract/loadChartCapabilityOverlay choke point (vidhi/inquiry/compiler.ts)
    // — this proves platform_internal (Portal/managed) and mcp_full (raw MCP) both resolve
    // get_av_transit_gating's DEFAULT mode to the identical binding, with identical semantic
    // obligations, matching the existing managed_bridge.test.ts precedent for non-modal SCUs.
    it('every channel resolves the same default mode binding for a modal SCU', async () => {
      let initialQuery = true
      const overlay = await loadChartCapabilityOverlay(snapshot, CHART_ID, async () => {
        if (initialQuery) { initialQuery = false; return { rows: [servedGenerationAnchorRow()] } }
        return { rows: [] }
      }, new Date('2026-09-27T00:05:00.000Z'))
      const proposalArgs = {
        snapshot, overlay, chart_id: CHART_ID, question: 'How do current transits gate against this chart\'s ashtakavarga?',
        scope_tuple: { intent: 'domain_assessment' as const, domains: ['career'], width: 'broad' as const, depth: 'standard' as const, horizon: 'natal' as const, intervention: 'none' as const, entitlement: 'native' as const },
        ai_proposal: {
          question_facets: [{ label: 'transit gating', terms: ['get_av_transit_gating', 'sav_bav_gating'], materiality: 'required' as const }],
          uncommon_adjacencies: [], hypotheses: [],
        },
      }
      const platform = compileInquiryContract({ ...proposalArgs, execution_channel: 'platform_internal', presentation_transport: 'portal' })
      const raw = compileInquiryContract({ ...proposalArgs, execution_channel: 'mcp_full', presentation_transport: 'raw_mcp' })
      const platformItem = platform.plan_items.find((item) => item.scu_id === 'scu.catalog.get_av_transit_gating')
      const rawItem = raw.plan_items.find((item) => item.scu_id === 'scu.catalog.get_av_transit_gating')
      expect(platformItem?.binding_id).toBe(savBavBindingId)
      expect(rawItem?.binding_id).toBe(savBavBindingId)
      expect(platform.semantic_contract_hash).toBe(raw.semantic_contract_hash)
    })

    describe('compiler well-formedness', () => {
      it('rejects two bindings on the same SCU that both omit mode_selector', () => {
        // kakshya_windows's selector stays intact (proving the SCU IS modal); a synthetic
        // third binding, cloned from it but selector-less, creates the ambiguity: two
        // candidate "defaults" (sav_bav_gating's real primary binding + this fixture) with no
        // selector to distinguish which one selectBindingForMode should fall back to.
        const fixtureBinding = {
          ...avTransitGating.bindings.find((binding) => binding.binding_id === kakshyaBindingId)!,
          binding_id: `${kakshyaBindingId}#fixture-duplicate-default`,
          mode_selector: undefined,
        }
        const report = inspectCapabilityKnowledge(catalog, replaceScu({
          ...avTransitGating,
          bindings: [...avTransitGating.bindings, fixtureBinding],
        }))
        expect(report.findings).toContainEqual(expect.objectContaining({
          code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
          subject: avTransitGating.scu_id,
          detail: expect.stringContaining("at most one may be the SCU's default"),
        }))
      })

      it('rejects an invalid per-binding proof_kind value', () => {
        const report = inspectCapabilityKnowledge(catalog, replaceScu({
          ...avTransitGating,
          bindings: avTransitGating.bindings.map((binding) => binding.binding_id === kakshyaBindingId
            ? { ...binding, proof_kind: 'not_a_real_kind' as never } : binding),
        }))
        expect(report.findings).toContainEqual(expect.objectContaining({
          code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
          subject: kakshyaBindingId,
          detail: expect.stringContaining('binding proof_kind must be'),
        }))
      })

      it('rejects a deliberately-dark disposition on a binding whose effective proof kind is answer, unless it is genuinely non-answer', () => {
        // Sanity check on the inverse of the existing rule: a non-answer BINDING (not SCU) may
        // never be marked deliberately_dark either — snapshot registration is its proof, not a
        // disposition. Give kakshya_windows a plan proof_kind and a snapshot_resource contract
        // AND keep its deliberately_dark disposition — this combination should be rejected.
        const report = inspectCapabilityKnowledge(catalog, replaceScu({
          ...avTransitGating,
          bindings: avTransitGating.bindings.map((binding) => binding.binding_id === kakshyaBindingId
            ? { ...binding, proof_kind: 'plan' } : binding),
          availability_contracts: [
            ...avTransitGating.availability_contracts!,
            { binding_id: kakshyaBindingId, requirements: [{
              kind: 'snapshot_resource', proof: 'registered_in_pinned_snapshot', scope: 'global', source_ref: 'fixture',
            }] },
          ],
        }))
        expect(report.findings).toContainEqual(expect.objectContaining({
          code: 'BAD_BINDING_AVAILABILITY_CONTRACT',
          subject: `${avTransitGating.scu_id}:${kakshyaBindingId}`,
          detail: expect.stringContaining('never deliberately dark'),
        }))
      })
    })
  })
})
