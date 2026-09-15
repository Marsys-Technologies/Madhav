import { describe, expect, it } from 'vitest'
import { getCatalog } from '../catalog'
import { compileCapabilityKnowledge, inspectCapabilityKnowledge } from './compiler'
import { compileChartCapabilityOverlay, assertOverlayCompatibility } from './overlay'
import { inspectSemanticCapability, searchSemanticCapabilities } from './query'
import type { CapabilityKnowledgeSnapshot, SemanticCapabilityUnit } from './types'
import { getDescriptorEditorialReview } from './editorial_review'
import estateCensus from '../../../../generated/capability_estate_census.json'
import type { CapabilityDescriptor } from '../types'
import { buildPlannerCapabilityKnowledgeProjection } from './planner_projection'

describe('planner capability knowledge', () => {
  const catalog = getCatalog()
  const snapshot = compileCapabilityKnowledge(catalog, '2026-09-13T00:00:00.000Z')

  it('compiles a total, deterministic snapshot from the live catalog', () => {
    const second = compileCapabilityKnowledge(catalog, '2026-09-14T00:00:00.000Z')
    expect(snapshot.census.runtime_descriptors).toBe(catalog.length)
    expect(snapshot.census.addressable_descriptors + snapshot.census.excluded_descriptors).toBe(catalog.length)
    expect(snapshot.census.semantic_capabilities).toBe(snapshot.scus.length)
    expect(snapshot.census.executable_bindings).toBe(186)
    expect(snapshot.census.unavailable_bindings).toBe(0)
    expect(snapshot.schema_version).toBe('2.2.0')
    expect(snapshot.compatibility_version).toBe('planner-scu-v2')
    expect(snapshot.content_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(snapshot.semantic_review_fingerprint).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(second.content_hash).toBe(snapshot.content_hash)
    expect(Object.isFrozen(snapshot)).toBe(true)
    const report = inspectCapabilityKnowledge(catalog, snapshot)
    expect(report.passed).toBe(true)
    expect(report.findings.every((finding) => finding.severity === 'warning')).toBe(true)
    expect(report.findings.map((finding) => finding.code)).toContain('BAD_PAGINATION_CONTRACT')
  })

  it('joins every registry binding to the reviewed full-profile route authority', () => {
    const routes = estateCensus.details.descriptor_route_contracts
    expect(routes).toHaveLength(186)
    expect(routes.filter((route) => route.public_route_disposition === 'reviewed_exposed')).toHaveLength(71)
    expect(routes.filter((route) => route.public_route_disposition === 'reviewed_not_exposed')).toHaveLength(115)
    expect(snapshot.census).toMatchObject({
      reviewed_route_descriptors: 186,
      reviewed_public_descriptors: 71,
      reviewed_nonpublic_descriptors: 115,
    })
    const bindings = snapshot.scus.flatMap((scu) => scu.bindings).filter((binding) => binding.kind === 'registry_capability')
    const bindingByUri = new Map(bindings.map((binding) => [binding.capability_uri, binding]))
    expect(bindingByUri.size).toBe(182)
    expect(routes.filter((route) => !bindingByUri.has(route.capability_uri)).map((route) => route.capability_uri).sort())
      .toEqual(snapshot.census.exclusions.map((item) => item.capability_uri).sort())
    for (const route of routes.filter((candidate) => bindingByUri.has(candidate.capability_uri))) {
      const binding = bindingByUri.get(route.capability_uri)
      expect(binding, route.capability_uri).toBeDefined()
      expect(binding?.execution_channels?.includes('mcp_full')).toBe(route.public_route_disposition === 'reviewed_exposed')
      expect(binding?.public_tool_name ?? null).toBe(route.public_tool_names[0] ?? null)
      expect(binding?.route_evidence).toContain(route.public_route_evidence[0])
    }
  })

  it('keeps SCUs distinct from tools with many-to-many executable bindings', () => {
    const finance = snapshot.scus.find((scu) => scu.scu_id === 'scu.finance.prosperity_assessment')
    const yoga = snapshot.scus.find((scu) => scu.scu_id === 'scu.yoga.firing_and_cancellation')
    expect(finance?.bindings).toHaveLength(2)
    expect(yoga?.bindings).toHaveLength(2)
    expect(finance?.bindings.every((binding) => binding.executable)).toBe(true)
    expect(yoga?.bindings.find((binding) => binding.relation === 'primary')?.public_tool_name).toBe('ganita_yoga_firings_get')
    expect(snapshot.census.publicly_named_bindings).toBeGreaterThan(0)
    expect(snapshot.census.reviewed_output_claims).toBe(7)
    expect(snapshot.scus.flatMap((scu) => scu.producer_output_claims ?? [])
      .filter((claim) => claim.disposition === 'reviewed_output')
      .every((claim) => /^[a-f0-9]{64}$/.test(claim.output_digest_spec_sha256 ?? ''))).toBe(true)
  })

  it('replaces every descriptor-derived stub with a source-linked editorial unit', () => {
    const enriched = snapshot as CapabilityKnowledgeSnapshot & {
      scus: readonly (SemanticCapabilityUnit & {
        editorial_method?: string
        editorial_sources?: readonly { source_ref: string; source_fields: readonly string[] }[]
      })[]
    }
    expect(enriched.census.editorial_scus).toBe(182)
    expect(enriched.census.derived_scus).toBe(0)
    expect(enriched.scus.every((scu) => scu.editorial)).toBe(true)
    expect(enriched.scus.every((scu) => ['authored_declaration', 'descriptor_metadata_review'].includes(scu.editorial_method ?? ''))).toBe(true)
    expect(enriched.scus.every((scu) => (scu.editorial_sources?.length ?? 0) > 0)).toBe(true)
    expect(enriched.scus.every((scu) => scu.editorial_sources?.every((source) => source.source_ref.length > 0 && source.source_fields.length > 0))).toBe(true)
    expect(enriched.scus.every((scu) => scu.description.trim().length >= 24)).toBe(true)
  })

  it('binds every SCU concept into one typed source-linked concept universe', () => {
    const enriched = snapshot as CapabilityKnowledgeSnapshot & {
      concept_universe?: readonly { concept_id: string; types: readonly string[]; source_refs: readonly string[] }[]
      scus: readonly (SemanticCapabilityUnit & {
        concept_bindings?: readonly { concept_id: string; concept_type: string; source_ref: string }[]
      })[]
      census: CapabilityKnowledgeSnapshot['census'] & { typed_concepts?: number; unbound_concepts?: number }
    }
    const universe = new Map((enriched.concept_universe ?? []).map((concept) => [concept.concept_id, concept]))
    expect(enriched.census.typed_concepts).toBe(universe.size)
    expect(enriched.census.unbound_concepts).toBe(0)
    for (const scu of enriched.scus) {
      expect(scu.concept_bindings?.map((binding) => binding.concept_id).sort()).toEqual([...scu.concepts].sort())
      expect(scu.concept_bindings?.every((binding) => binding.concept_type.length > 0 && binding.source_ref.length > 0)).toBe(true)
      expect(scu.concepts.every((concept) => universe.has(concept))).toBe(true)
    }
    expect([...universe.values()].every((concept) => concept.types.length > 0 && concept.source_refs.length > 0)).toBe(true)
  })

  it('connects every SCU through the typed graph and detects an isolated unit', () => {
    const enriched = snapshot as CapabilityKnowledgeSnapshot & {
      census: CapabilityKnowledgeSnapshot['census'] & { isolated_scus: number; graph_components: number; dispositioned_isolated_scus: number; unresolved_isolated_scus: number }
    }
    expect(enriched.census.unresolved_isolated_scus).toBe(0)
    expect(enriched.census.isolated_scus).toBe(enriched.census.dispositioned_isolated_scus)
    expect(enriched.census.graph_components).toBeGreaterThan(0)
    for (const scu of snapshot.scus) {
      const incident = snapshot.edges.some((edge) => edge.from_scu_id === scu.scu_id || edge.to_scu_id === scu.scu_id)
      expect(incident || scu.graph_disposition.status === 'isolated_dispositioned').toBe(true)
    }
    const isolated = snapshot.scus.find((scu) => scu.graph_disposition.status === 'connected')!
    const broken = {
      ...snapshot,
      edges: snapshot.edges.filter((edge) => edge.from_scu_id !== isolated.scu_id && edge.to_scu_id !== isolated.scu_id),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, broken).findings).toContainEqual(expect.objectContaining({ code: 'ISOLATED_SCU', severity: 'error', subject: isolated.scu_id }))
  })

  it('requires an explicit disposition for every declared semantic gap', () => {
    const enriched = snapshot as CapabilityKnowledgeSnapshot & {
      scus: readonly (SemanticCapabilityUnit & {
        gap_dispositions?: readonly { gap: string; status: string; rationale: string; source_ref: string }[]
      })[]
      census: CapabilityKnowledgeSnapshot['census'] & { undispositioned_gaps?: number }
    }
    expect(enriched.census.undispositioned_gaps).toBe(0)
    for (const scu of enriched.scus) {
      expect(scu.gap_dispositions?.map((gap) => gap.gap).sort()).toEqual([...scu.known_gaps].sort())
      expect(scu.gap_dispositions?.every((gap) => gap.status.length > 0 && gap.rationale.length > 0 && gap.source_ref.length > 0)).toBe(true)
    }
    const source = enriched.scus.find((scu) => scu.known_gaps.length > 0)!
    const broken = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === source.scu_id ? { ...scu, gap_dispositions: [] } : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, broken).findings).toContainEqual(expect.objectContaining({ code: 'UNDISPOSITIONED_GAP', severity: 'error', subject: source.scu_id }))
  })

  it('rejects an editorial unit whose source link is removed', () => {
    const first = snapshot.scus[0]!
    const broken = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === first.scu_id ? { ...scu, editorial_sources: [] } : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, broken).findings).toContainEqual(expect.objectContaining({ code: 'UNSOURCED_EDITORIAL_SCU', severity: 'error', subject: first.scu_id }))
  })

  it('rotates snapshot provenance when source semantic metadata changes', () => {
    const changedCatalog = catalog.map((cap, index) => index === 0 ? { ...cap, description: `${cap.description} Editorial change.` } : cap)
    const changed = compileCapabilityKnowledge(changedCatalog, '2026-09-13T00:00:00.000Z')
    expect(changed.source_catalog_fingerprint).not.toBe(snapshot.source_catalog_fingerprint)
    expect(changed.content_hash).not.toBe(snapshot.content_hash)
  })

  it.each([
    ['emits_references', (cap: (typeof catalog)[number]) => ({ ...cap, emits_references: !cap.emits_references })],
    ['required_inputs', (cap: (typeof catalog)[number]) => ({ ...cap, required_inputs: [...(cap.required_inputs ?? []), '__provenance_fixture'] })],
    ['mutation', (cap: (typeof catalog)[number]) => ({ ...cap, mutation: !cap.mutation })],
  ] as const)('rotates provenance when %s changes', (_field, mutate) => {
    const changedCatalog: readonly CapabilityDescriptor[] = catalog.map((cap, index) => index === 0 ? mutate(cap) as CapabilityDescriptor : cap)
    const changed = compileCapabilityKnowledge(changedCatalog, '2026-09-13T00:00:00.000Z')
    expect(changed.source_catalog_fingerprint).not.toBe(snapshot.source_catalog_fingerprint)
    expect(changed.content_hash).not.toBe(snapshot.content_hash)
  })

  it('dispositions every unverified pagination warning as a named contract gap', () => {
    const warnings = inspectCapabilityKnowledge(catalog, snapshot).findings.filter((finding) => finding.code === 'BAD_PAGINATION_CONTRACT')
    expect(warnings.length).toBeGreaterThan(0)
    for (const warning of warnings) {
      const scu = snapshot.scus.find((item) => item.bindings.some((binding) => binding.binding_id === warning.subject))
      expect(scu?.gap_dispositions).toContainEqual(expect.objectContaining({ status: 'deferred_contract' }))
      expect(scu?.known_gaps.some((gap) => /pagination|paging|bounded|exhaustion|ordering/i.test(gap))).toBe(true)
    }
  })

  it('materially editorializes descriptor metadata instead of relabeling derived stubs', () => {
    const descriptorByUri = new Map(catalog.map((cap) => [cap.uri, cap]))
    const reviewed = snapshot.scus.filter((scu) => scu.editorial_method === 'descriptor_metadata_review')
    expect(reviewed).toHaveLength(176)
    for (const scu of reviewed) {
      const descriptor = descriptorByUri.get(scu.source_descriptor_uris[0]!)!
      expect(scu.description).not.toBe(descriptor.display?.one_line ?? descriptor.description)
      expect(scu.description).toContain('Evidence use:')
      expect(scu.domains).not.toEqual(['all'])
      expect(scu.concept_bindings.some((binding) => binding.concept_type === 'domain_concept')).toBe(true)
      expect(scu.concepts).not.toContain(descriptor.archetype)
      expect(scu.concepts).not.toContain(descriptor.tool_role)
      for (const projection of descriptor.projection_tags ?? []) expect(scu.concepts).not.toContain(projection)
      expect(scu.intents).not.toContain(descriptor.traversal_level.toLowerCase())
      expect(scu.intents).not.toContain(descriptor.tool_role)
      expect(scu.outputs).not.toEqual(descriptor.output_schema ? ['structured_content'] : ['content'])
    }
  })

  it('pins representative descriptors to semantically reviewed families', () => {
    expect(getDescriptorEditorialReview('get_vichara')?.family_id).toBe('assessment')
    expect(getDescriptorEditorialReview('get_tara_chandra_bala')?.family_id).toBe('strength_timing')
    expect(getDescriptorEditorialReview('query_classical_texts')?.family_id).toBe('classical')
    expect(getDescriptorEditorialReview('query_vastu_directions')?.family_id).toBe('vastu')
    expect(getDescriptorEditorialReview('chart_snapshot')?.family_id).toBe('chart_evidence')
    expect(getDescriptorEditorialReview('get_chart_header')?.family_id).toBe('chart_evidence')
    expect(getDescriptorEditorialReview('chart_facts_query')?.family_id).toBe('chart_evidence')
    expect(getDescriptorEditorialReview('maro_mcp_surface')?.family_id).toBe('system_introspection')
    expect(getDescriptorEditorialReview('channel_mcp_wiring')?.family_id).toBe('system_introspection')
  })

  it('uses full source descriptions and reviewed output semantics for substantive tools', () => {
    const reviewed = snapshot.scus.filter((scu) => scu.editorial_method === 'descriptor_metadata_review')
    const descriptorByUri = new Map(catalog.map((cap) => [cap.uri, cap]))
    for (const scu of reviewed) {
      const sourceDescription = descriptorByUri.get(scu.source_descriptor_uris[0]!)!.description.trim().replace(/[.。]+$/, '')
      expect(scu.description.startsWith(sourceDescription)).toBe(true)
    }
    expect(reviewed.every((scu) => scu.outputs.length > 0 && !scu.outputs.every((output) => ['evidence_payload', 'evidence_references'].includes(output)))).toBe(true)
    expect(snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.chart_snapshot')?.outputs).toContain('chart_state_evidence')
    expect(snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.get_aspects')?.outputs).toContain('relationship_evidence')
    expect(snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.get_dashas')?.outputs).toContain('temporal_sequence_evidence')
  })

  it('preserves synthesizer kind and authored temporal horizons', () => {
    for (const name of ['graha_portrait', 'compose_large_n', 'query_spine_bundle', 'synergy_cross_layer']) {
      expect(snapshot.scus.find((scu) => scu.scu_id === `scu.catalog.${name}`)?.kind).toBe('synthesis_support')
    }
    expect(snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.get_sade_sati')?.horizons).toEqual(expect.arrayContaining(['historical', 'future', 'multi_year']))
    expect(snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.get_tajik')?.horizons).toEqual(expect.arrayContaining(['annual', 'current_year']))
    expect(getDescriptorEditorialReview('get_tajik')?.family_id).toBe('annual')
  })

  it('grounds every graph edge in an authored declaration or drill-child contract', () => {
    const byId = new Map(snapshot.scus.map((scu) => [scu.scu_id, scu]))
    expect(snapshot.edges.length).toBeGreaterThan(0)
    for (const edge of snapshot.edges) {
      const from = byId.get(edge.from_scu_id)!
      const to = byId.get(edge.to_scu_id)!
      expect(from).toBeDefined()
      expect(to).toBeDefined()
      expect(edge.from_scu_id).not.toBe(edge.to_scu_id)
      expect(['authored_declaration', 'drill_child_contract']).toContain(edge.edge_source)
      expect(edge.source_ref).toBe(edge.edge_source === 'authored_declaration'
        ? from.editorial_sources[0]?.source_ref
        : `CapabilityDescriptor:${from.source_descriptor_uris[0]}#drill_children`)
    }
  })

  it('keeps embedded SCU edges normalized for planner expansion', () => {
    const scuIds = new Set(snapshot.scus.map((scu) => scu.scu_id))
    expect(snapshot.scus.flatMap((scu) => scu.edges ?? []).every((edge) => scuIds.has(edge.target_scu_id))).toBe(true)
    expect(snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.judgment_query')?.edges).toContainEqual(expect.objectContaining({
      target_scu_id: 'scu.kala.temporal_activation',
    }))
    const projection = buildPlannerCapabilityKnowledgeProjection(snapshot, 'judgment query', {
      intent: 'assess', domains: ['cross_domain'], width: 'focused', depth: 'deep', horizon: 'current', intervention: false, entitlement: 'native',
    })
    expect(projection.capabilities.map((capability) => capability.id)).toContain('scu.kala.temporal_activation')
  })

  it('accounts for every active producer with one exact source-backed semantic binding', () => {
    const enriched = snapshot as CapabilityKnowledgeSnapshot & {
      producer_semantic_bindings?: readonly {
        asset_id: string
        target_scu_id: string | null
        target_capability_uri: string | null
        relation: string
        rationale: string
        source_refs: readonly string[]
      }[]
      scus: readonly (SemanticCapabilityUnit & {
        producer_semantic_disposition?: {
          status: 'linked' | 'not_applicable'
          asset_ids: readonly string[]
          rationale: string
          source_refs: readonly string[]
        }
      })[]
    }
    const expected = [...estateCensus.details.producer_assets.active_asset_ids].sort()
    const bindings = enriched.producer_semantic_bindings ?? []
    expect(bindings).toHaveLength(expected.length)
    expect([...new Set(bindings.map((binding) => binding.asset_id))].sort()).toEqual(expected)
    expect(bindings.map((binding) => binding.asset_id).sort()).toEqual(expected)
    const scuIds = new Set(enriched.scus.map((scu) => scu.scu_id))
    for (const binding of bindings) {
      expect(Number(binding.target_scu_id !== null) + Number(binding.target_capability_uri !== null)).toBe(1)
      if (binding.target_scu_id !== null) expect(scuIds.has(binding.target_scu_id)).toBe(true)
      if (binding.target_capability_uri !== null) expect(catalog.some((capability) => capability.uri === binding.target_capability_uri)).toBe(true)
      expect(['directly_serves_output', 'consumes_output', 'supports_same_semantic_domain']).toContain(binding.relation)
      expect(binding.rationale.length).toBeGreaterThan(12)
      expect(binding.source_refs).toEqual([
        `platform/src/generated/capability_estate_census.json#details.producer_output_contracts:${binding.asset_id}`,
        `platform/src/lib/retrieval/registry/knowledge/producer_editorial_review.ts#${binding.target_scu_id ?? binding.target_capability_uri}:${binding.asset_id}`,
      ])
    }
    for (const scu of enriched.scus) {
      const disposition = scu.producer_semantic_disposition
      expect(disposition).toBeDefined()
      expect(disposition?.rationale.length).toBeGreaterThan(12)
      if (disposition?.status === 'linked') {
        expect(disposition.asset_ids.length).toBeGreaterThan(0)
        expect(disposition.asset_ids.every((assetId) => bindings.some((binding) => binding.asset_id === assetId && binding.target_scu_id === scu.scu_id))).toBe(true)
      } else {
        expect(disposition?.asset_ids).toEqual([])
      }
    }
    expect(enriched.census.producer_semantic_bindings).toBe(expected.length)
    expect(enriched.census.directly_served_producer_outputs).toBe(expected.length - 1)
    expect(enriched.census.support_only_producer_bindings).toBe(1)
    expect(enriched.census.unbound_active_producers).toBe(0)
    expect(enriched.census.undispositioned_producer_scus).toBe(0)
  })

  it('rejects unknown, duplicate, missing, or mistargeted producer semantic bindings', () => {
    const bindings = snapshot.producer_semantic_bindings
    const first = bindings[0]!
    const malformed = {
      ...snapshot,
      producer_semantic_bindings: [
        ...bindings.slice(1),
        { ...first, asset_id: 'unknown_asset' },
        { ...first, target_scu_id: 'scu.missing' },
      ],
    } as CapabilityKnowledgeSnapshot
    const codes = inspectCapabilityKnowledge(catalog, malformed).findings.map((finding) => finding.code)
    expect(codes).toContain('UNBOUND_ACTIVE_PRODUCER')
    expect(codes).toContain('INVALID_PRODUCER_SEMANTIC_BINDING')

    const otherScu = snapshot.scus.find((scu) => scu.scu_id !== first.target_scu_id)!
    const forgedRetarget = {
      ...snapshot,
      producer_semantic_bindings: bindings.map((binding, index) => index === 0 ? {
        ...binding,
        target_scu_id: otherScu.scu_id,
        target_capability_uri: null,
        rationale: 'A plausible but unauthorised replacement rationale for this producer relationship.',
        source_refs: [
          `platform/src/generated/capability_estate_census.json#details.producer_output_contracts:${binding.asset_id}`,
          `platform/src/lib/retrieval/registry/knowledge/producer_editorial_review.ts#${otherScu.scu_id}:${binding.asset_id}`,
        ],
      } : binding),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, forgedRetarget).findings).toContainEqual(expect.objectContaining({
      code: 'INVALID_PRODUCER_SEMANTIC_BINDING', severity: 'error', subject: first.asset_id,
    }))
  })

  it('rejects fake sources, concept parity drift, and stale edge origins', () => {
    const first = snapshot.scus[0]!
    const concept = first.concept_bindings[0]!
    const fakeSource = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === first.scu_id
        ? { ...scu, editorial_sources: [{ source_ref: 'fake', source_fields: ['fake'] }] }
        : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, fakeSource).findings).toContainEqual(expect.objectContaining({ code: 'UNSOURCED_EDITORIAL_SCU', severity: 'error', subject: first.scu_id }))

    const conceptDrift = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === first.scu_id
        ? { ...scu, concept_bindings: scu.concept_bindings.map((binding) => binding.concept_id === concept.concept_id ? { ...binding, concept_type: 'projection' as const, source_ref: 'fake' } : binding) }
        : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, conceptDrift).findings).toContainEqual(expect.objectContaining({ code: 'CONCEPT_BINDING_MISMATCH', severity: 'error', subject: `${first.scu_id}:${concept.concept_id}` }))

    const staleFrom = {
      ...snapshot,
      edges: [...snapshot.edges, { from_scu_id: 'scu.missing', relation: 'related' as const, to_scu_id: first.scu_id, rationale: 'fixture' }],
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, staleFrom).findings).toContainEqual(expect.objectContaining({ code: 'STALE_EDGE', severity: 'error', subject: 'scu.missing' }))

    const firstUniverseConcept = snapshot.concept_universe[0]!
    const universeDrift = {
      ...snapshot,
      concept_universe: snapshot.concept_universe.map((entry, index) => index === 0
        ? { ...entry, types: [...entry.types, 'projection' as const], source_refs: [...entry.source_refs, 'fake'] }
        : entry),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, universeDrift).findings).toContainEqual(expect.objectContaining({
      code: 'CONCEPT_BINDING_MISMATCH', severity: 'error', subject: firstUniverseConcept.concept_id,
    }))

    const firstEdge = snapshot.edges[0]!
    const edgeDrift = {
      ...snapshot,
      edges: snapshot.edges.map((edge, index) => index === 0 ? { ...edge, edge_source: edge.edge_source === 'authored_declaration' ? 'drill_child_contract' as const : 'authored_declaration' as const, rationale: 'forged rationale' } : edge),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, edgeDrift).findings).toContainEqual(expect.objectContaining({
      code: 'INVALID_SEMANTIC_EDGE', severity: 'error', subject: firstEdge.from_scu_id,
    }))

    const graphDispositionDrift = {
      ...snapshot,
      scus: snapshot.scus.map((scu, index) => index === 0 ? { ...scu, graph_disposition: { ...scu.graph_disposition, source_refs: ['fake'] } } : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, graphDispositionDrift).findings).toContainEqual(expect.objectContaining({
      code: snapshot.scus[0]!.graph_disposition.status === 'connected' ? 'INVALID_GRAPH_DISPOSITION' : 'ISOLATED_SCU', severity: 'error', subject: snapshot.scus[0]!.scu_id,
    }))

    const notApplicable = snapshot.scus.find((scu) => scu.producer_semantic_disposition.status === 'not_applicable')!
    const producerDispositionDrift = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === notApplicable.scu_id
        ? { ...scu, producer_semantic_disposition: { ...scu.producer_semantic_disposition, source_refs: ['fake'] } }
        : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, producerDispositionDrift).findings).toContainEqual(expect.objectContaining({
      code: 'INVALID_PRODUCER_SEMANTIC_DISPOSITION', severity: 'error', subject: notApplicable.scu_id,
    }))

    const extraUniverse = {
      ...snapshot,
      concept_universe: [...snapshot.concept_universe, { concept_id: 'forged_unbound_concept', types: ['domain_concept' as const], source_refs: ['fake'] }],
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, extraUniverse).findings).toContainEqual(expect.objectContaining({
      code: 'UNBOUND_CONCEPT', severity: 'error', subject: 'forged_unbound_concept',
    }))
  })

  it('fails change-sync integrity when catalog or authored-review fingerprints drift', () => {
    const staleCatalog = { ...snapshot, source_catalog_fingerprint: 'sha256:stale' } as CapabilityKnowledgeSnapshot
    const staleReview = { ...snapshot, semantic_review_fingerprint: 'sha256:stale' } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, staleCatalog).findings).toContainEqual(expect.objectContaining({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'source_catalog_fingerprint' }))
    expect(inspectCapabilityKnowledge(catalog, staleReview).findings).toContainEqual(expect.objectContaining({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'semantic_review_fingerprint' }))
  })

  it('fails change-sync integrity when schema, content hash, or census is forged', () => {
    const staleSchema = { ...snapshot, schema_version: '1.0.0' } as unknown as CapabilityKnowledgeSnapshot
    const staleHash = { ...snapshot, content_hash: 'sha256:forged' } as CapabilityKnowledgeSnapshot
    const staleCensus = { ...snapshot, census: { ...snapshot.census, editorial_scus: 0, producer_semantic_bindings: 0 } } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, staleSchema).findings).toContainEqual(expect.objectContaining({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'schema_version' }))
    expect(inspectCapabilityKnowledge(catalog, staleHash).findings).toContainEqual(expect.objectContaining({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'content_hash' }))
    expect(inspectCapabilityKnowledge(catalog, staleCensus).findings).toContainEqual(expect.objectContaining({ code: 'CHANGE_SYNC_DRIFT', severity: 'error', subject: 'census' }))
  })

  it('rotates producer provenance when a referenced W1 contract row changes', () => {
    const changedProducerCensus = {
      ...estateCensus,
      details: {
        ...estateCensus.details,
        producer_output_contracts: estateCensus.details.producer_output_contracts.map((contract, index) => index === 0
          ? { ...contract, disposition: `${contract.disposition}_fixture_change` }
          : contract),
      },
    }
    const changed = compileCapabilityKnowledge(catalog, '2026-09-13T00:00:00.000Z', changedProducerCensus)
    expect(changed.source_catalog_fingerprint).toBe(snapshot.source_catalog_fingerprint)
    expect(changed.producer_contract_fingerprint).not.toBe(snapshot.producer_contract_fingerprint)
    expect(changed.content_hash).not.toBe(snapshot.content_hash)
  })

  it('fails closed when an active W1 producer contract is missing', () => {
    const incompleteProducerCensus = {
      ...estateCensus,
      details: {
        ...estateCensus.details,
        producer_output_contracts: estateCensus.details.producer_output_contracts.slice(1),
      },
    }
    expect(() => compileCapabilityKnowledge(catalog, '2026-09-13T00:00:00.000Z', incompleteProducerCensus)).toThrow('INVALID_PRODUCER_CONTRACT_SOURCE')
  })

  it('normalizes legacy flat and JSON Schema input dialects without losing required fields', () => {
    const transit = snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.query_planet_transit')
    expect(transit?.inputs).toEqual(expect.arrayContaining(['planet', 'start_date', 'end_date']))
    expect(transit?.bindings.find((binding) => binding.relation === 'primary')?.input_contract).toMatchObject({
      planet: 'string:required', start_date: 'string:required', end_date: 'string:required',
    })
    expect(transit?.bindings.find((binding) => binding.binding_id === 'registry:marsys://tool/L0/query_current_transit_snapshot')?.input_contract)
      .toEqual({ as_of_date: 'string:required' })
    expect(transit?.bindings[0]?.input_contract).not.toHaveProperty('properties')
  })

  it('requires both stored and computed provenance for hybrid capabilities', () => {
    const pact = snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.pact_query')
    expect(pact?.provenance_requirements).toEqual([
      'chart_id_when_chart_scoped',
      'build_id',
      'formula_or_writer_version',
      'computed_at',
      'engine_version',
    ])
    expect(pact?.freshness_policy).toContain('stored evidence')
    expect(pact?.freshness_policy).toContain('computed evidence')
  })

  it('provides staged discovery, graph inspection, and bounded depth', () => {
    expect(searchSemanticCapabilities(snapshot, 'finance prosperity mechanisms', 5)[0]?.scu_id).toBe('scu.finance.prosperity_assessment')
    const graph = inspectSemanticCapability(snapshot, 'scu.finance.prosperity_assessment', 2)
    expect(graph.root?.kind).toBe('assessment')
    expect(graph.nodes.map((node) => node.scu_id)).toContain('scu.bodha.mechanism.network')
    expect(graph.edges.every((edge) => snapshot.scus.some((scu) => scu.scu_id === edge.to_scu_id))).toBe(true)
  })

  it('fails CI-style integrity for duplicate SCUs, stale edges, and non-executable bindings', () => {
    const first = snapshot.scus[0] as SemanticCapabilityUnit
    const broken = {
      ...snapshot,
      scus: [
        ...snapshot.scus,
        { ...first, bindings: first.bindings.map((binding) => ({ ...binding, executable: false })) },
      ],
      edges: [...snapshot.edges, { from_scu_id: first.scu_id, relation: 'requires' as const, to_scu_id: 'scu.missing', rationale: 'fixture' }],
    } as CapabilityKnowledgeSnapshot
    const report = inspectCapabilityKnowledge(catalog, broken)
    expect(report.passed).toBe(false)
    expect(new Set(report.findings.map((finding) => finding.code))).toEqual(expect.objectContaining(new Set(['DUPLICATE_SCU', 'STALE_EDGE', 'NON_EXECUTABLE_BINDING'])))
  })

  it('rejects a reviewed producer-output claim without an exact specification hash', () => {
    const source = snapshot.scus.find((scu) => (scu.producer_output_claims?.length ?? 0) > 0)!
    const broken = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === source.scu_id
        ? { ...scu, producer_output_claims: [{ ...scu.producer_output_claims![0]!, disposition: 'reviewed_output' as const, output_digest_spec_sha256: null }] }
        : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, broken).findings).toContainEqual(expect.objectContaining({ code: 'BAD_PRODUCER_OUTPUT_CLAIM', severity: 'error' }))
  })

  it('keeps chart availability separate and rejects a stale compatibility pair', () => {
    const overlay = compileChartCapabilityOverlay({ snapshot, chart_id: 'chart-fixture', build_id: 'build-fixture', evidence: [], generated_at: '2026-09-13T00:00:00.000Z' })
    expect(overlay.availability.every((item) => item.state === 'dark')).toBe(true)
    expect(() => assertOverlayCompatibility(snapshot, overlay)).not.toThrow()
    expect(() => assertOverlayCompatibility(snapshot, overlay, 'other-chart')).toThrow('CAPABILITY_OVERLAY_CHART_MISMATCH')
    expect(() => assertOverlayCompatibility(snapshot, { ...overlay, catalog_content_hash: 'sha256:stale' })).toThrow('CAPABILITY_OVERLAY_INCOMPATIBLE')
  })
})
